"""Registration flow handlers."""
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from states.all_states import RegistrationState
from keyboards.registration import (
    get_agreement_keyboard,
    get_age_keyboard,
    get_experience_keyboard,
    get_work_hours_keyboard,
    get_motivation_keyboard,
    get_source_keyboard,
    get_admin_decision_keyboard,
    get_join_team_keyboard
)
from database import get_user, create_user, update_user_status
from config import APPLICATIONS_CHANNEL_ID

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user: dict = None) -> None:
    """Handle /start command."""
    user = db_user if db_user is not None else await get_user(message.from_user.id)
    
    if user and user["status"] == "active":
        from handlers.user_menu import show_main_menu
        await show_main_menu(message, db_user=user)
        return
    
    if user and user["status"] == "pending":
        await message.answer(
            "⏳ <b>Ваша анкета на рассмотрении</b>\n\n"
            "⏱ Ждите одобрения администратора."
        )
        return
    
    if user and user["status"] == "banned":
        await message.answer("🚫 <b>Доступ запрещен</b>")
        return
    
    # Check for referral link
    referrer_id = None
    if message.text and message.text.startswith("/start ref"):
        try:
            ref_str = message.text.replace("/start ref", "").strip()
            referrer_id = int(ref_str)
            # Don't allow self-referral
            if referrer_id == message.from_user.id:
                referrer_id = None
        except:
            pass
    
    await start_registration(message, state, referrer_id)


async def start_registration(message: Message, state: FSMContext, referrer_id: int = None) -> None:
    """Start registration process."""
    await state.set_state(RegistrationState.waiting_for_agreement)
    if referrer_id:
        await state.update_data(referrer_id=referrer_id)
    
    from utils.design import header
    from utils.messages import answer_with_brand
    from config import BRAND_IMAGE_WELCOME
    
    text = f"{header('ДОБРО ПОЖАЛОВАТЬ!', '🔷')}\n\n"
    text += "🔷 <b>СОГЛАШЕНИЕ</b>\n"
    text += "  ✅ Соблюдать правила команды\n"
    text += "  ✅ Поддерживать конфиденциальность\n"
    text += "  ✅ Работать профессионально\n"
    text += "  ✅ Уважать участников команды\n\n"
    text += "❓ Вы принимаете условия?"
    
    await answer_with_brand(message, text, reply_markup=get_agreement_keyboard(), image_path=BRAND_IMAGE_WELCOME)


@router.callback_query(F.data == "accept_agreement")
async def accept_agreement(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle agreement acceptance."""
    await callback.answer()
    await state.set_state(RegistrationState.waiting_for_age)
    
    from utils.design import header
    from utils.messages import edit_with_brand
    
    text = f"{header('РЕГИСТРАЦИЯ', '📝')}\n\n"
    text += "🎂 <b>Сколько вам лет?</b>"
    
    await edit_with_brand(callback, text, reply_markup=get_age_keyboard())


@router.callback_query(F.data == "decline_agreement")
async def decline_agreement(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle agreement decline."""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>Регистрация отменена</b>\n\n"
        "💬 Если передумаете, напишите /start"
    )


@router.callback_query(F.data.in_(["age_18_25", "age_26_35", "age_36_plus"]))
async def receive_age(callback: CallbackQuery, state: FSMContext) -> None:
    """Receive age selection."""
    await callback.answer()
    
    age_map = {"age_18_25": "14-18 лет", "age_26_35": "18-21 лет", "age_36_plus": "21+ лет"}
    await state.update_data(age=age_map.get(callback.data, "Не указан"))
    await state.set_state(RegistrationState.waiting_for_exp_confirm)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(
        callback,
        "💼 <b>У вас есть опыт работы в этой сфере?</b>\n\n"
        "🎯 Не переживайте, если вы новичок!",
        reply_markup=get_experience_keyboard()
    )


@router.callback_query(F.data.in_(["exp_yes", "exp_no"]))
async def receive_experience(callback: CallbackQuery, state: FSMContext) -> None:
    """Receive experience confirmation."""
    await callback.answer()
    
    exp = "✅ Есть опыт" if callback.data == "exp_yes" else "❌ Новичок"
    await state.update_data(experience_text=exp)
    await state.set_state(RegistrationState.waiting_for_work_hours)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(
        callback,
        "⏰ <b>Сколько времени готовы уделять работе?</b>",
        reply_markup=get_work_hours_keyboard()
    )


@router.callback_query(F.data.in_(["hours_1_3", "hours_4_6", "hours_7_plus", "hours_full"]))
async def receive_work_hours(callback: CallbackQuery, state: FSMContext) -> None:
    """Receive work hours selection."""
    await callback.answer()
    
    hours_map = {
        "hours_1_3": "⏰ 1-3 часа", "hours_4_6": "⏰ 4-6 часов",
        "hours_7_plus": "⏰ 7+ часов", "hours_full": "⏰ Полный день"
    }
    await state.update_data(work_hours=hours_map.get(callback.data, "Не указано"))
    await state.set_state(RegistrationState.waiting_for_motivation)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "🎯 <b>Что вас мотивирует?</b>", reply_markup=get_motivation_keyboard())


