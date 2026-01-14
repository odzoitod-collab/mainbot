"""Chat group commands handlers."""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import (
    get_user, get_user_stats, get_top_workers, get_user_position,
    get_direct_payment_settings, get_active_user_ids, get_team_stats_by_period,
    get_mentors, get_services, get_resources, get_referral_stats, get_user_referrals,
    update_user_tag, is_tag_available, get_service, get_mentors_by_service
)
from config import ADMIN_IDS, BRAND_IMAGE_LOGO
from utils.auto_delete import reply_with_auto_delete, reply_photo_with_auto_delete, is_group_chat
from states.all_states import ChangeTagState

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    try:
        photo = FSInputFile("images/ирл.jpg")
        await reply_photo_with_auto_delete(message, 
            photo=photo,
            caption="📋 <b>КОМАНДЫ</b>\n\n"
                    "👤 /me - Профиль\n"
                    "💳 /card - Реквизиты\n"
                    "🏷 /changetag - Сменить тег\n\n"
                    "🏆 /top - Топ за всё время\n"
                    "📅 /topm - За месяц\n"
                    "📊 /topw - За неделю\n"
                    "⏰ /topd - За день\n\n"
                    "💰 /kasa - Касса команды\n"
                    "👨‍🏫 /kurator - Список наставников\n\n"
                    "🛠 /сервисы - Список сервисов\n"
                    "📚 /ресурсы - Материалы\n"
                    "💬 /сообщество - Чаты\n"
                    "💡 /идеи - Идеи команды\n"
                    "🔗 /реф - Рефералка\n\n"
                    "ℹ️ /инфо - О команде\n"
                    "📜 /правила - Правила\n"
                    "🆘 /поддержка - Поддержка\n"
                    "⚡️ /быстро - Быстрые команды"
        )
    except Exception:
        await reply_with_auto_delete(message, 
            "📋 <b>КОМАНДЫ</b>\n\n"
            "👤 /me - Профиль\n"
            "💳 /card - Реквизиты\n"
            "🏷 /changetag - Сменить тег\n\n"
            "🏆 /top - Топ за всё время\n"
            "�  /topm - За месяц\n"
            "📊 /topw - За неделю\n"
            "⏰ /topd - За день\n\n"
            "💰 /kasa - Касса команды\n"
            "‍🏫 /kurator - Список наставников\n\n"
            "🛠 /сервисы - Список сервисов\n"
            "📚 /ресурсы - Материалы\n"
            "💬 /сообщество - Чаты\n"
            "💡 /идеи - Идеи команды\n"
            "🔗 /реф - Рефералка\n\n"
            "ℹ️ /инфо - О команде\n"
            "📜 /правила - Правила\n"
            "🆘 /поддержка - Поддержка\n"
            "⚡️ /быстро - Быстрые команды"
        )


@router.message(Command("me"))
async def cmd_me(message: Message) -> None:
    user = await get_user(message.from_user.id)
    
    if not user or user["status"] != "active":
        await reply_with_auto_delete(message, "❌ Не зарегистрированы.", delay=10, delete_original=True)
        return
    
    stats = await get_user_stats(message.from_user.id)
    position = await get_user_position(message.from_user.id)
    
    # Показываем тег вместо имени
    user_tag = user.get('user_tag', '#irl_???')
    
    text = "\n".join([
        f"🏷 <b>{user_tag}</b>",
        "",
        "💳 <b>Профиты:</b>",
        f"┣ За Все Время: {stats.get('total_profit', 0):.2f} RUB",
        f"┣ За День: {stats.get('day_profit', 0):.2f} RUB",
        f"┣ За Неделю: {stats.get('week_profit', 0):.2f} RUB",
        f"┣ За Месяц: {stats.get('month_profit', 0):.2f} RUB",
        f"┣ Кол-во: {stats.get('total_count', 0)}",
        f"┗ Место: {position['overall_rank']} из {position['total_users']}",
    ])
    
    # Создаем красивую инлайн клавиатуру
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏷 Сменить тег",
            callback_data="change_tag_menu"
        )]
    ])
    
    try:
        photo = FSInputFile("images/профиль.JPG")
        await reply_photo_with_auto_delete(message, photo=photo, caption=text, reply_markup=keyboard, delay=10, delete_original=True)
    except Exception:
        await reply_with_auto_delete(message, text, reply_markup=keyboard, delay=10, delete_original=True)


