"""User keyboards for main menu and navigation."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from typing import List, Dict, Any

import config


def get_main_menu_keyboard(unread_notifications: int = 0, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Get main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="📊 Аналитика", web_app=WebAppInfo(url=config.WEBAPP_ANALYTICS))
        ],
        [
            InlineKeyboardButton(text="🌐 Хаб", web_app=WebAppInfo(url=config.WEBAPP_HUB)),
            InlineKeyboardButton(text="👨‍🏫 Наставники", callback_data="choose_mentor")
        ],
        [
            InlineKeyboardButton(text="💳 Прямики", callback_data="direct_payments")
        ]
    ]

    if is_admin:
        keyboard.append([InlineKeyboardButton(text="🛡 Админ меню", callback_data="admin_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Get profile inline keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="� Исатория профитов", web_app=WebAppInfo(url=config.WEBAPP_PROFITS_HISTORY))],
        [InlineKeyboardButton(text="🔗 Реферальная ссылка", callback_data="referral_link")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])


def get_profit_history_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Get profit history keyboard with pagination."""
    buttons = []
    
    # Pagination row
    if total_pages > 1:
        pagination_row = []
        
        if current_page > 0:
            pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"profit_page_{current_page - 1}"))
        else:
            pagination_row.append(InlineKeyboardButton(text="·", callback_data="none"))
        
        pagination_row.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="none"))
        
        if current_page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"profit_page_{current_page + 1}"))
        else:
            pagination_row.append(InlineKeyboardButton(text="·", callback_data="none"))
        
        buttons.append(pagination_row)
    
    # Navigation
    buttons.append([
        InlineKeyboardButton(text="👤 К профилю", callback_data="profile"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_services_keyboard(services: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get services selection keyboard."""
    buttons = []
    
    for service in services:
        icon = service.get("icon", "🔹")
        buttons.append([
            InlineKeyboardButton(text=f"{icon} {service['name']}", callback_data=f"service_{service['id']}")
        ])
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_service_detail_keyboard(service_id: int, manual_link: str = None, bot_link: str = None) -> InlineKeyboardMarkup:
    """Get service detail keyboard with links."""
    buttons = []
    
    # Links in separate rows
    if manual_link and manual_link.strip():
        buttons.append([InlineKeyboardButton(text="📖 Мануал", url=manual_link.strip())])
    
    if bot_link and bot_link.strip():
        buttons.append([InlineKeyboardButton(text="🤖 Бот", url=bot_link.strip())])
    
    # Navigation
    buttons.append([
        InlineKeyboardButton(text="🛠 К сервисам", callback_data="services"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_resources_keyboard(resources: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get resources keyboard."""
    buttons = []
    
    for resource in resources:
        icon = "👥" if resource["type"] == "community" else "📚"
        buttons.append([
            InlineKeyboardButton(text=f"{icon} {resource['title']}", url=resource['content_link'])
        ])
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_menu_keyboard(section: str = None) -> InlineKeyboardMarkup:
    """Get back keyboard with optional section button."""
    buttons = []
    
    if section:
        section_map = {
            "profile": ("👤 К профилю", "profile"),
            "services": ("🛠 К сервисам", "services"),
            "mentors": ("👨‍🏫 К наставникам", "choose_mentor"),
            "community": ("📚 К материалам", "community"),
        }
        if section in section_map:
            text, callback = section_map[section]
            buttons.append([InlineKeyboardButton(text=text, callback_data=callback)])
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)




def get_mentor_services_keyboard(services: List[str]) -> InlineKeyboardMarkup:
    """Get mentor services selection keyboard."""
    buttons = []
    
    for service in services:
        buttons.append([
            InlineKeyboardButton(text=f"🛠 {service}", callback_data=f"mentor_service_{service[:30]}")
        ])
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_mentor_selection_keyboard(mentors: List[Dict[str, Any]], service_name: str) -> InlineKeyboardMarkup:
    """Get mentor selection keyboard for specific service."""
    buttons = []
    
    for mentor in mentors:
        name = mentor.get('full_name', 'Наставник')
        buttons.append([
            InlineKeyboardButton(text=f"👨‍🏫 {name}", callback_data=f"select_mentor_{mentor['id']}")
        ])
    
    buttons.append([
        InlineKeyboardButton(text="👨‍🏫 К наставникам", callback_data="choose_mentor"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_mentor_detail_keyboard(mentor_id: int, has_mentor: bool, service_name: str) -> InlineKeyboardMarkup:
    """Get mentor detail keyboard."""
    buttons = []
    
    if has_mentor:
        buttons.append([InlineKeyboardButton(text="❌ Отказаться от наставника", callback_data="remove_mentor")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Выбрать наставника", callback_data=f"confirm_mentor_{mentor_id}")])
    
    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data=f"mentor_service_{service_name[:30]}"),
        InlineKeyboardButton(text="👨‍🏫 Наставники", callback_data="choose_mentor")
    ])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_notifications_keyboard(has_unread: bool = False) -> InlineKeyboardMarkup:
    """Get notifications keyboard."""
    buttons = []
    
    if has_unread:
        buttons.append([InlineKeyboardButton(text="✅ Отметить все прочитанными", callback_data="mark_all_read")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_direct_payments_keyboard(support_username: str) -> InlineKeyboardMarkup:
    """Get direct payments keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Отправить скриншот", url=f"https://t.me/{support_username}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


def get_referral_keyboard(ref_link: str, website_url: str) -> InlineKeyboardMarkup:
    """Get referral link keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Мои рефералы", web_app=WebAppInfo(url=config.WEBAPP_REFERRALS))],
        [InlineKeyboardButton(text="📤 Поделиться", switch_inline_query=f"Присоединяйся к команде! {ref_link}")],
        [
            InlineKeyboardButton(text="👤 К профилю", callback_data="profile"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
        ]
    ])
