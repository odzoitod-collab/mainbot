"""Optimized user main menu and navigation handlers."""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from contextlib import suppress

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.fsm.context import FSMContext

from keyboards.user_kb import (
    get_main_menu_keyboard, get_profile_keyboard, get_profit_history_keyboard,
    get_services_keyboard, get_service_detail_keyboard, get_resources_keyboard,
    get_back_to_menu_keyboard, get_mentor_services_keyboard, get_mentor_selection_keyboard,
    get_mentor_detail_keyboard, get_direct_payments_keyboard, get_referral_keyboard,
    get_main_static_keyboard, get_communities_keyboard, get_community_detail_keyboard,
    get_community_create_keyboard
)
from database import (
    get_user, get_user_stats, get_user_profits, get_services, get_service,
    get_resources, get_user_mentor, get_mentor,
    get_mentor_services, get_mentors_by_service,
    assign_mentor, remove_mentor, update_user_activity, get_direct_payment_settings,
    get_referral_stats, get_user_position, get_profile_data,
    get_communities_for_user, get_community, create_community_request,
    join_community, leave_community, is_community_member, is_user_mentor,
    get_mentor_channel_info
)
from utils.messages import answer_with_brand, edit_with_brand
from utils.design import header, profit_card
from config import ADMIN_IDS, BRAND_IMAGE_LOGO, BRAND_IMAGE_MAIN_MENU, BRAND_IMAGE_PROFILE, BRAND_IMAGE_SERVICES, BRAND_IMAGE_MENTORS, BRAND_IMAGE_REFERRALS, BRAND_IMAGE_PROFITS, BRAND_IMAGE_PAYMENTS, BRAND_IMAGE_COMMUNITY, WEBSITE_URL
from states.all_states import CommunityCreateState

logger = logging.getLogger(__name__)
router = Router()


