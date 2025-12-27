"""Chat group commands handlers."""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from database import (
    get_user, get_user_stats, get_top_workers, get_user_position,
    get_direct_payment_settings, get_active_user_ids
)
from config import ADMIN_IDS, BRAND_IMAGE_LOGO

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.reply(
        "📋 <b>КОМАНДЫ</b>\n\n"
        "👤 /me - Профиль\n"
        "/card - Реквизиты\n\n"
        "🏆 /top - Топ за всё время\n"
        "/topm - За месяц\n"
        "/topw - За неделю\n"
        "/topd - За день"
    )


@router.message(Command("me"))
async def cmd_me(message: Message) -> None:
    user = await get_user(message.from_user.id)
    
    if not user or user["status"] != "active":
        await message.reply("❌ Не зарегистрированы.")
        return
    
    stats = await get_user_stats(message.from_user.id)
    position = await get_user_position(message.from_user.id)
    
    username = f"@{user['username']}" if user.get('username') else user['full_name']
    
    text = "\n".join([
        f"👤 <b>{username}</b>",
        "",
        "💳 <b>Профиты:</b>",
        f"┣ За Все Время: {stats.get('total_profit', 0):.2f} RUB",
        f"┣ За День: {stats.get('day_profit', 0):.2f} RUB",
        f"┣ За Неделю: {stats.get('week_profit', 0):.2f} RUB",
        f"┣ За Месяц: {stats.get('month_profit', 0):.2f} RUB",
        f"┣ Кол-во: {stats.get('total_count', 0)}",
        f"┗ Место: {position['overall_rank']} из {position['total_users']}",
    ])
    
    try:
        photo = FSInputFile(BRAND_IMAGE_LOGO)
        await message.reply_photo(photo=photo, caption=text)
    except Exception:
        await message.reply(text)


@router.message(Command("card"))
async def cmd_card(message: Message) -> None:
    settings = await get_direct_payment_settings()
    
    if not settings:
        await message.reply("❌ Не настроено.")
        return
    
    text = f"💳 <b>РЕКВИЗИТЫ</b>\n\n<code>{settings['requisites']}</code>\n\n"
    if settings.get('additional_info'):
        text += f"ℹ️ {settings['additional_info']}\n\n"
    text += f"📸 Скрин: @{settings['support_username']}"
    
    try:
        photo = FSInputFile(BRAND_IMAGE_LOGO)
        await message.reply_photo(photo=photo, caption=text)
    except Exception:
        await message.reply(text)


@router.message(Command("top"))
async def cmd_top(message: Message) -> None:
    await _show_top(message, "all", "ЗА ВСЁ ВРЕМЯ")


@router.message(Command("topm"))
async def cmd_topm(message: Message) -> None:
    await _show_top(message, "month", "ЗА МЕСЯЦ")


@router.message(Command("topw"))
async def cmd_topw(message: Message) -> None:
    await _show_top(message, "week", "ЗА НЕДЕЛЮ")


@router.message(Command("topd"))
async def cmd_topd(message: Message) -> None:
    await _show_top(message, "day", "ЗА ДЕНЬ")


async def _show_top(message: Message, period: str, title: str) -> None:
    workers = await get_top_workers(period, 10)
    
    if not workers:
        await message.reply(f"🏆 Топ {title.lower()}\n\nНет данных.")
        return
    
    medals = ["🥇", "🥈", "🥉"]
    text = f"🏆 <b>ТОП-10 {title}</b>\n\n"
    
    for i, w in enumerate(workers[:10], 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = f"@{w['username']}" if w.get('username') else w['full_name']
        text += f"{medal} <b>{name}</b>\n   💰 {w['total_profit']:.2f} RUB • {w['profit_count']} шт\n"
    
    try:
        photo = FSInputFile(BRAND_IMAGE_LOGO)
        await message.reply_photo(photo=photo, caption=text)
    except Exception:
        await message.reply(text)


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        return
    
    users = await get_active_user_ids()
    top_all = await get_top_workers("all", 100)
    top_month = await get_top_workers("month", 100)
    top_day = await get_top_workers("day", 100)
    
    total_all = sum(w['total_profit'] for w in top_all)
    total_month = sum(w['total_profit'] for w in top_month)
    total_day = sum(w['total_profit'] for w in top_day)
    
    await message.reply(
        f"📊 <b>СТАТИСТИКА</b>\n\n"
        f"👥 Активных: <b>{len(users)}</b>\n\n"
        f"💰 Всего: <b>{total_all:.2f} RUB</b>\n"
        f"├ Месяц: {total_month:.2f} RUB\n"
        f"╰ День: {total_day:.2f} RUB"
    )
