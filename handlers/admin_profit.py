"""Admin profit creation handlers."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states.all_states import AdminProfitState
from keyboards.admin_kb import (
    get_admin_menu_keyboard, get_stage_keyboard, get_confirm_keyboard,
    get_back_to_admin_keyboard, get_service_selection_keyboard
)
from database import (
    get_user_by_username, get_user, get_services, get_service,
    create_profit, get_user_stats, get_user_mentor, update_mentor_stats,
    log_admin_action, log_rank_change, create_notification,
    get_user_referrer, update_referrer_earnings, create_referral_profit,
    create_mentor_profit
)
from config import ADMIN_IDS, LOG_CHANNEL_ID, REFERRAL_PERCENT
from middlewares.admin import admin_only
from utils.ranks import get_rank_info, check_rank_up, get_rank_reward_message

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("admin"))
@admin_only
async def show_admin_menu(message: Message) -> None:
    from utils.design import header
    from utils.messages import answer_with_brand
    
    text = f"{header('АДМИН ПАНЕЛЬ', '⚙️')}\n\n🎯 Что делаем?"
    await answer_with_brand(message, text, reply_markup=get_admin_menu_keyboard())


@router.callback_query(F.data == "admin_menu")
@admin_only
async def callback_admin_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.design import header
    from utils.messages import edit_with_brand
    
    text = f"{header('АДМИН ПАНЕЛЬ', '⚙️')}\n\n🎯 Что делаем?"
    await edit_with_brand(callback, text, reply_markup=get_admin_menu_keyboard())


@router.callback_query(F.data == "create_profit")
@admin_only
async def start_profit_creation(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AdminProfitState.waiting_for_worker_username)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "💰 <b>ПРОФИТ - Шаг 1/7</b>\n\n👤 Username или ID воркера:")


@router.message(AdminProfitState.waiting_for_worker_username)
@admin_only
async def receive_worker(message: Message, state: FSMContext) -> None:
    input_text = message.text.strip().lstrip("@")
    
    user = await get_user(int(input_text)) if input_text.isdigit() else await get_user_by_username(input_text)
    
    if not user:
        await message.answer("❌ Не найден. Попробуйте снова:")
        return
    
    if user["status"] != "active":
        await message.answer(f"❌ Не активен ({user['status']}). Другой:")
        return
    
    await state.update_data(worker_id=user["id"], worker_username=user["username"], worker_name=user["full_name"])
    await state.set_state(AdminProfitState.waiting_for_mammoth_name)
    
    await message.answer(f"✅ {user['full_name']} (@{user['username']})\n\n💰 <b>Шаг 2/7</b>\n\nИмя мамонта:")


@router.message(AdminProfitState.waiting_for_mammoth_name)
@admin_only
async def receive_mammoth(message: Message, state: FSMContext) -> None:
    await state.update_data(mammoth_name=message.text.strip())
    await state.set_state(AdminProfitState.waiting_for_service)
    
    services = await get_services()
    if not services:
        await message.answer("❌ Нет сервисов.")
        await state.clear()
        return
    
    await message.answer("💰 <b>Шаг 3/7</b>\n\nСервис:", reply_markup=get_service_selection_keyboard(services))


@router.callback_query(F.data.startswith("select_service_"), AdminProfitState.waiting_for_service)
@admin_only
async def receive_service(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    service = await get_service(int(callback.data.split("_")[2]))
    if not service:
        await callback.message.edit_text("❌ Не найден")
        await state.clear()
        return
    
    await state.update_data(service_id=service["id"], service_name=service["name"])
    await state.set_state(AdminProfitState.waiting_for_amount)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"✅ {service['name']}\n\n💰 <b>Шаг 4/7</b>\n\nСумма (RUB):")


@router.message(AdminProfitState.waiting_for_amount)
@admin_only
async def receive_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.strip().replace("$", "").replace(",", ""))
        if amount <= 0:
            raise ValueError()
    except:
        await message.answer("❌ Неверная сумма:")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(AdminProfitState.waiting_for_percent)
    await message.answer(f"✅ {amount:.2f} RUB\n\n💰 <b>Шаг 5/7</b>\n\nПроцент воркера (0-100):")


@router.message(AdminProfitState.waiting_for_percent)
@admin_only
async def receive_percent(message: Message, state: FSMContext) -> None:
    try:
        percent = int(message.text.strip().replace("%", ""))
        if not 0 <= percent <= 100:
            raise ValueError()
    except:
        await message.answer("❌ 0-100:")
        return
    
    await state.update_data(percent=percent)
    await state.set_state(AdminProfitState.waiting_for_stage)
    await message.answer(f"✅ {percent}%\n\n💰 <b>Шаг 6/7</b>\n\nЭтап:", reply_markup=get_stage_keyboard())


@router.callback_query(F.data.in_(["stage_deposit", "stage_tax"]), AdminProfitState.waiting_for_stage)
@admin_only
async def receive_stage(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    stage = "Депозит" if callback.data == "stage_deposit" else "Налог"
    await state.update_data(stage=stage)
    await state.set_state(AdminProfitState.waiting_for_confirm)
    
    data = await state.get_data()
    amount, percent = data["amount"], data["percent"]
    base_share = amount * (percent / 100)
    
    worker_stats = await get_user_stats(data["worker_id"])
    rank_info = get_rank_info(worker_stats['total_profit'])
    bonus = base_share * (rank_info['bonus'] / 100)
    profit_with_bonus = base_share + bonus
    
    # Referral cut (from total amount, not worker share)
    referrer = await get_user_referrer(data["worker_id"])
    referral_cut = 0
    referral_text = ""
    
    if referrer:
        referral_cut = amount * (REFERRAL_PERCENT / 100)
        referral_text = f"🔗 Реферер @{referrer.get('username', 'N/A')} ({REFERRAL_PERCENT}%): {referral_cut:.2f} RUB\n"
    
    mentor = await get_user_mentor(data["worker_id"])
    mentor_cut = 0
    mentor_text = ""
    
    if mentor:
        mentor_cut = profit_with_bonus * (mentor['percent'] / 100)
        mentor_text = f"👨‍🏫 @{mentor['username']} ({mentor['percent']}%): {mentor_cut:.2f} RUB\n"
    
    worker_share = profit_with_bonus - mentor_cut - referral_cut
    
    preview = (
        f"💰 <b>ПРЕДПРОСМОТР - Шаг 7/7</b>\n\n"
        f"👤 {data['worker_name']} (@{data['worker_username']})\n"
        f"🏆 {rank_info['emoji']} {rank_info['name']} (+{rank_info['bonus']}%)\n"
        f"{mentor_text}"
        f"{referral_text}"
        f"🎯 {data['mammoth_name']}\n"
        f"🛠 {data['service_name']}\n"
        f"📊 {stage}\n\n"
        f"💸 Всего: {amount:.2f} RUB\n"
        f"📊 {percent}% = {base_share:.2f} RUB\n"
        f"🏆 Бонус: +{bonus:.2f} RUB\n"
        f"💵 Воркеру: {worker_share:.2f} RUB\n\n"
        f"Подтвердить?"
    )
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, preview, reply_markup=get_confirm_keyboard())


@router.callback_query(F.data == "confirm_profit", AdminProfitState.waiting_for_confirm)
@admin_only
async def confirm_profit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Создание...")
    
    data = await state.get_data()
    await state.clear()
    
    amount, percent = data["amount"], data["percent"]
    base_profit = amount * (percent / 100)
    
    worker_stats = await get_user_stats(data["worker_id"])
    rank_info = get_rank_info(worker_stats['total_profit'])
    bonus = base_profit * (rank_info['bonus'] / 100)
    profit_with_bonus = base_profit + bonus
    
    # Referral cut
    referrer = await get_user_referrer(data["worker_id"])
    referral_cut = 0
    
    if referrer:
        referral_cut = amount * (REFERRAL_PERCENT / 100)
        await update_referrer_earnings(referrer['id'], referral_cut)
        # Create referral profit record (will be linked after profit creation)
    
    mentor = await get_user_mentor(data["worker_id"])
    mentor_cut = 0
    net_profit = profit_with_bonus - referral_cut
    
    if mentor:
        mentor_cut = profit_with_bonus * (mentor['percent'] / 100)
        net_profit = profit_with_bonus - mentor_cut - referral_cut
        await update_mentor_stats(mentor['id'], mentor_cut)
    
    old_total = worker_stats['total_profit']
    profit_id = await create_profit(data["worker_id"], amount, net_profit, data["service_name"])
    
    # Create referral profit record with profit_id
    if referrer and referral_cut > 0:
        await create_referral_profit(referrer['id'], data["worker_id"], profit_id, referral_cut)
    
    # Create mentor profit record with profit_id
    if mentor and mentor_cut > 0:
        await create_mentor_profit(mentor['id'], mentor['user_id'], data["worker_id"], profit_id, mentor_cut, mentor['percent'])
    
    # Check rank up
    new_total = old_total + net_profit
    rank_up = check_rank_up(old_total, new_total)
    
    if rank_up:
        old_rank = get_rank_info(old_total)
        await log_rank_change(data["worker_id"], old_rank['name'], rank_up['name'], old_rank['level'], rank_up['level'], new_total)
        await create_notification(data["worker_id"], "rank_up", f"🎉 {rank_up['emoji']} {rank_up['name']}!", get_rank_reward_message(rank_up))
        
        try:
            await callback.bot.send_message(data["worker_id"], get_rank_reward_message(rank_up))
        except:
            pass
    
    await log_admin_action(callback.from_user.id, callback.from_user.username or callback.from_user.full_name, "create_profit", f"#{profit_id}: {amount:.2f} RUB @{data['worker_username']}", data["worker_id"])
    
    # Notify worker
    try:
        from aiogram.types import FSInputFile
        from config import BRAND_IMAGE_PROFITS
        
        bonus_text = f"\n🏆 Бонус: +{bonus:.2f} RUB" if bonus > 0 else ""
        mentor_text = f"\n👨‍🏫 Наставник: -{mentor_cut:.2f} RUB" if mentor_cut > 0 else ""
        
        photo = FSInputFile(BRAND_IMAGE_PROFITS)
        await callback.bot.send_photo(
            data["worker_id"], photo=photo,
            caption=(
                f"💎 <b>НОВЫЙ ПРОФИТ</b>\n\n"
                f"Сервис: {data['service_name']}\n"
                f"Всего: {amount:.2f} RUB\n"
                f"Твоя доля ({percent}%): {net_profit:.2f} RUB{bonus_text}{mentor_text}\n\n"
                f"⏳ На удержании"
            )
        )
    except Exception as e:
        logger.error(f"Notify worker failed: {e}")
    
    # Notify mentor
    if mentor and mentor_cut > 0:
        try:
            from aiogram.types import FSInputFile
            from config import BRAND_IMAGE_PROFITS
            
            photo = FSInputFile(BRAND_IMAGE_PROFITS)
            await callback.bot.send_photo(
                mentor['user_id'], photo=photo,
                caption=(
                    f"💰 <b>ПРОФИТ ОТ УЧЕНИКА</b>\n\n"
                    f"Воркер: @{data['worker_username']}\n"
                    f"Ваша доля: {mentor_cut:.2f} RUB"
                )
            )
        except:
            pass
    
    # Notify referrer
    if referrer and referral_cut > 0:
        try:
            from aiogram.types import FSInputFile
            from config import BRAND_IMAGE_PROFITS
            
            photo = FSInputFile(BRAND_IMAGE_PROFITS)
            await callback.bot.send_photo(
                referrer['id'], photo=photo,
                caption=(
                    f"🔗 <b>РЕФЕРАЛЬНЫЙ ДОХОД</b>\n\n"
                    f"Реферал: @{data['worker_username']}\n"
                    f"Ваша доля ({REFERRAL_PERCENT}%): {referral_cut:.2f} RUB"
                )
            )
        except:
            pass
    
    # Log channel
    try:
        from aiogram.types import FSInputFile
        from config import BRAND_IMAGE_PROFITS
        
        photo = FSInputFile(BRAND_IMAGE_PROFITS)
        await callback.bot.send_photo(
            LOG_CHANNEL_ID, photo=photo,
            caption=(
                f"💎 <b>НОВЫЙ ПРОФИТ</b>\n\n"
                f"Воркер: {data['worker_name']} (@{data['worker_username']})\n"
                f"Сервис: {data['service_name']}\n"
                f"Всего: {amount:.2f} RUB\n"
                f"Доля воркера ({percent}%): {net_profit:.2f} RUB"
            )
        )
    except Exception as e:
        logger.error(f"Log channel failed: {e}")
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"✅ <b>ПРОФИТ #{profit_id} СОЗДАН!</b>", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data == "cancel_profit", AdminProfitState.waiting_for_confirm)
@admin_only
async def cancel_profit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "❌ Отменено", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data == "cancel_profit_creation")
@admin_only
async def cancel_profit_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel profit creation at any stage."""
    await callback.answer()
    await state.clear()
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "❌ Создание профита отменено", reply_markup=get_back_to_admin_keyboard())
