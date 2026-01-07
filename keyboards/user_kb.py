"""User keyboards for main menu and navigation."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict, Any

import config


def get_main_static_keyboard() -> ReplyKeyboardMarkup:
    """Get main static keyboard with quick access button."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        persistent=True
    )


def get_main_menu_keyboard(unread_notifications: int = 0, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Get main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="📊 Аналитика", web_app=WebAppInfo(url=config.WEBAPP_ANALYTICS))
        ],
        [
            InlineKeyboardButton(text="🛠 Сервисы", callback_data="services"),
            InlineKeyboardButton(text="👨‍🏫 Наставники", callback_data="choose_mentor")
        ],
        [
            InlineKeyboardButton(text="💳 Прямики", callback_data="direct_payments"),
            InlineKeyboardButton(text="🔗 Рефералы", callback_data="referral_link")
        ],
        [
            InlineKeyboardButton(text="👥 Комьюнити", callback_data="community"),
            InlineKeyboardButton(text="💭 Чат", url=config.CHAT_GROUP_URL)
        ],
        [
            InlineKeyboardButton(text="🌐 Хаб", web_app=WebAppInfo(url=config.WEBAPP_HUB)),
            InlineKeyboardButton(text="💡 Идеи", web_app=WebAppInfo(url=config.WEBAPP_IDEAS))
        ]
    ]

    if is_admin:
        keyboard.append([InlineKeyboardButton(text="🛡 Админ меню", callback_data="admin_menu")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Get profile inline keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 История профитов", web_app=WebAppInfo(url=config.WEBAPP_PROFITS_HISTORY))],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


def get_profit_history_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Get profit history keyboard with pagination."""
    buttons = []
    
    # Pagination row
    if total_pages > 1:
        pagination_row = []
        
        if current_page > 0:
            pagination_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"profit_page_{current_page - 1}"))
        
        pagination_row.append(InlineKeyboardButton(text=f"Стр. {current_page + 1}/{total_pages}", callback_data="none"))
        
        if current_page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"profit_page_{current_page + 1}"))
        
        buttons.append(pagination_row)
    
    # Navigation
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_services_keyboard(services: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get services selection keyboard."""
    buttons = []
    
    # Группируем сервисы по 2 в ряд для компактности
    for i in range(0, len(services), 2):
        row = []
        for j in range(2):
            if i + j < len(services):
                service = services[i + j]
                icon = service.get("icon", "🔹")
                row.append(InlineKeyboardButton(
                    text=f"{icon} {service['name']}", 
                    callback_data=f"service_{service['id']}"
                ))
        buttons.append(row)
    
    # Простая навигация
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_service_detail_keyboard(service_id: int, manual_link: str = None, bot_link: str = None) -> InlineKeyboardMarkup:
    """Get service detail keyboard with links."""
    buttons = []
    
    # Ссылки в одном ряду если обе есть
    links_row = []
    if manual_link and manual_link.strip():
        links_row.append(InlineKeyboardButton(text="📖 Открыть мануал", url=manual_link.strip()))
    
    if bot_link and bot_link.strip():
        links_row.append(InlineKeyboardButton(text="🤖 Перейти к боту", url=bot_link.strip()))
    
    if links_row:
        if len(links_row) == 2:
            buttons.append(links_row)
        else:
            buttons.append([links_row[0]])
    
    # Простая навигация
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_resources_keyboard(resources: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get resources keyboard."""
    buttons = []
    
    for resource in resources:
        icon = "👥" if resource["type"] == "community" else "📚"
        buttons.append([
            InlineKeyboardButton(text=f"{icon} {resource['title']}", url=resource['content_link'])
        ])
    
    # Простая навигация
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_menu_keyboard(section: str = None) -> InlineKeyboardMarkup:
    """Get back keyboard - always leads to main menu for simplicity."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])




def get_mentor_services_keyboard(services: List[str]) -> InlineKeyboardMarkup:
    """Get mentor services selection keyboard."""
    buttons = []
    
    # Группируем сервисы по 1 в ряд для ясности
    for service in services:
        buttons.append([InlineKeyboardButton(
            text=f"🛠 {service}", 
            callback_data=f"mentor_service_{service[:30]}"
        )])
    
    # Простая навигация
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
    
    # Простая навигация
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_mentor_detail_keyboard(mentor_id: int, has_mentor: bool, service_name: str) -> InlineKeyboardMarkup:
    """Get mentor detail keyboard."""
    buttons = []
    
    if has_mentor:
        buttons.append([InlineKeyboardButton(text="❌ Отказаться от наставника", callback_data="remove_mentor")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Выбрать наставника", callback_data=f"confirm_mentor_{mentor_id}")])
    
    # Простая навигация
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
        [InlineKeyboardButton(text="📤 Поделиться ссылкой", switch_inline_query=f"Присоединяйся к команде! {ref_link}")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


def get_communities_keyboard(communities: List[Dict[str, Any]], user_profit: float) -> InlineKeyboardMarkup:
    """Get communities list keyboard."""
    buttons = []
    
    # Communities list
    for community in communities:
        status_icon = "✅" if community.get("is_member") else "👥"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} {community['name']} ({community['members_count']})",
                callback_data=f"community_view_{community['id']}"
            )
        ])
    
    # Create community button (if user has enough profit)
    if user_profit >= 50000:
        buttons.append([InlineKeyboardButton(text="➕ Создать комьюнити", callback_data="community_create")])
    
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_community_detail_keyboard(community_id: int, is_member: bool, is_creator: bool = False) -> InlineKeyboardMarkup:
    """Get community detail keyboard."""
    buttons = []
    
    if is_member:
        buttons.append([InlineKeyboardButton(text="❌ Покинуть", callback_data=f"community_leave_{community_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Присоединиться", callback_data=f"community_join_{community_id}")])
    
    buttons.append([
        InlineKeyboardButton(text="🔙 К списку", callback_data="community"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_community_create_keyboard() -> InlineKeyboardMarkup:
    """Get community creation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К списку", callback_data="community")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])