@router.message(Command("card"))
async def cmd_card(message: Message) -> None:
    settings = await get_direct_payment_settings()
    
    if not settings:
        await reply_with_auto_delete(message, "❌ Не настроено.", delay=10, delete_original=True)
        return
    
    text = f"💳 <b>РЕКВИЗИТЫ</b>\n\n<code>{settings['requisites']}</code>\n\n"
    if settings.get('additional_info'):
        text += f"ℹ️ {settings['additional_info']}\n\n"
    text += f"📸 Скрин: @{settings['support_username']}"
    
    try:
        photo = FSInputFile("images/Реквизиты.jpg")
        await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
    except Exception:
        await reply_with_auto_delete(message, text, delay=10, delete_original=True)


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
        await reply_with_auto_delete(message, f"🏆 Топ {title.lower()}\n\nНет данных.", delay=10, delete_original=True)
        return
    
    medals = ["🥇", "🥈", "🥉"]
    text = f"🏆 <b>ТОП-10 {title}</b>\n\n"
    
    for i, w in enumerate(workers[:10], 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        # Показываем тег вместо имени
        display_name = w.get('user_tag', '#irl_???')
        text += f"{medal} <b>{display_name}</b>\n   💰 {w['total_profit']:.2f} RUB • {w['profit_count']} шт\n"
    
    try:
        photo = FSInputFile("images/профиты.jpg")
        await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
    except Exception:
        await reply_with_auto_delete(message, text, delay=10, delete_original=True)


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
                # Показываем тег вместо имени
                display_name = worker.get('user_tag', '#irl_???')
                text += f"{i}. {display_name} - {worker['total_profit']:.2f} RUB\n"
        
        try:
            photo = FSInputFile("images/ирл.jpg")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_kasa: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения данных кассы.", delay=10, delete_original=True)


@router.message(Command("kurator"))
async def cmd_kurator(message: Message) -> None:
    """Показать список наставников с кнопками."""
    try:
        mentors = await get_mentors()
        
        if not mentors:
            await reply_with_auto_delete(message, "👨‍🏫 <b>НАСТАВНИКИ</b>\n\nНаставники не найдены.", delay=10, delete_original=True)
            return
        
        text = "👨‍🏫 <b>НАСТАВНИКИ</b>\n\nВыберите наставника:"
        
        # Создаем клавиатуру с наставниками
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        
        # Группируем наставников по сервисам
        services = {}
        for mentor in mentors:
            service = mentor['service_name']
            if service not in services:
                services[service] = []
            services[service].append(mentor)
        
        # Создаем кнопки по сервисам
        for service_name, service_mentors in services.items():
            mentor_count = len(service_mentors)
            avg_percent = sum(m.get('percent', 0) for m in service_mentors) / mentor_count if mentor_count > 0 else 0
            
            button_text = f"🛠 {service_name} • {mentor_count} наставников • {avg_percent:.0f}%"
            
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"mentors_service_{service_name[:30]}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        try:
            photo = FSInputFile("images/главное меню.jpg")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, reply_markup=keyboard, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, reply_markup=keyboard, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_kurator: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения списка наставников.", delay=10, delete_original=True)


@router.message(Command("services", "сервисы"))
async def cmd_services(message: Message) -> None:
    """Показать список сервисов с кнопками."""
    try:
        services = await get_services()
        
        if not services:
            await reply_with_auto_delete(message, "🛠 <b>СЕРВИСЫ</b>\n\nСервисы не найдены.", delay=10, delete_original=True)
            return
        
        text = "🛠 <b>СЕРВИСЫ</b>\n\nВыберите сервис:"
        
        # Создаем клавиатуру с сервисами
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        
        for service in services[:10]:  # Первые 10 сервисов
            icon = service.get('icon', '🔹')
            name = service['name']
            description = service.get('description', '')
            
            # Краткое описание для кнопки
            short_desc = description[:30] + "..." if len(description) > 30 else description
            button_text = f"{icon} {name}"
            if short_desc:
                button_text += f" • {short_desc}"
            
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"service_open_{service['id']}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        try:
            photo = FSInputFile("images/сервисы.JPG")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, reply_markup=keyboard, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, reply_markup=keyboard, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_services: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения списка сервисов.", delay=10, delete_original=True)


@router.message(Command("resources", "ресурсы"))
async def cmd_resources(message: Message) -> None:
    """Показать ресурсы и материалы с кнопками."""
    try:
        resources = await get_resources()
        
        if not resources:
            await reply_with_auto_delete(message, "📚 <b>РЕСУРСЫ</b>\n\nРесурсы не найдены.", delay=10, delete_original=True)
            return
        
        text = "📚 <b>МАТЕРИАЛЫ</b>\n\nВыберите материал:"
        
        # Создаем клавиатуру с ресурсами
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        
        # Группируем по типам
        materials = [r for r in resources if r.get('type') == 'resource']
        
        for resource in materials[:8]:  # Первые 8 материалов
            title = resource['title']
            # Краткий заголовок для кнопки
            short_title = title[:40] + "..." if len(title) > 40 else title
            
            buttons.append([InlineKeyboardButton(
                text=f"📖 {short_title}",
                url=resource['content_link']
            )])
        
        if not buttons:
            await reply_with_auto_delete(message, "� <b>МАТЕРИАЛЫ</b>\n\nМатериалы не найдены.", delay=10, delete_original=True)
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        try:
            photo = FSInputFile("images/главное меню.jpg")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, reply_markup=keyboard, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, reply_markup=keyboard, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_resources: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения ресурсов.", delay=10, delete_original=True)


@router.message(Command("community", "сообщество"))
async def cmd_community(message: Message) -> None:
    """Показать чаты сообщества с кнопками."""
    try:
        resources = await get_resources()
        community_chats = [r for r in resources if r.get('type') == 'community']
        
        if not community_chats:
            await reply_with_auto_delete(message, "💬 <b>ЧАТЫ</b>\n\nЧаты сообщества не найдены.", delay=10, delete_original=True)
            return
        
        text = "💬 <b>ЧАТЫ СООБЩЕСТВА</b>\n\nВыберите чат:"
        
        # Создаем клавиатуру с чатами
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        
        for chat in community_chats[:8]:  # Первые 8 чатов
            title = chat['title']
            # Краткий заголовок для кнопки
            short_title = title[:35] + "..." if len(title) > 35 else title
            
            buttons.append([InlineKeyboardButton(
                text=f"� {short_title}",
                url=chat['content_link']
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        try:
            photo = FSInputFile("images/главное меню.jpg")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, reply_markup=keyboard, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, reply_markup=keyboard, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_community: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения чатов сообщества.", delay=10, delete_original=True)


@router.message(Command("analytics", "аналитика"))
async def cmd_analytics(message: Message) -> None:
    """Показать аналитику (только для админов)."""
    if message.from_user.id not in ADMIN_IDS:
        await reply_with_auto_delete(message, "❌ Команда доступна только администраторам.", delay=10, delete_original=True)
        return
    
    try:
        # Получаем статистику за разные периоды
        team_all = await get_team_stats_by_period("all")
        team_month = await get_team_stats_by_period("month")
        team_week = await get_team_stats_by_period("week")
        team_today = await get_team_stats_by_period("today")
        
        users = await get_active_user_ids()
        top_workers = await get_top_workers("all", 5)
        
        text = "📊 <b>АНАЛИТИКА КОМАНДЫ</b>\n\n"
        
        text += "💰 <b>ПРОФИТЫ:</b>\n"
        text += f"├ Всего: {team_all['total_profit']:.2f} RUB\n"
        text += f"├ Месяц: {team_month['total_profit']:.2f} RUB\n"
        text += f"├ Неделя: {team_week['total_profit']:.2f} RUB\n"
        text += f"╰ Сегодня: {team_today['total_profit']:.2f} RUB\n\n"
        
        text += "👥 <b>АКТИВНОСТЬ:</b>\n"
        text += f"├ Всего воркеров: {len(users)}\n"
        text += f"├ Активных за месяц: {team_month['active_workers']}\n"
        text += f"├ Активных за неделю: {team_week['active_workers']}\n"
        text += f"╰ Активных сегодня: {team_today['active_workers']}\n\n"
        
        if top_workers:
            text += "🏆 <b>ТОП-5:</b>\n"
            for i, worker in enumerate(top_workers, 1):
                # Показываем тег вместо имени
                display_name = worker.get('user_tag', '#irl_???')
                text += f"{i}. {display_name} - {worker['total_profit']:.2f} RUB\n"
        
        try:
            photo = FSInputFile("images/главное меню.jpg")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_analytics: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения аналитики.", delay=10, delete_original=True)


@router.message(Command("ideas", "идеи"))
async def cmd_ideas(message: Message) -> None:
    """Показать идеи и предложения."""
    try:
        # Пытаемся получить идеи из базы данных
        # Если таблица идей не существует, показываем заглушку
        text = "💡 <b>ИДЕИ И ПРЕДЛОЖЕНИЯ</b>\n\n"
        text += "🔸 Здесь будут отображаться идеи от команды\n"
        text += "🔸 Предложения по улучшению работы\n"
        text += "🔸 Новые направления развития\n\n"
        text += "📝 Отправляйте свои идеи администраторам!"
        
        try:
            photo = FSInputFile("images/главное меню.jpg")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_ideas: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения идей.", delay=10, delete_original=True)


@router.message(Command("info", "инфо"))
async def cmd_info(message: Message) -> None:
    """Показать основную информацию о команде."""
    try:
        users = await get_active_user_ids()
        team_stats = await get_team_stats_by_period("all")
        services = await get_services()
        
        text = "ℹ️ <b>ИНФОРМАЦИЯ О КОМАНДЕ</b>\n\n"
        text += "🏢 <b>IRL Team</b> - команда профессионалов\n\n"
        text += "📊 <b>СТАТИСТИКА:</b>\n"
        text += f"├ Участников: {len(users)}\n"
        text += f"├ Общий профит: {team_stats['total_profit']:.2f} RUB\n"
        text += f"├ Сервисов: {len(services)}\n"
        text += f"╰ Активных воркеров: {team_stats['active_workers']}\n\n"
        text += "🚀 Присоединяйся к нашей команде!\n"
        text += "📱 Команды: /help"
        
        try:
            photo = FSInputFile("images/ирл.jpg")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_info: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения информации.", delay=10, delete_original=True)


@router.message(Command("rules", "правила"))
async def cmd_rules(message: Message) -> None:
    """Показать правила команды."""
    text = "📜 <b>ПРАВИЛА КОМАНДЫ</b>\n\n"
    text += "1️⃣ <b>Уважение</b> - относитесь друг к другу с уважением\n\n"
    text += "2️⃣ <b>Активность</b> - будьте активными участниками\n\n"
    text += "3️⃣ <b>Честность</b> - предоставляйте достоверную информацию\n\n"
    text += "4️⃣ <b>Развитие</b> - стремитесь к постоянному росту\n\n"
    text += "5️⃣ <b>Поддержка</b> - помогайте новичкам\n\n"
    text += "❗️ Нарушение правил может привести к исключению\n\n"
    text += "📞 Вопросы к администрации"
    
    try:
        photo = FSInputFile("images/главное меню.jpg")
        await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
    except Exception:
        await reply_with_auto_delete(message, text, delay=10, delete_original=True)


@router.message(Command("support", "поддержка"))
async def cmd_support(message: Message) -> None:
    """Показать контакты поддержки."""
    try:
        settings = await get_direct_payment_settings()
        support_username = settings.get('support_username', 'support') if settings else 'support'
        
        text = "🆘 <b>ПОДДЕРЖКА</b>\n\n"
        text += "📞 <b>Техническая поддержка:</b>\n"
        text += f"└ @{support_username}\n\n"
        text += "💬 <b>Вопросы по работе:</b>\n"
        text += "└ Обратитесь к наставнику (/kurator)\n\n"
        text += "🔧 <b>Проблемы с ботом:</b>\n"
        text += f"└ @{support_username}\n\n"
        text += "⏰ Время ответа: до 24 часов"
        
        try:
            photo = FSInputFile("images/главное меню.jpg")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_support: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения контактов поддержки.", delay=10, delete_original=True)


@router.message(Command("ref", "реф", "referral", "рефералка"))
async def cmd_referral(message: Message) -> None:
    """Показать информацию о реферальной программе."""
    try:
        user = await get_user(message.from_user.id)
        
        if not user or user["status"] != "active":
            await reply_with_auto_delete(message, "❌ Не зарегистрированы.", delay=10, delete_original=True)
            return
        
        # Получаем статистику рефералов
        ref_stats = await get_referral_stats(message.from_user.id)
        referrals = await get_user_referrals(message.from_user.id)
        
        text = "🔗 <b>РЕФЕРАЛЬНАЯ ПРОГРАММА</b>\n\n"
        text += f"👥 Приглашено: <b>{ref_stats['count']}</b>\n"
        text += f"💰 Заработано: <b>{ref_stats['earnings']:.2f} RUB</b>\n\n"
        
        if referrals:
            text += "📋 <b>ВАШИ РЕФЕРАЛЫ:</b>\n"
            for i, ref in enumerate(referrals[:5], 1):  # Первые 5
                name = f"@{ref['username']}" if ref.get('username') else ref['full_name']
                status_emoji = "✅" if ref['status'] == 'active' else "⏳"
                text += f"{i}. {status_emoji} {name}\n"
            
            if len(referrals) > 5:
                text += f"... и еще {len(referrals) - 5}\n"
            text += "\n"
        
        text += "🎯 Приглашайте друзей и получайте бонусы!\n"
        text += "📱 Ваша ссылка в боте: /start"
        
        try:
            photo = FSInputFile("images/профиль.JPG")
            await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
        except Exception:
            await reply_with_auto_delete(message, text, delay=10, delete_original=True)
            
    except Exception as e:
        logger.error(f"Error in cmd_referral: {e}")
        await reply_with_auto_delete(message, "❌ Ошибка получения данных рефералки.", delay=10, delete_original=True)


@router.message(Command("changetag"))
async def cmd_change_tag(message: Message) -> None:
    """Изменить тег пользователя."""
    user = await get_user(message.from_user.id)
    
    if not user or user["status"] != "active":
        await reply_with_auto_delete(message, "❌ Не зарегистрированы.", delay=10, delete_original=True)
        return
    
    # Получаем новый тег из сообщения
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        current_tag = user.get('user_tag', '#irl_???')
        await reply_with_auto_delete(message, 
            f"🏷 <b>СМЕНА ТЕГА</b>\n\n"
            f"Текущий тег: <b>{current_tag}</b>\n\n"
            f"Использование: <code>/changetag новый_тег</code>\n\n"
            f"Правила:\n"
            f"• Тег должен начинаться с #\n"
            f"• Длина: 3-20 символов\n"
            f"• Только буквы, цифры и _\n"
            f"• Пример: #irl_boss, #worker1"
        )
        return
    
    new_tag = args[1].strip()
    
    # Валидация тега
    if not new_tag.startswith('#'):
        await reply_with_auto_delete(message, "❌ Тег должен начинаться с символа #", delay=10, delete_original=True)
        return
    
    if len(new_tag) < 3 or len(new_tag) > 20:
        await reply_with_auto_delete(message, "❌ Длина тега должна быть от 3 до 20 символов", delay=10, delete_original=True)
        return
    
    # Проверяем символы (только буквы, цифры, подчеркивание)
    import re
    if not re.match(r'^#[a-zA-Z0-9_]+$', new_tag):
        await reply_with_auto_delete(message, "❌ Тег может содержать только буквы, цифры и символ _", delay=10, delete_original=True)
        return
    
    # Проверяем доступность тега
    if not await is_tag_available(new_tag, message.from_user.id):
        await reply_with_auto_delete(message, "❌ Этот тег уже занят. Выберите другой.", delay=10, delete_original=True)
        return
    
    # Обновляем тег
    success = await update_user_tag(message.from_user.id, new_tag)
    
    if success:
        await reply_with_auto_delete(message, 
            f"✅ <b>ТЕГ ИЗМЕНЕН</b>\n\n"
            f"Новый тег: <b>{new_tag}</b>\n\n"
            f"Теперь в топах и профитах будет отображаться ваш новый тег!"
        )
    else:
        await reply_with_auto_delete(message, "❌ Ошибка при смене тега. Попробуйте позже.", delay=10, delete_original=True)


@router.message(Command("quick", "быстро"))
async def cmd_quick(message: Message) -> None:
    """Быстрые команды."""
    text = "⚡️ <b>БЫСТРЫЕ КОМАНДЫ</b>\n\n"
    text += "👤 /me - Мой профиль\n"
    text += "🏆 /top - Топ воркеров\n"
    text += "💰 /kasa - Касса команды\n"
    text += "🛠 /сервисы - Сервисы\n"
    text += "🔗 /реф - Рефералка\n"
    text += "🆘 /поддержка - Поддержка\n\n"
    text += "📋 Все команды: /help"
    
    try:
        photo = FSInputFile("images/ирл.jpg")
        await reply_photo_with_auto_delete(message, photo=photo, caption=text, delay=10, delete_original=True)
    except Exception:
        await reply_with_auto_delete(message, text, delay=10, delete_original=True)


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
    
    await reply_with_auto_delete(message, 
        f"📊 <b>СТАТИСТИКА</b>\n\n"
        f"👥 Активных: <b>{len(users)}</b>\n\n"
        f"💰 Всего: <b>{total_all:.2f} RUB</b>\n"
        f"├ Месяц: {total_month:.2f} RUB\n"
        f"╰ День: {total_day:.2f} RUB"
    )


# ============================================
# ОБРАБОТЧИКИ CALLBACK КНОПОК ДЛЯ КОМАНД
# ============================================

@router.callback_query(F.data.startswith("service_open_"))
async def handle_service_open(callback: CallbackQuery) -> None:
    """Обработчик открытия сервиса."""
    await callback.answer()
    
    try:
        service_id = int(callback.data.split("_")[-1])
        service = await get_service(service_id)
        
        if not service:
            await callback.message.edit_text("❌ Сервис не найден.")
            return
        
        icon = service.get('icon', '🔹')
        name = service['name']
        description = service.get('description', 'Описание отсутствует')
        manual_link = service.get('manual_link')
        bot_link = service.get('bot_link')
        
        text = f"{icon} <b>{name}</b>\n\n📝 {description}\n\n"
        
        # Создаем кнопки для ссылок
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        
        if manual_link and manual_link.strip():
            buttons.append([InlineKeyboardButton(
                text="📖 Открыть мануал",
                url=manual_link.strip()
            )])
        
        if bot_link and bot_link.strip():
            buttons.append([InlineKeyboardButton(
                text="🤖 Перейти к боту",
                url=bot_link.strip()
            )])
        
        # Кнопка назад
        buttons.append([InlineKeyboardButton(
            text="🔙 К списку сервисов",
            callback_data="back_to_services"
        )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in handle_service_open: {e}")
        await callback.message.edit_text("❌ Ошибка загрузки сервиса.")


@router.callback_query(F.data.startswith("mentors_service_"))
async def handle_mentors_service(callback: CallbackQuery) -> None:
    """Обработчик показа наставников по сервису."""
    await callback.answer()
    
    try:
        service_name = callback.data.replace("mentors_service_", "")
        mentors = await get_mentors_by_service(service_name)
        
        if not mentors:
            await callback.message.edit_text(f"❌ Наставники по сервису '{service_name}' не найдены.")
            return
        
        text = f"👨‍🏫 <b>НАСТАВНИКИ • {service_name}</b>\n\n"
        
        for mentor in mentors[:8]:  # Первые 8 наставников
            # Показываем тег вместо имени
            display_name = mentor.get('user_tag', f"@{mentor['username']}" if mentor.get('username') else mentor['full_name'])
            students = mentor.get('students_count', 0)
            percent = mentor.get('percent', 0)
            rating = mentor.get('rating', 0)
            
            text += f"🏷 <b>{display_name}</b>\n"
            text += f"   💰 {percent}% • ⭐ {rating:.1f} • 👥 {students}\n\n"
        
        # Кнопка назад
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔙 К списку сервисов",
                callback_data="back_to_mentors"
            )]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error in handle_mentors_service: {e}")
        await callback.message.edit_text("❌ Ошибка загрузки наставников.")


@router.callback_query(F.data == "back_to_services")
async def handle_back_to_services(callback: CallbackQuery) -> None:
    """Возврат к списку сервисов."""
    await callback.answer()
    
    try:
        services = await get_services()
        
        if not services:
            await callback.message.edit_text("🛠 <b>СЕРВИСЫ</b>\n\nСервисы не найдены.")
            return
        
        text = "🛠 <b>СЕРВИСЫ</b>\n\nВыберите сервис:"
        
        # Создаем клавиатуру с сервисами
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        
        for service in services[:10]:  # Первые 10 сервисов
            icon = service.get('icon', '🔹')
            name = service['name']
            description = service.get('description', '')
            
            # Краткое описание для кнопки
            short_desc = description[:30] + "..." if len(description) > 30 else description
            button_text = f"{icon} {name}"
            if short_desc:
                button_text += f" • {short_desc}"
            
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"service_open_{service['id']}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error returning to services: {e}")
        await callback.message.edit_text("❌ Ошибка. Используйте /сервисы")


@router.callback_query(F.data == "back_to_mentors")
async def handle_back_to_mentors(callback: CallbackQuery) -> None:
    """Возврат к списку наставников."""
    await callback.answer()
    
    try:
        mentors = await get_mentors()
        
        if not mentors:
            await callback.message.edit_text("👨‍🏫 <b>НАСТАВНИКИ</b>\n\nНаставники не найдены.")
            return
        
        text = "👨‍🏫 <b>НАСТАВНИКИ</b>\n\nВыберите наставника:"
        
        # Создаем клавиатуру с наставниками
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        
        # Группируем наставников по сервисам
        services = {}
        for mentor in mentors:
            service = mentor['service_name']
            if service not in services:
                services[service] = []
            services[service].append(mentor)
        
        # Создаем кнопки по сервисам
        for service_name, service_mentors in services.items():
            mentor_count = len(service_mentors)
            avg_percent = sum(m.get('percent', 0) for m in service_mentors) / mentor_count if mentor_count > 0 else 0
            
            button_text = f"🛠 {service_name} • {mentor_count} наставников • {avg_percent:.0f}%"
            
            buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"mentors_service_{service_name[:30]}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error returning to mentors: {e}")
        await callback.message.edit_text("❌ Ошибка. Используйте /kurator")


# ============================================
# ОБРАБОТЧИКИ СМЕНЫ ТЕГА
# ============================================

@router.callback_query(F.data == "change_tag_menu")
async def handle_change_tag_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Показать меню смены тега."""
    try:
        await callback.answer()
        
        # Очищаем состояние если было
        await state.clear()
        
        user = await get_user(callback.from_user.id)
        if not user:
            # Проверяем тип сообщения
            if callback.message.photo:
                await callback.message.edit_caption(caption="❌ Пользователь не найден.")
            else:
                await callback.message.edit_text("❌ Пользователь не найден.")
            return
        
        current_tag = user.get('user_tag', '#irl_???')
        
        text = (
            "🏷 <b>СМЕНА ТЕГА</b>\n\n"
            f"Текущий тег: <b>{current_tag}</b>\n\n"
            "📝 <b>Правила для нового тега:</b>\n"
            "• Начинается с символа #\n"
            "• Длина: 3-20 символов\n"
            "• Только буквы, цифры и _\n"
            "• Должен быть уникальным\n\n"
            "💡 <b>Примеры:</b>\n"
            "<code>#irl_boss</code>, <code>#worker1</code>, <code>#pro_trader</code>\n\n"
            "Нажмите кнопку ниже для смены тега:"
        )
        
        # Создаем красивую клавиатуру
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✏️ Ввести новый тег",
                callback_data="start_tag_change"
            )],
            [InlineKeyboardButton(
                text="🎲 Случайный тег",
                callback_data="random_tag"
            )],
            [InlineKeyboardButton(
                text="🔙 Назад к профилю",
                callback_data="profile"
            )]
        ])
        
        # Проверяем тип сообщения и используем правильный метод
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error in change_tag_menu: {e}", exc_info=True)
        try:
            if callback.message.photo:
                await callback.message.edit_caption(caption="❌ Ошибка загрузки меню смены тега.")
            else:
                await callback.message.edit_text("❌ Ошибка загрузки меню смены тега.")
        except:
            await callback.answer("❌ Ошибка загрузки меню смены тега.", show_alert=True)


@router.callback_query(F.data == "start_tag_change")
async def handle_start_tag_change(callback: CallbackQuery, state: FSMContext) -> None:
    """Начать процесс смены тега."""
    try:
        await callback.answer()
        
        text = (
            "✏️ <b>ВВОД НОВОГО ТЕГА</b>\n\n"
            "Отправьте новый тег в этот чат.\n\n"
            "📝 <b>Формат:</b> <code>#новый_тег</code>\n\n"
            "💡 <b>Примеры:</b>\n"
            "• <code>#irl_boss</code>\n"
            "• <code>#worker1</code>\n"
            "• <code>#pro_trader</code>\n\n"
            "📋 <b>Правила:</b>\n"
            "• Начинается с #\n"
            "• Длина: 3-20 символов\n"
            "• Только буквы, цифры и _\n\n"
            "⚠️ Тег должен быть уникальным!"
        )
        
        # Кнопка назад
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="❌ Отменить",
                callback_data="change_tag_menu"
            )]
        ])
        
        # Проверяем тип сообщения
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
        # Устанавливаем состояние ожидания тега
        await state.set_state(ChangeTagState.waiting_for_tag)
        logger.info(f"User {callback.from_user.id} entered tag change state")
        
    except Exception as e:
        logger.error(f"Error in start_tag_change: {e}", exc_info=True)
        try:
            if callback.message.photo:
                await callback.message.edit_caption(caption="❌ Ошибка. Попробуйте еще раз.")
            else:
                await callback.message.edit_text("❌ Ошибка. Попробуйте еще раз.")
        except:
            await callback.answer("❌ Ошибка. Попробуйте еще раз.", show_alert=True)


@router.callback_query(F.data == "random_tag")
async def handle_random_tag(callback: CallbackQuery) -> None:
    """Сгенерировать случайный тег."""
    await callback.answer()
    
    try:
        import random
        import string
        
        # Генерируем случайный тег
        adjectives = ['pro', 'top', 'best', 'cool', 'fast', 'smart', 'elite', 'mega', 'super', 'ultra']
        nouns = ['worker', 'trader', 'boss', 'king', 'master', 'expert', 'ninja', 'legend', 'hero', 'star']
        numbers = [''.join(random.choices(string.digits, k=2)) for _ in range(3)]
        
        # Создаем несколько вариантов
        variants = []
        for _ in range(5):
            variant_type = random.choice(['adj_noun', 'adj_num', 'noun_num', 'irl_num'])
            
            if variant_type == 'adj_noun':
                tag = f"#{random.choice(adjectives)}_{random.choice(nouns)}"
            elif variant_type == 'adj_num':
                tag = f"#{random.choice(adjectives)}{random.choice(numbers)}"
            elif variant_type == 'noun_num':
                tag = f"#{random.choice(nouns)}{random.choice(numbers)}"
            else:  # irl_num
                tag = f"#irl_{random.choice(numbers)}{random.choice(string.ascii_lowercase)}"
            
            # Проверяем доступность
            if await is_tag_available(tag, callback.from_user.id):
                variants.append(tag)
        
        if not variants:
            text = (
                "😅 <b>НЕ УДАЛОСЬ СГЕНЕРИРОВАТЬ</b>\n\n"
                "Все случайные теги заняты.\n"
                "Попробуйте ввести тег вручную."
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="change_tag_menu")]
            ])
            
            if callback.message.photo:
                await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            return
        
        text = (
            "🎲 <b>СЛУЧАЙНЫЕ ТЕГИ</b>\n\n"
            "Выберите понравившийся тег:\n\n"
        )
        
        # Создаем кнопки с вариантами
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        buttons = []
        
        for tag in variants[:3]:  # Показываем первые 3
            buttons.append([InlineKeyboardButton(
                text=f"🏷 {tag}",
                callback_data=f"select_tag_{tag[1:]}"  # Убираем # для callback
            )])
        
        # Кнопки управления
        buttons.extend([
            [InlineKeyboardButton(
                text="🎲 Другие варианты",
                callback_data="random_tag"
            )],
            [InlineKeyboardButton(
                text="🔙 Назад к меню",
                callback_data="change_tag_menu"
            )]
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        # Проверяем тип сообщения
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error generating random tag: {e}", exc_info=True)
        try:
            if callback.message.photo:
                await callback.message.edit_caption(caption="❌ Ошибка генерации тега.")
            else:
                await callback.message.edit_text("❌ Ошибка генерации тега.")
        except:
            await callback.answer("❌ Ошибка генерации тега.", show_alert=True)


@router.callback_query(F.data.startswith("select_tag_"))
async def handle_select_tag(callback: CallbackQuery, state: FSMContext) -> None:
    """Выбрать сгенерированный тег."""
    try:
        await callback.answer()
        
        # Очищаем состояние
        await state.clear()
        
        tag_without_hash = callback.data.replace("select_tag_", "")
        new_tag = f"#{tag_without_hash}"
        
        logger.info(f"User {callback.from_user.id} selecting tag: {new_tag}")
        
        # Проверяем доступность еще раз
        is_available = await is_tag_available(new_tag, callback.from_user.id)
        logger.info(f"Tag {new_tag} availability: {is_available}")
        
        if not is_available:
            text = (
                f"❌ <b>ТЕГ ЗАНЯТ</b>\n\n"
                f"Тег <code>{new_tag}</code> уже занят другим пользователем.\n"
                "Попробуйте другой вариант."
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="random_tag")]
            ])
            
            if callback.message.photo:
                await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            return
        
        # Обновляем тег
        success = await update_user_tag(callback.from_user.id, new_tag)
        logger.info(f"Tag update result for user {callback.from_user.id}: {success}")
        
        if success:
            text = (
                f"✅ <b>ТЕГ ИЗМЕНЕН</b>\n\n"
                f"Ваш новый тег: <b>{new_tag}</b>\n\n"
                f"🎉 Теперь в топах и профитах будет отображаться ваш новый тег!"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="👤 Посмотреть профиль",
                    callback_data="profile"
                )]
            ])
            
            if callback.message.photo:
                await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
            else:
                await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            if callback.message.photo:
                await callback.message.edit_caption(caption="❌ Ошибка при смене тега. Попробуйте позже.")
            else:
                await callback.message.edit_text("❌ Ошибка при смене тега. Попробуйте позже.")
            
    except Exception as e:
        logger.error(f"Error selecting tag: {e}", exc_info=True)
        try:
            if callback.message.photo:
                await callback.message.edit_caption(caption="❌ Ошибка при смене тега.")
            else:
                await callback.message.edit_text("❌ Ошибка при смене тега.")
        except:
            await callback.answer("❌ Ошибка при смене тега.", show_alert=True)


@router.callback_query(F.data == "back_to_profile")
async def handle_back_to_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Вернуться к профилю."""
    try:
        await callback.answer()
        
        # Очищаем состояние
        await state.clear()
        
        user = await get_user(callback.from_user.id)
        
        if not user or user["status"] != "active":
            if callback.message.photo:
                await callback.message.edit_caption(caption="❌ Не зарегистрированы.")
            else:
                await callback.message.edit_text("❌ Не зарегистрированы.")
            return
        
        stats = await get_user_stats(callback.from_user.id)
        position = await get_user_position(callback.from_user.id)
        
        # Показываем тег вместо имени
        user_tag = user.get('user_tag', '#irl_???')
        
        text = "\n".join([
            f"🏷 <b>{user_tag}</b>",
            "",
            "💳 <b>Профиты:</b>",
            f"┣ За Все Время: {stats.get('total_profit', 0):.2f} RUB",
            f"┣ За День: {stats.get('day_profit', 0):.2f} RUB",
            f"┣ За Неделю: {stats.get('week_profit', 0):.2f} RUB",
            f"┣ За Месяц: {stats.get('month_profit', 0):.2f} RUB",
            f"┣ Кол-во: {stats.get('total_count', 0)}",
            f"┗ Место: {position['overall_rank']} из {position['total_users']}",
        ])
        
        # Создаем клавиатуру
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🏷 Сменить тег",
                callback_data="change_tag_menu"
            )]
        ])
        
        # Проверяем тип сообщения
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Error returning to profile: {e}", exc_info=True)
        try:
            if callback.message.photo:
                await callback.message.edit_caption(caption="❌ Ошибка загрузки профиля.")
            else:
                await callback.message.edit_text("❌ Ошибка загрузки профиля.")
        except:
            await callback.answer("❌ Ошибка загрузки профиля.", show_alert=True)