@router.callback_query(F.data.in_(["motivation_money", "motivation_learning", "motivation_career", "motivation_network"]))
async def receive_motivation(callback: CallbackQuery, state: FSMContext) -> None:
    """Receive motivation selection."""
    await callback.answer()
    
    motivation_map = {
        "motivation_money": "💰 Заработок", "motivation_learning": "📚 Опыт",
        "motivation_career": "🚀 Карьера", "motivation_network": "🎯 Знакомства"
    }
    await state.update_data(motivation=motivation_map.get(callback.data, "Не указано"))
    await state.set_state(RegistrationState.waiting_for_source)
    
    from utils.messages import edit_with_brand
    await edit_with_brand(callback, "📢 <b>Откуда вы узнали о нас?</b>", reply_markup=get_source_keyboard())


@router.callback_query(F.data.in_(["source_telegram", "source_friend", "source_internet", "source_ads", "source_other"]))
async def receive_source(callback: CallbackQuery, state: FSMContext) -> None:
    """Receive source and submit application."""
    from utils.messages import edit_with_brand
    
    await edit_with_brand(
        callback,
        "✅ <b>Анкета отправлена!</b>\n\n"
        "⏳ Ждите одобрения администратора."
    )
    await callback.answer()
    
    source_map = {
        "source_telegram": "📱 Telegram", "source_friend": "👥 Друг",
        "source_internet": "🌐 Интернет", "source_ads": "📢 Реклама", "source_other": "🔍 Другое"
    }
    source_text = source_map.get(callback.data, "Не указано")
    
    data = await state.get_data()
    await state.clear()
    
    user_id = callback.from_user.id
    username = callback.from_user.username or "Нет username"
    full_name = callback.from_user.full_name
    
    combined_info = f"{data.get('age')}\n{data.get('experience_text')}\n{data.get('work_hours')}\n{data.get('motivation')}"
    referrer_id = data.get('referrer_id')
    
    await create_user(user_id, username, full_name, combined_info, source_text, referrer_id)
    
    # Send to admin channel
    channel_text = (
        f"📋 <b>НОВАЯ АНКЕТА</b>\n\n"
        f"👤 ID: <code>{user_id}</code>\n"
        f"👤 @{username}\n"
        f"👤 {full_name}\n\n"
        f"🎂 {data.get('age')}\n"
        f"💼 {data.get('experience_text')}\n"
        f"⏰ {data.get('work_hours')}\n"
        f"🎯 {data.get('motivation')}\n"
        f"📢 {source_text}"
    )
    
    try:
        sent_message = await callback.bot.send_message(
            APPLICATIONS_CHANNEL_ID, channel_text,
            reply_markup=get_admin_decision_keyboard(user_id)
        )
        logger.info(f"Application sent to channel {APPLICATIONS_CHANNEL_ID}, message_id: {sent_message.message_id}")
    except Exception as e:
        logger.error(f"Failed to send application to channel {APPLICATIONS_CHANNEL_ID}: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        # Try to notify user about the issue
        try:
            await callback.bot.send_message(
                user_id,
                "⚠️ Анкета сохранена, но возникла проблема с отправкой в канал. Администратор уведомлен."
            )
        except:
            pass


@router.callback_query(F.data.startswith("approve_"))
async def approve_application(callback: CallbackQuery) -> None:
    """Admin approves application."""
    user_id = int(callback.data.split("_")[1])
    await update_user_status(user_id, "active")
    
    try:
        await callback.bot.send_message(
            user_id,
            "🎉 <b>ВЫ ПРИНЯТЫ В КОМАНДУ!</b>\n\n"
            "✅ Ваша анкета одобрена.\n"
            "👇 Нажмите кнопку чтобы начать:",
            reply_markup=get_join_team_keyboard()
        )
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")
    
    await callback.message.edit_text(
        f"{callback.message.text}\n\n✅ <b>ОДОБРЕНО</b>\n👤 {callback.from_user.full_name}"
    )
    await callback.answer("✅ Одобрено")


@router.callback_query(F.data.startswith("decline_"))
async def decline_application(callback: CallbackQuery) -> None:
    """Admin declines application."""
    user_id = int(callback.data.split("_")[1])
    await update_user_status(user_id, "banned")
    
    try:
        await callback.bot.send_message(user_id, "❌ <b>Анкета отклонена</b>")
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")
    
    await callback.message.edit_text(
        f"{callback.message.text}\n\n❌ <b>ОТКЛОНЕНО</b>\n👤 {callback.from_user.full_name}"
    )
    await callback.answer("❌ Отклонено")


@router.callback_query(F.data == "join_team")
async def join_team(callback: CallbackQuery) -> None:
    """User clicks Join Team - show main menu."""
    await callback.answer()
    from handlers.user_menu import show_main_menu
    await show_main_menu(callback)
