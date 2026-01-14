"""Admin profit creation handlers."""
import logging
import asyncio
import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest

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
from config import ADMIN_IDS, PROFITS_CHANNEL_ID, REFERRAL_PERCENT, BRAND_IMAGE_LOGO, BRAND_IMAGE_PROFIT
from middlewares.admin import admin_only
from utils.ranks import get_rank_info, check_rank_up, get_rank_reward_message

logger = logging.getLogger(__name__)
router = Router()

# Cache for profit image file_id
_profit_image_cache: str = None


async def send_profit_to_channel(
    bot: Bot,
    profit_id: int,
    worker_name: str,
    worker_username: str,
    worker_tag: str,
    service_name: str,
    amount: float,
    net_profit: float,
    percent: int
) -> bool:
    """Send profit notification to channel with text-top layout."""
    global _profit_image_cache
    
    # Элегантный стиль сообщения (Белая тема) с встроенной картинкой
    # Используем тег вместо username
    caption = (
        f"▫️<b>ПРОФИТ</b> от {worker_tag}\n"
        f"  ╭• 🛠 <b>Сервис:</b> {service_name}\n"
        f"  ╰• 🏳️ <b>Страна:</b> Россия🇷🇺\n"
        f"<blockquote>"
        f"➘ � <b>>Сумма:</b> {amount:,.2f} ₽\n"
        f"➘ 💸 <b>Доля воркера ({percent}%):</b> {net_profit:,.2f} ₽"
        f"</blockquote>\n"
        f"<i>▫️ Отличная работа! Продолжаем так же</i>"
        f"<a href='https://ebon-pi.vercel.app/d51435ba-5023-442d-8152-bca2cddda485.png'>&#8288;</a>"
    )
    
    for attempt in range(3):
        try:
            # Отправляем как текстовое сообщение с встроенной картинкой
            await bot.send_message(
                chat_id=PROFITS_CHANNEL_ID,
                text=caption,
                parse_mode="HTML",
                disable_web_page_preview=False  # Включаем предпросмотр для отображения картинки
            )
            logger.info(f"Profit #{profit_id} sent to channel with image URL in text")
            return True
            
        except TelegramRetryAfter as e:
            logger.warning(f"Rate limited, waiting {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            continue
            
        except TelegramBadRequest as e:
            if "chat not found" in str(e).lower():
                logger.error(f"Channel {PROFITS_CHANNEL_ID} not found! Check bot is admin in channel.")
            elif "not enough rights" in str(e).lower():
                logger.error(f"Bot has no rights to post in channel {PROFITS_CHANNEL_ID}")
            else:
                logger.error(f"Telegram error: {e}")
            return False
            
        except Exception as e:
            logger.error(f"Send to channel failed (attempt {attempt + 1}): {e}")
            if attempt < 2:
                await asyncio.sleep(1)
                continue
            return False
    
    return False


@router.message(Command("admin"))
@admin_only
async def show_admin_menu(message: Message) -> None:
    from utils.design import header
    from utils.messages import answer_with_brand
    
    text = f"{header('АДМИН ПАНЕЛЬ', '⚙️')}\n\n╭• 🎯 <b>Выберите действие:</b>"
    await answer_with_brand(message, text, reply_markup=get_admin_menu_keyboard())


@router.callback_query(F.data == "admin_menu")
@admin_only
async def callback_admin_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    from utils.design import header
    from utils.messages import edit_with_brand
    
    text = f"{header('АДМИН ПАНЕЛЬ', '⚙️')}\n\n╭• 🎯 <b>Выберите действие:</b>"
    await edit_with_brand(callback, text, reply_markup=get_admin_menu_keyboard())


@router.callback_query(F.data == "create_profit")
@admin_only
async def start_profit_creation(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AdminProfitState.waiting_for_worker_username)
    
    from utils.messages import edit_with_brand
    msg = (
        f"╭• 💸 <b>СОЗДАНИЕ ВЫПЛАТЫ (1/7)</b>\n"
        f"┖• 👤 Введите Username или ID воркера:"
    )
    await edit_with_brand(callback, msg)


@router.message(AdminProfitState.waiting_for_worker_username)
@admin_only
async def receive_worker(message: Message, state: FSMContext) -> None:
    input_text = message.text.strip().lstrip("@")
    
    user = await get_user(int(input_text)) if input_text.isdigit() else await get_user_by_username(input_text)
    
    if not user:
        await message.answer("╭• ❌ <b>Не найден!</b>\n┖• Попробуйте снова:")
        return
    
    if user["status"] != "active":
        await message.answer(f"╭• ❌ <b>Статус: {user['status']}</b>\n┖• Введите другого:")
        return
    
    # Сохраняем тег пользователя
    user_tag = user.get('user_tag', '#irl_???')
    await state.update_data(
        worker_id=user["id"], 
        worker_username=user["username"], 
        worker_name=user["full_name"],
        worker_tag=user_tag
    )
    await state.set_state(AdminProfitState.waiting_for_mammoth_name)
    
    msg = (
        f"╭• ✅ <b>Воркер:</b> {user['full_name']} (@{user['username']}) {user_tag}\n"
        f"┠\n"
        f"┠• 💸 <b>СОЗДАНИЕ ВЫПЛАТЫ (2/7)</b>\n"
        f"┖• 🦣 Введите имя мамонта:"
    )
    await message.answer(msg)


@router.message(AdminProfitState.waiting_for_mammoth_name)
@admin_only
async def receive_mammoth(message: Message, state: FSMContext) -> None:
    await state.update_data(mammoth_name=message.text.strip())
    await state.set_state(AdminProfitState.waiting_for_service)
    
    services = await get_services()
    if not services:
        await message.answer("❌ Нет доступных сервисов.")
        await state.clear()
        return
    
    msg = (
        f"╭• 💸 <b>СОЗДАНИЕ ВЫПЛАТЫ (3/7)</b>\n"
        f"┖• 🛠 Выберите сервис из списка:"
    )
    await message.answer(msg, reply_markup=get_service_selection_keyboard(services))


@router.callback_query(F.data.startswith("select_service_"), AdminProfitState.waiting_for_service)
@admin_only
async def receive_service(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    service = await get_service(int(callback.data.split("_")[2]))
    if not service:
        await callback.message.edit_text("❌ Сервис не найден")
        await state.clear()
        return
    
    await state.update_data(service_id=service["id"], service_name=service["name"])
    await state.set_state(AdminProfitState.waiting_for_amount)
    
    from utils.messages import edit_with_brand
    msg = (
        f"╭• ✅ <b>Сервис:</b> {service['name']}\n"
        f"┠\n"
        f"┠• 💸 <b>СОЗДАНИЕ ВЫПЛАТЫ (4/7)</b>\n"
        f"┖• 💰 Введите сумму (RUB):"
    )
    await edit_with_brand(callback, msg)


@router.message(AdminProfitState.waiting_for_amount)
@admin_only
async def receive_amount(message: Message, state: FSMContext) -> None:
    try:
        amount = float(message.text.strip().replace("$", "").replace(",", ""))
        if amount <= 0:
            raise ValueError()
    except:
        await message.answer("╭• ❌ <b>Ошибка!</b>\n┖• Введите корректное число:")
        return
    
    await state.update_data(amount=amount)
    await state.set_state(AdminProfitState.waiting_for_percent)
    
    msg = (
        f"╭• ✅ <b>Сумма:</b> {amount:,.2f} RUB\n"
        f"┠\n"
        f"┠• 💸 <b>СОЗДАНИЕ ВЫПЛАТЫ (5/7)</b>\n"
        f"┖• 📊 Введите процент воркера (0-100):"
    )
    await message.answer(msg)


@router.message(AdminProfitState.waiting_for_percent)
@admin_only
async def receive_percent(message: Message, state: FSMContext) -> None:
    try:
        percent = int(message.text.strip().replace("%", ""))
        if not 0 <= percent <= 100:
            raise ValueError()
    except:
        await message.answer("╭• ❌ <b>Ошибка!</b>\n┖• Введите целое число 0-100:")
        return
    
    await state.update_data(percent=percent)
    await state.set_state(AdminProfitState.waiting_for_stage)
    
    msg = (
        f"╭• ✅ <b>Процент:</b> {percent}%\n"
        f"┠\n"
        f"┠• 💸 <b>СОЗДАНИЕ ВЫПЛАТЫ (6/7)</b>\n"
        f"┖• 🎭 Выберите этап:"
    )
    await message.answer(msg, reply_markup=get_stage_keyboard())


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
    
    # Referral cut
    referrer = await get_user_referrer(data["worker_id"])
    referral_text = ""
    
    if referrer:
        referral_cut = amount * (REFERRAL_PERCENT / 100)
        referral_text = f"┠• 🔗 <b>Реферер:</b> @{referrer.get('username', 'N/A')} ({referral_cut:.2f} ₽)\n"
    
    mentor = await get_user_mentor(data["worker_id"])
    mentor_cut = 0
    mentor_text = ""
    
    # Проверяем, что наставник работает по тому же сервису, что и профит
    if mentor and mentor['service_name'].lower() == data["service_name"].lower():
        mentor_cut = profit_with_bonus * (mentor['percent'] / 100)
        mentor_text = f"┠• 👨‍🏫 <b>Наставник:</b> @{mentor['username']} ({mentor_cut:.2f} ₽)\n"
    
    worker_share = profit_with_bonus - mentor_cut
    
    # Эстетичный предпросмотр
    preview = (
        f"╭• 🦢 <b>ПРЕДПРОСМОТР (7/7)</b>\n"
        f"┠• 👤 <b>Воркер:</b> {data['worker_name']}\n"
        f"┠• 🏆 <b>Ранг:</b> {rank_info['emoji']} {rank_info['name']} (+{rank_info['bonus']}%)\n"
        f"┠• 🦣 <b>Мамонт:</b> {data['mammoth_name']}\n"
        f"┠• 🛠 <b>Сервис:</b> {data['service_name']} ({stage})\n"
        f"<blockquote>"
        f"┠• 💳 <b>Сумма:</b> {amount:,.2f} ₽\n"
        f"┠• 📊 <b>База ({percent}%):</b> {base_share:,.2f} ₽\n"
        f"┠• 🎁 <b>Бонус:</b> +{bonus:,.2f} ₽\n"
        f"{mentor_text}"
        f"{referral_text}"
        f"┖• 💸 <b>ИТОГ ВОРКЕРУ:</b> {worker_share:,.2f} ₽"
        f"</blockquote>\n\n"
        f"<i>▫️ Отправляем в канал?</i>"
    )
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, preview, reply_markup=get_confirm_keyboard())


@router.callback_query(F.data == "confirm_profit", AdminProfitState.waiting_for_confirm)
@admin_only
async def confirm_profit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("⏳ Создаем выплату...")
    
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
    
    mentor = await get_user_mentor(data["worker_id"])
    mentor_cut = 0
    net_profit = profit_with_bonus # Referral cut usually doesn't reduce worker profit in most teams, but if it does, adjust here. Assuming standard model where referral is extra or from admin cut.
    # Note: In previous code `net_profit = profit_with_bonus - referral_cut`. Keeping logical consistency with standard logic:
    
    # Проверяем, что наставник работает по тому же сервису, что и профит
    if mentor and mentor['service_name'].lower() == data["service_name"].lower():
        mentor_cut = profit_with_bonus * (mentor['percent'] / 100)
        net_profit = profit_with_bonus - mentor_cut
        await update_mentor_stats(mentor['id'], mentor_cut)
    
    old_total = worker_stats['total_profit']
    profit_id = await create_profit(data["worker_id"], amount, net_profit, data["service_name"])
    
    if referrer and referral_cut > 0:
        await create_referral_profit(referrer['id'], data["worker_id"], profit_id, referral_cut)
    
    if mentor and mentor_cut > 0 and mentor['service_name'].lower() == data["service_name"].lower():
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
        bonus_text = f"\n┠• 🎁 Бонус: +{bonus:.2f} ₽" if bonus > 0 else ""
        mentor_text = f"\n┠• 👨‍🏫 Наставник: -{mentor_cut:.2f} ₽" if mentor_cut > 0 else ""
        
        caption = (
            f"╭• 💎 <b>НОВЫЙ ПРОФИТ!</b>\n"
            f"┠• 🛠 Сервис: {data['service_name']}\n"
            f"<blockquote>"
            f"┠• 💳 Сумма: {amount:,.2f} ₽\n"
            f"┠• 💸 Твоя доля: {net_profit:,.2f} ₽"
            f"{bonus_text}{mentor_text}"
            f"</blockquote>\n"
            f"┖• ⏳ <i>Средства на удержании</i>"
        )
        
        await callback.bot.send_message(
            data["worker_id"], caption, parse_mode="HTML"
        )
        logger.info(f"Worker {data['worker_id']} notified about profit #{profit_id}")
    except Exception as e:
        logger.error(f"Notify worker failed: {e}")
    
    # Notify mentor
    if mentor and mentor_cut > 0:
        try:
            mentor_msg = (
                 f"╭• 🦢 <b>ПРОФИТ ОТ УЧЕНИКА</b>\n"
                 f"┠• 👤 Воркер: {data.get('worker_tag', '#irl_???')}\n"
                 f"┖• 💸 Ваша доля: <b>{mentor_cut:.2f} RUB</b>"
            )
            
            await callback.bot.send_message(
                mentor['user_id'], mentor_msg, parse_mode="HTML"
            )
        except:
            pass
    
    # Notify referrer
    if referrer and referral_cut > 0:
        try:
            ref_msg = (
                f"╭• 🔗 <b>РЕФЕРАЛЬНЫЙ ДОХОД</b>\n"
                f"┠• 👤 Реферал: {data.get('worker_tag', '#irl_???')}\n"
                f"┖• 💸 Ваша доля: <b>{referral_cut:.2f} RUB</b>"
            )
            
            await callback.bot.send_message(
                referrer['id'], ref_msg, parse_mode="HTML"
            )
        except:
            pass
    
    # Send to profits channel
    await send_profit_to_channel(
        callback.bot,
        profit_id=profit_id,
        worker_name=data['worker_name'],
        worker_username=data['worker_username'],
        worker_tag=data.get('worker_tag', '#irl_???'),
        service_name=data['service_name'],
        amount=amount,
        net_profit=net_profit,
        percent=percent
    )
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, f"╭• ✅ <b>ПРОФИТ #{profit_id} СОЗДАН!</b>\n┖• Отправлен в канал и ЛС.", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data == "cancel_profit", AdminProfitState.waiting_for_confirm)
@admin_only
async def cancel_profit(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "╭• ❌ <b>Отменено</b>\n┖• Действие сброшено.", reply_markup=get_back_to_admin_keyboard())


@router.callback_query(F.data == "cancel_profit_creation")
@admin_only
async def cancel_profit_creation(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel profit creation at any stage."""
    await callback.answer()
    await state.clear()
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "╭• ❌ <b>Создание отменено</b>\n┖• Возврат в меню.", reply_markup=get_back_to_admin_keyboard())