# ============================================
# FSM ОБРАБОТЧИКИ ДЛЯ СМЕНЫ ТЕГА
# ============================================

@router.message(ChangeTagState.waiting_for_tag)
async def process_new_tag(message: Message, state: FSMContext) -> None:
    """Обработка нового тега от пользователя."""
    try:
        logger.info(f"Processing new tag from user {message.from_user.id}: {message.text}")
        
        if not message.text:
            await message.reply("❌ Отправьте текст с новым тегом.")
            return
        
        new_tag = message.text.strip()
        
        # Валидация тега
        if not new_tag.startswith('#'):
            await message.reply("❌ Тег должен начинаться с символа #\n\nПопробуйте еще раз:")
            return
        
        if len(new_tag) < 3 or len(new_tag) > 20:
            await message.reply("❌ Длина тега должна быть от 3 до 20 символов\n\nПопробуйте еще раз:")
            return
        
        # Проверяем символы (только буквы, цифры, подчеркивание)
        import re
        if not re.match(r'^#[a-zA-Z0-9_]+$', new_tag):
            await message.reply("❌ Тег может содержать только буквы, цифры и символ _\n\nПопробуйте еще раз:")
            return
        
        # Проверяем доступность тега
        is_available = await is_tag_available(new_tag, message.from_user.id)
        logger.info(f"Tag {new_tag} availability: {is_available}")
        
        if not is_available:
            await message.reply("❌ Этот тег уже занят. Выберите другой.\n\nПопробуйте еще раз:")
            return
        
        # Обновляем тег
        success = await update_user_tag(message.from_user.id, new_tag)
        logger.info(f"Tag update result for user {message.from_user.id}: {success}")
        
        if success:
            # Создаем клавиатуру для возврата к профилю
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="👤 Посмотреть профиль",
                    callback_data="profile"
                )]
            ])
            
            await message.reply(
                f"✅ <b>ТЕГ ИЗМЕНЕН</b>\n\n"
                f"Ваш новый тег: <b>{new_tag}</b>\n\n"
                f"🎉 Теперь в топах и профитах будет отображаться ваш новый тег!",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Очищаем состояние
            await state.clear()
            logger.info(f"Tag change completed successfully for user {message.from_user.id}")
        else:
            await message.reply("❌ Ошибка при смене тега. Попробуйте позже.")
            await state.clear()
            
    except Exception as e:
        logger.error(f"Error in process_new_tag: {e}", exc_info=True)
        await message.reply("❌ Произошла ошибка. Попробуйте позже.")
        await state.clear()
