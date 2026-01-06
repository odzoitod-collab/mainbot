"""Chat group commands handlers."""
import logging
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile

from database import (
    get_user, get_user_stats, get_top_workers, get_user_position,
    get_direct_payment_settings, get_active_user_ids, get_team_stats_by_period,
    get_mentors
)
from config import ADMIN_IDS, BRAND_IMAGE_LOGO

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    try:
        photo = FSInputFile("images/главное.jpg")
        await message.reply_photo(
            photo=photo,
            caption="📋 <b>КОМАНДЫ</b>\n\n"
                    "👤 /me - Профиль\n"
                    "💳 /card - Реквизиты\n\n"
                    "🏆 /top - Топ за всё время\n"
                    "📅 /topm - За месяц\n"
                    "📊 /topw - За неделю\n"
                    "⏰ /topd - За день\n\n"
                    "💰 /kasa - Касса команды\n"
                    "👨‍🏫 /kurator - Список наставников"
        )
    except Exception:
        await message.reply(
            "📋 <b>КОМАНДЫ</b>\n\n"
            "👤 /me - Профиль\n"
            "💳 /card - Реквизиты\n\n"
            "🏆 /top - Топ за всё время\n"
            "📅 /topm - За месяц\n"
            "📊 /topw - За неделю\n"
            "⏰ /topd - За день\n\n"
            "💰 /kasa - Касса команды\n"
            "👨‍🏫 /kurator - Список наставников"
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
        photo = FSInputFile("images/профиль.jpg")
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
        photo = FSInputFile("images/Реквизиты.jpg")
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
        photo = FSInputFile("images/профиты.jpg")
        await message.reply_photo(photo=photo, caption=text)
    except Exception:
        await message.reply(text)


@router.message(Command("kasa"))
async def cmd_kasa(message: Message) -> None:
    """Показать кассу команды за все время."""
    try:
        # Получаем статистику команды за все время
        team_stats = await get_team_stats_by_period("all")
        top_workers = await get_top_workers("all", 5)
        
        text = "💰 <b>КАССА КОМАНДЫ</b>\n\n"
        text += f"💵 Общий профит: <b>{team_stats['total_profit']:.2f} RUB</b>\n"
        text += f"📊 Количество профитов: <b>{team_stats['profits_count']}</b>\n"
        text += f"👥 Активных воркеров: <b>{team_stats['active_workers']}</b>\n"
        text += f"📈 Средний профит: <b>{team_stats['avg_profit']:.2f} RUB</b>\n\n"
        
        if top_workers:
            text += "🏆 <b>ТОП-5 ВОРКЕРОВ:</b>\n"
            for i, worker in enumerate(top_workers[:5], 1):
                name = f"@{worker['username']}" if worker.get('username') else worker['full_name']
                text += f"{i}. {name} - {worker['total_profit']:.2f} RUB\n"
        
        try:
            photo = FSInputFile("images/главное.jpg")
            await message.reply_photo(photo=photo, caption=text)
        except Exception:
            await message.reply(text)
            
    except Exception as e:
        logger.error(f"Error in cmd_kasa: {e}")
        await message.reply("❌ Ошибка получения данных кассы.")


@router.message(Command("kurator"))
async def cmd_kurator(message: Message) -> None:
    """Показать список наставников."""
    try:
        mentors = await get_mentors()
        
        if not mentors:
            await message.reply("👨‍🏫 <b>НАСТАВНИКИ</b>\n\nНаставники не найдены.")
            return
        
        text = "👨‍🏫 <b>СПИСОК НАСТАВНИКОВ</b>\n\n"
        
        # Группируем наставников по сервисам
        services = {}
        for mentor in mentors:
            service = mentor['service_name']
            if service not in services:
                services[service] = []
            services[service].append(mentor)
        
        for service_name, service_mentors in services.items():
            text += f"🔹 <b>{service_name}</b>\n"
            for mentor in service_mentors:
                name = f"@{mentor['username']}" if mentor.get('username') else mentor['full_name']
                students = mentor.get('students_count', 0)
                percent = mentor.get('percent', 0)
                text += f"   • {name} ({percent}% | {students} учеников)\n"
            text += "\n"
        
        try:
            photo = FSInputFile("images/наставники.jpg")
            await message.reply_photo(photo=photo, caption=text)
        except Exception:
            await message.reply(text)
            
    except Exception as e:
        logger.error(f"Error in cmd_kurator: {e}")
        await message.reply("❌ Ошибка получения списка наставников.")


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