def _format_date(date_str: str) -> str:
    """Format date for display (optimized)."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now.date() - dt.date()
        time_str = dt.strftime("%H:%M")
        
        if diff.days == 0:
            return f"Сегодня {time_str}"
        elif diff.days == 1:
            return f"Вчера {time_str}"
        return dt.strftime("%d.%m %H:%M")
    except:
        return date_str[:16] if len(date_str) > 16 else date_str


def _build_profile_text(user: dict, stats: dict, position: dict, mentor: Optional[dict]) -> str:
    """Build profile text."""
    mentor_name = "Отсутствует"
    if mentor:
        # Для наставника показываем тег, если есть
        mentor_name = mentor.get('user_tag', f"@{mentor['username']}" if mentor.get('username') else mentor.get('full_name', 'Наставник'))
    
    # Показываем тег пользователя
    user_tag = user.get('user_tag', '#irl_???')
    username = f"@{user['username']}" if user.get('username') else "—"
    
    return (
        f"🏷 <b>Ваш тег:</b> {user_tag}\n\n"
        f"👤 <b>Информация о профиле:</b>\n"
        f"┣ ID: <code>{user['id']}</code>\n"
        f"┣ Никнейм: {username}\n"
        f"┗ Наставник: {mentor_name}\n\n"
        f"💳 <b>Информация о профитах:</b>\n"
        f"┣ За Все Время: {stats.get('total_profit', 0):.2f} RUB\n"
        f"┣ За День: {stats.get('day_profit', 0):.2f} RUB\n"
        f"┣ За Неделю: {stats.get('week_profit', 0):.2f} RUB\n"
        f"┣ За Месяц: {stats.get('month_profit', 0):.2f} RUB\n"
        f"┣ Рекорд: {stats.get('max_profit', 0):.2f} RUB\n"
        f"┗ Место в топе: {position['overall_rank']} из {position['total_users']}"
    )


def _build_profit_history(profits: list, page: int, per_page: int = 5) -> tuple[str, int]:
    """Build profit history text."""
    if not profits:
        return header("История профитов", "💰") + "\n\n<i>Пока нет профитов.</i>", 1
    
    total_pages = max(1, -(-len(profits) // per_page))  # Ceiling division
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    page_profits = profits[start:start + per_page]
    page_total = sum(p["net_profit"] for p in page_profits)
    
    lines = [
        header("История профитов", "💰"),
        f"<i>Стр. {page + 1}/{total_pages} • Всего: {len(profits)}</i>",
        f"<i>На странице: {page_total:.2f} RUB</i>"
    ]
    
    for p in page_profits:
        lines.append(profit_card(
            p["service_name"], p["amount"], p["net_profit"],
            _format_date(p["created_at"]), p["status"]
        ))
    
    return "\n".join(lines), total_pages


async def show_main_menu(event: TelegramObject, db_user: dict = None) -> None:
    """Show main menu (optimized)."""
    if isinstance(event, CallbackQuery):
        user = event.from_user
    elif isinstance(event, Message):
        user = event.from_user
    else:
        return
    
    if db_user is None:
        db_user = await get_user(user.id)
    
    if not db_user:
        msg = "❌ Не найден. /start"
        if isinstance(event, CallbackQuery):
            await event.answer(msg, show_alert=True)
        else:
            await event.answer(msg)
        return
    
    # Fire and forget - don't block
    asyncio.create_task(update_user_activity(user.id))
    
    is_admin = user.id in ADMIN_IDS
    is_mentor = await is_user_mentor(user.id)
    
    # Простой текст главного меню
    text = header('Главное меню', '💠')
    
    inline_kb = get_main_menu_keyboard(0, is_admin, is_mentor)
    
    if isinstance(event, CallbackQuery):
        await edit_with_brand(event, text, reply_markup=inline_kb, image_path=BRAND_IMAGE_MAIN_MENU)
    else:
        # For messages, set static keyboard separately
        static_kb = get_main_static_keyboard()
        await answer_with_brand(event, text, reply_markup=inline_kb, image_path=BRAND_IMAGE_MAIN_MENU, static_keyboard=static_kb)


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await show_main_menu(callback)


@router.message(F.text == "🏠 Главное меню")
async def text_main_menu(message: Message) -> None:
    """Handle static keyboard main menu button - works like /start."""
    # Get user from database
    user = await get_user(message.from_user.id)
    
    if user and user["status"] == "active":
        # Set static keyboard and show main menu
        static_kb = get_main_static_keyboard()
        is_mentor = await is_user_mentor(message.from_user.id)
        await answer_with_brand(
            message, 
            header('Главное меню', '💠'), 
            reply_markup=get_main_menu_keyboard(0, message.from_user.id in ADMIN_IDS, is_mentor), 
            image_path=BRAND_IMAGE_MAIN_MENU,
            static_keyboard=static_kb
        )
        # Update user activity
        asyncio.create_task(update_user_activity(message.from_user.id))
    elif user and user["status"] == "pending":
        await message.answer(
            "⏳ <b>Ваша анкета на рассмотрении</b>\n\n"
            "⏱ Ждите одобрения администратора."
        )
    elif user and user["status"] == "banned":
        await message.answer("🚫 <b>Доступ запрещен</b>")
    else:
        # User not found - suggest registration
        await message.answer(
            "❌ <b>Пользователь не найден</b>\n\n"
            "Для начала работы нажмите /start"
        )


@router.message(F.text == "👤 Профиль")
async def text_profile(message: Message) -> None:
    """Handle static keyboard profile button."""
    # Parallel data loading
    data = await get_profile_data(message.from_user.id)
    
    if not data["user"]:
        await message.answer("❌ Ошибка")
        return
    
    text = _build_profile_text(data["user"], data["stats"], data["position"], data["mentor"])
    static_kb = get_main_static_keyboard()
    await answer_with_brand(message, text, reply_markup=get_profile_keyboard(), image_path=BRAND_IMAGE_PROFILE, static_keyboard=static_kb)


@router.message(F.text == "🛠 Сервисы")
async def text_services(message: Message) -> None:
    """Handle static keyboard services button."""
    services = await get_services()
    
    text = (
        f"{header('Сервисы', '🛠')}\n\n"
        f"🎯 <b>Рабочие инструменты для заработка</b>\n\n"
        f"Выбери нужный сервис из списка ниже.\n"
        f"Каждый сервис содержит мануалы и боты для работы."
    )
    
    if not services:
        text += "\n\n<i>Пока нет доступных сервисов.</i>"
    
    static_kb = get_main_static_keyboard()
    await answer_with_brand(message, text, reply_markup=get_services_keyboard(services), image_path=BRAND_IMAGE_SERVICES, static_keyboard=static_kb)


@router.message(F.text == "/menu")
async def cmd_menu(message: Message) -> None:
    """Handle /menu command and set static keyboard."""
    await show_main_menu(message)


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery) -> None:
    await callback.answer()
    
    # Parallel data loading
    data = await get_profile_data(callback.from_user.id)
    
    if not data["user"]:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    text = _build_profile_text(data["user"], data["stats"], data["position"], data["mentor"])
    await edit_with_brand(callback, text, reply_markup=get_profile_keyboard(), image_path=BRAND_IMAGE_PROFILE)


@router.callback_query(F.data == "referral_link")
async def show_referral_link(callback: CallbackQuery) -> None:
    from config import BOT_USERNAME, REFERRAL_PERCENT
    await callback.answer()
    
    ref_stats = await get_referral_stats(callback.from_user.id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref{callback.from_user.id}"
    
    text = (
        f"{header('Реферальная программа', '🔗')}\n\n"
        f"💰 Получай <b>{REFERRAL_PERCENT}%</b> от профитов приглашенных!\n\n"
        f"📊 <b>Твоя статистика:</b>\n"
        f"👥 Рефералов: {ref_stats['count']}\n"
        f"💵 Заработано: {ref_stats['earnings']:.2f} RUB\n\n"
        f"🔗 <b>Твоя ссылка:</b>\n<code>{ref_link}</code>"
    )
    
    await edit_with_brand(callback, text, reply_markup=get_referral_keyboard(ref_link, WEBSITE_URL), image_path=BRAND_IMAGE_REFERRALS)


@router.callback_query(F.data == "profit_history")
async def show_profit_history(callback: CallbackQuery) -> None:
    await callback.answer()
    
    profits = await get_user_profits(callback.from_user.id)
    text, total_pages = _build_profit_history(profits, 0)
    await edit_with_brand(callback, text, reply_markup=get_profit_history_keyboard(0, total_pages), image_path=BRAND_IMAGE_PROFITS)


@router.callback_query(F.data.startswith("profit_page_"))
async def paginate_profits(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        page = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        page = 0
    
    profits = await get_user_profits(callback.from_user.id)
    text, total_pages = _build_profit_history(profits, page)
    await edit_with_brand(callback, text, reply_markup=get_profit_history_keyboard(page, total_pages), image_path=BRAND_IMAGE_PROFITS)


@router.callback_query(F.data == "services")
async def show_services(callback: CallbackQuery) -> None:
    await callback.answer()
    
    services = await get_services()
    
    text = (
        f"{header('Сервисы', '🛠')}\n\n"
        f"🎯 <b>Рабочие инструменты для заработка</b>\n\n"
        f"Выбери нужный сервис из списка ниже.\n"
        f"Каждый сервис содержит мануалы и боты для работы."
    )
    
    if not services:
        text += "\n\n<i>Пока нет доступных сервисов.</i>"
    
    await edit_with_brand(callback, text, reply_markup=get_services_keyboard(services), image_path=BRAND_IMAGE_SERVICES)


@router.callback_query(F.data.startswith("service_"))
async def show_service_detail(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        service_id = int(callback.data.split("_")[1])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    service = await get_service(service_id)
    if not service:
        await callback.answer("❌ Не найден", show_alert=True)
        return
    
    text = f"{service.get('icon', '🔹')} <b>{service['name']}</b>"
    if service.get('description'):
        text += f"\n\n{service['description']}"
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_service_detail_keyboard(service_id, service.get("manual_link"), service.get("bot_link"))
    )


@router.callback_query(F.data == "community")
async def show_community(callback: CallbackQuery) -> None:
    await callback.answer()
    
    # Get user stats to check profit requirement
    user_stats = await get_user_stats(callback.from_user.id)
    communities = await get_communities_for_user(callback.from_user.id)
    
    text = f"{header('Комьюнити', '👥')}\n\n"
    
    if user_stats.get('total_profit', 0) >= 50000:
        text += f"💰 {user_stats['total_profit']:.0f} RUB - можешь создать комьюнити!\n\n"
    else:
        needed = 50000 - user_stats.get('total_profit', 0)
        text += f"💰 Нужно ещё {needed:.0f} RUB для создания\n\n"
    
    if not communities:
        text += "<i>Пока нет доступных комьюнити.</i>"
    else:
        text += f"📋 Доступно: {len(communities)} комьюнити"
    
    await edit_with_brand(
        callback, text, 
        reply_markup=get_communities_keyboard(communities, user_stats.get('total_profit', 0)), 
        image_path=BRAND_IMAGE_COMMUNITY
    )


@router.callback_query(F.data == "choose_mentor")
async def show_mentors(callback: CallbackQuery) -> None:
    await callback.answer()
    
    services = await get_mentor_services()
    
    text = f"{header('Наставники', '👨‍🏫')}\n\n🎓 Выбери направление:"
    
    if not services:
        text += "\n\n<i>Пока нет доступных наставников.</i>"
        await edit_with_brand(callback, text, reply_markup=get_back_to_menu_keyboard(), image_path=BRAND_IMAGE_MENTORS)
        return
    
    await edit_with_brand(callback, text, reply_markup=get_mentor_services_keyboard(services), image_path=BRAND_IMAGE_MENTORS)


@router.callback_query(F.data.startswith("mentor_service_"))
async def show_mentors_by_service(callback: CallbackQuery) -> None:
    await callback.answer()
    
    service_name = callback.data[15:]  # Remove "mentor_service_" prefix
    mentors = await get_mentors_by_service(service_name)
    
    if not mentors:
        await callback.answer("❌ Нет наставников", show_alert=True)
        return
    
    text = f"👨‍🏫 <b>{service_name}</b>\n\nВыбери наставника:"
    await edit_with_brand(callback, text, reply_markup=get_mentor_selection_keyboard(mentors, service_name))


@router.callback_query(F.data.startswith("select_mentor_"))
async def show_mentor_detail(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        mentor_id = int(callback.data.split("_")[2])
        logger.info(f"User {callback.from_user.id} selecting mentor {mentor_id}")
    except (IndexError, ValueError) as e:
        logger.error(f"Error parsing mentor_id from callback data: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    # First get mentor to get user_id
    mentor = await get_mentor(mentor_id)
    
    if not mentor:
        logger.warning(f"Mentor {mentor_id} not found")
        await callback.answer("❌ Не найден", show_alert=True)
        return
    
    logger.info(f"Mentor {mentor_id} found: {mentor.get('full_name')}, user_id: {mentor.get('user_id')}")
    
    # Then parallel fetch current mentor and channel info
    try:
        current, channel_info = await asyncio.gather(
            get_user_mentor(callback.from_user.id),
            get_mentor_channel_info(mentor.get('user_id'))
        )
        logger.info(f"Got channel info: {channel_info is not None}")
    except Exception as e:
        logger.error(f"Error fetching mentor data: {e}")
        current = None
        channel_info = None
    
    has_mentor = current is not None
    # Проверяем, является ли пользователь учеником этого наставника
    is_student_of_this_mentor = current and current.get("id") == mentor_id
    username = f"@{mentor['username']}" if mentor.get('username') else ""
    
    text = (
        f"👨‍🏫 <b>{mentor['full_name']}</b> {username}\n\n"
        f"🛠 {mentor['service_name']}\n"
        f"💰 {mentor['percent']}% от профита\n"
        f"⭐ Рейтинг: {mentor.get('rating', 0):.0f}\n"
        f"👥 Учеников: {mentor.get('students_count', 0)}"
    )
    
    # Показываем канал только ученикам этого наставника
    if is_student_of_this_mentor and channel_info and channel_info.get('telegram_channel'):
        text += f"\n\n📺 <b>ТГК наставника:</b> {channel_info['telegram_channel']}"
        if channel_info.get('channel_description'):
            text += f"\n📝 {channel_info['channel_description']}"
        if channel_info.get('channel_invite_link'):
            text += f"\n🔗 {channel_info['channel_invite_link']}"
    
    if current and current.get("id") != mentor_id:
        text += "\n\n⚠️ У вас уже есть наставник."
    
    logger.info(f"Sending mentor detail to user {callback.from_user.id}, is_student: {is_student_of_this_mentor}")
    await edit_with_brand(callback, text, reply_markup=get_mentor_detail_keyboard(mentor_id, has_mentor, mentor['service_name']))


@router.callback_query(F.data.startswith("confirm_mentor_"))
async def confirm_mentor(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        mentor_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    mentor = await get_mentor(mentor_id)
    if not mentor:
        await callback.answer("❌ Не найден", show_alert=True)
        return
    
    current = await get_user_mentor(callback.from_user.id)
    if current and current.get("id") != mentor_id:
        await remove_mentor(callback.from_user.id)
    
    await assign_mentor(callback.from_user.id, mentor_id)
    
    text = (
        f"✅ <b>Наставник выбран!</b>\n\n"
        f"👨‍🏫 <b>{mentor['full_name']}</b>\n"
        f"🛠 {mentor['service_name']}\n\n"
        f"Теперь ты можешь обращаться к наставнику за помощью!"
    )
    
    await edit_with_brand(callback, text, reply_markup=get_back_to_menu_keyboard())


@router.callback_query(F.data == "remove_mentor")
async def remove_user_mentor(callback: CallbackQuery) -> None:
    await callback.answer()
    await remove_mentor(callback.from_user.id)
    
    text = (
        f"✅ <b>Наставник удален</b>\n\n"
        f"Ты можешь выбрать нового наставника\n"
        f"в любое время через главное меню."
    )
    
    await edit_with_brand(callback, text, reply_markup=get_back_to_menu_keyboard())


@router.callback_query(F.data == "direct_payments")
async def show_direct_payments(callback: CallbackQuery) -> None:
    await callback.answer()
    
    settings = await get_direct_payment_settings()
    if not settings:
        await callback.message.answer("❌ Не настроено.")
        return
    
    text = (
        f"{header('Прямики', '💳')}\n\n"
        f"💰 <b>Реквизиты для прямых выплат:</b>\n\n"
        f"<code>{settings['requisites']}</code>\n\n"
    )
    
    if settings.get('additional_info'):
        text += f"ℹ️ <b>Дополнительная информация:</b>\n{settings['additional_info']}\n\n"
    
    text += (
        f"📋 <i>Нажми на реквизиты чтобы скопировать</i>\n\n"
        f"📸 После перевода отправь скриншот в поддержку"
    )
    
    await edit_with_brand(callback, text, reply_markup=get_direct_payments_keyboard(settings['support_username']), image_path=BRAND_IMAGE_PAYMENTS)


@router.callback_query(F.data == "none")
async def ignore_none(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("community_view_"))
async def show_community_detail(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        community_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    community = await get_community(community_id)
    if not community:
        await callback.answer("❌ Комьюнити не найдено", show_alert=True)
        return
    
    is_member = await is_community_member(callback.from_user.id, community_id)
    creator_name = community.get('creator', {}).get('full_name', 'Неизвестный')
    
    text = (
        f"👥 <b>{community['name']}</b>\n\n"
        f"📝 <b>Описание:</b>\n{community.get('description', 'Описание отсутствует')}\n\n"
        f"👤 <b>Создатель:</b> {creator_name}\n"
        f"👥 <b>Участников:</b> {community['members_count']}\n"
        f"📅 <b>Создано:</b> {_format_date(community['created_at'])}\n\n"
    )
    
    if is_member:
        text += "✅ <b>Вы участник этого комьюнити</b>\n"
        text += f"💬 <b>Ссылка на чат:</b> {community['chat_link']}"
    else:
        text += "❌ <b>Вы не участник этого комьюнити</b>"
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_community_detail_keyboard(community_id, is_member),
        image_path=BRAND_IMAGE_COMMUNITY
    )


@router.callback_query(F.data.startswith("community_join_"))
async def join_community_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        community_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    success = await join_community(callback.from_user.id, community_id)
    if success:
        await callback.answer("✅ Вы присоединились к комьюнити!", show_alert=True)
        # Refresh the community detail view
        await show_community_detail(callback)
    else:
        await callback.answer("❌ Ошибка при присоединении", show_alert=True)


@router.callback_query(F.data.startswith("community_leave_"))
async def leave_community_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        community_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    success = await leave_community(callback.from_user.id, community_id)
    if success:
        await callback.answer("✅ Вы покинули комьюнити", show_alert=True)
        # Refresh the community detail view
        await show_community_detail(callback)
    else:
        await callback.answer("❌ Ошибка при выходе", show_alert=True)


@router.callback_query(F.data == "community_create")
async def start_community_creation(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    
    # Check profit requirement
    user_stats = await get_user_stats(callback.from_user.id)
    if user_stats.get('total_profit', 0) < 50000:
        await callback.answer("❌ Недостаточно профита для создания комьюнити", show_alert=True)
        return
    
    text = (
        f"{header('Создание комьюнити', '➕')}\n\n"
        f"🎯 <b>Шаг 1 из 3: Название</b>\n\n"
        f"Введите название для вашего комьюнити:\n"
        f"<i>Максимум 100 символов</i>"
    )
    
    await edit_with_brand(
        callback, text,
        reply_markup=get_community_create_keyboard(),
        image_path=BRAND_IMAGE_COMMUNITY
    )
    await state.set_state(CommunityCreateState.waiting_for_name)
