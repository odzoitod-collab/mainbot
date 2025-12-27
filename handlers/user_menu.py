"""Optimized user main menu and navigation handlers."""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from contextlib import suppress

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, TelegramObject

from keyboards.user_kb import (
    get_main_menu_keyboard, get_profile_keyboard, get_profit_history_keyboard,
    get_services_keyboard, get_service_detail_keyboard, get_resources_keyboard,
    get_back_to_menu_keyboard, get_mentor_services_keyboard, get_mentor_selection_keyboard,
    get_mentor_detail_keyboard, get_direct_payments_keyboard, get_referral_keyboard
)
from database import (
    get_user, get_user_stats, get_user_profits, get_services, get_service,
    get_resources, get_user_mentor, get_mentor,
    get_mentor_services, get_mentors_by_service,
    assign_mentor, remove_mentor, update_user_activity, get_direct_payment_settings,
    get_referral_stats, get_user_position, get_profile_data
)
from utils.messages import answer_with_brand, edit_with_brand
from utils.design import header, profit_card
from config import ADMIN_IDS, BRAND_IMAGE_LOGO

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
        mentor_name = f"@{mentor['username']}" if mentor.get('username') else mentor.get('full_name', 'Наставник')
    
    username = f"@{user['username']}" if user.get('username') else "—"
    
    return (
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
    text = header('Главное меню', '💠')
    kb = get_main_menu_keyboard(0, is_admin)
    
    if isinstance(event, CallbackQuery):
        await edit_with_brand(event, text, reply_markup=kb)
    else:
        await answer_with_brand(event, text, reply_markup=kb, image_path=BRAND_IMAGE_LOGO)


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await show_main_menu(callback)


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery) -> None:
    await callback.answer()
    
    # Parallel data loading
    data = await get_profile_data(callback.from_user.id)
    
    if not data["user"]:
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    text = _build_profile_text(data["user"], data["stats"], data["position"], data["mentor"])
    await edit_with_brand(callback, text, reply_markup=get_profile_keyboard())


@router.callback_query(F.data == "referral_link")
async def show_referral_link(callback: CallbackQuery) -> None:
    from config import BOT_USERNAME, WEBSITE_URL, REFERRAL_PERCENT
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
    
    await edit_with_brand(callback, text, reply_markup=get_referral_keyboard(ref_link, WEBSITE_URL))


@router.callback_query(F.data == "profit_history")
async def show_profit_history(callback: CallbackQuery) -> None:
    await callback.answer()
    
    profits = await get_user_profits(callback.from_user.id)
    text, total_pages = _build_profit_history(profits, 0)
    await edit_with_brand(callback, text, reply_markup=get_profit_history_keyboard(0, total_pages))


@router.callback_query(F.data.startswith("profit_page_"))
async def paginate_profits(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        page = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        page = 0
    
    profits = await get_user_profits(callback.from_user.id)
    text, total_pages = _build_profit_history(profits, page)
    await edit_with_brand(callback, text, reply_markup=get_profit_history_keyboard(page, total_pages))


@router.callback_query(F.data == "services")
async def show_services(callback: CallbackQuery) -> None:
    await callback.answer()
    
    services = await get_services()
    text = header("Сервисы", "🛠")
    await edit_with_brand(callback, text, reply_markup=get_services_keyboard(services))


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
    
    resources = await get_resources()
    text = header("Материалы", "📚")
    await edit_with_brand(callback, text, reply_markup=get_resources_keyboard(resources))


@router.callback_query(F.data == "choose_mentor")
async def show_mentors(callback: CallbackQuery) -> None:
    await callback.answer()
    
    services = await get_mentor_services()
    text = header("Наставники", "👨‍🏫")
    
    if not services:
        await edit_with_brand(callback, text + "\n\nПока нет наставников.", reply_markup=get_back_to_menu_keyboard("mentors"))
        return
    
    await edit_with_brand(callback, text, reply_markup=get_mentor_services_keyboard(services))


@router.callback_query(F.data.startswith("mentor_service_"))
async def show_mentors_by_service(callback: CallbackQuery) -> None:
    await callback.answer()
    
    service_name = callback.data[15:]  # Remove "mentor_service_" prefix
    mentors = await get_mentors_by_service(service_name)
    
    if not mentors:
        await callback.answer("❌ Нет наставников", show_alert=True)
        return
    
    text = f"👨‍🏫 <b>Наставники: {service_name}</b>"
    await edit_with_brand(callback, text, reply_markup=get_mentor_selection_keyboard(mentors, service_name))


@router.callback_query(F.data.startswith("select_mentor_"))
async def show_mentor_detail(callback: CallbackQuery) -> None:
    await callback.answer()
    
    try:
        mentor_id = int(callback.data.split("_")[2])
    except (IndexError, ValueError):
        await callback.answer("❌ Ошибка", show_alert=True)
        return
    
    # Parallel fetch
    mentor, current = await asyncio.gather(
        get_mentor(mentor_id),
        get_user_mentor(callback.from_user.id)
    )
    
    if not mentor:
        await callback.answer("❌ Не найден", show_alert=True)
        return
    
    has_mentor = current is not None
    username = f"@{mentor['username']}" if mentor.get('username') else ""
    
    text = (
        f"👨‍🏫 <b>{mentor['full_name']}</b> {username}\n\n"
        f"🛠 {mentor['service_name']}\n"
        f"💰 {mentor['percent']}% от профита\n"
        f"⭐ Рейтинг: {mentor.get('rating', 0):.0f}\n"
        f"👥 Учеников: {mentor.get('students_count', 0)}"
    )
    
    if current and current.get("id") != mentor_id:
        text += "\n\n⚠️ У вас уже есть наставник."
    
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
    await edit_with_brand(callback, f"✅ Наставник: {mentor['full_name']}", reply_markup=get_back_to_menu_keyboard("mentors"))


@router.callback_query(F.data == "remove_mentor")
async def remove_user_mentor(callback: CallbackQuery) -> None:
    await callback.answer()
    await remove_mentor(callback.from_user.id)
    await edit_with_brand(callback, "✅ Наставник удален.", reply_markup=get_back_to_menu_keyboard("mentors"))


@router.callback_query(F.data == "direct_payments")
async def show_direct_payments(callback: CallbackQuery) -> None:
    await callback.answer()
    
    settings = await get_direct_payment_settings()
    if not settings:
        await callback.message.answer("❌ Не настроено.")
        return
    
    text = (
        f"{header('Прямики', '💳')}\n\n"
        f"<b>Реквизиты:</b>\n<code>{settings['requisites']}</code>\n\n"
    )
    
    if settings.get('additional_info'):
        text += f"<b>Инфо:</b>\n{settings['additional_info']}\n\n"
    
    text += "<i>Нажмите на реквизиты чтобы скопировать.</i>"
    
    await edit_with_brand(callback, text, reply_markup=get_direct_payments_keyboard(settings['support_username']))


@router.callback_query(F.data == "none")
async def ignore_none(callback: CallbackQuery) -> None:
    await callback.answer()
