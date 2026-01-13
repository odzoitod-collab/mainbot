"""Mentor panel keyboards."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any


def get_mentor_panel_keyboard() -> InlineKeyboardMarkup:
    """Get main mentor panel keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="mentor_stats"),
            InlineKeyboardButton(text="👥 Мои студенты", callback_data="mentor_students")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="mentor_broadcast"),
            InlineKeyboardButton(text="📺 Мой ТГК", callback_data="mentor_channel")
        ],
        [
            InlineKeyboardButton(text="📈 История рассылок", callback_data="mentor_broadcast_history"),
            InlineKeyboardButton(text="💰 Мои доходы", callback_data="mentor_earnings")
        ],
        [
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ])


def get_mentor_students_keyboard(page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Get mentor students keyboard with pagination."""
    buttons = []
    
    # Pagination
    if total_pages > 1:
        pagination_row = []
        
        if page > 0:
            pagination_row.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"mentor_students_page_{page - 1}"
            ))
        
        pagination_row.append(InlineKeyboardButton(
            text=f"Стр. {page + 1}/{total_pages}", 
            callback_data="none"
        ))
        
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"mentor_students_page_{page + 1}"
            ))
        
        buttons.append(pagination_row)
    
    # Navigation
    buttons.extend([
        [InlineKeyboardButton(text="📢 Рассылка студентам", callback_data="mentor_broadcast")],
        [InlineKeyboardButton(text="🔙 Панель наставника", callback_data="mentor_panel")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_mentor_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Get mentor broadcast keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Текстовая рассылка", callback_data="mentor_broadcast_text"),
            InlineKeyboardButton(text="🖼 С изображением", callback_data="mentor_broadcast_photo")
        ],
        [
            InlineKeyboardButton(text="📈 История рассылок", callback_data="mentor_broadcast_history")
        ],
        [
            InlineKeyboardButton(text="🔙 Панель наставника", callback_data="mentor_panel")
        ]
    ])


def get_mentor_channel_keyboard(has_channel: bool = False) -> InlineKeyboardMarkup:
    """Get mentor channel management keyboard."""
    buttons = []
    
    if has_channel:
        buttons.extend([
            [InlineKeyboardButton(text="✏️ Редактировать ТГК", callback_data="mentor_channel_edit")],
            [InlineKeyboardButton(text="📊 Статистика ТГК", callback_data="mentor_channel_stats")],
            [InlineKeyboardButton(text="🔗 Поделиться ссылкой", callback_data="mentor_channel_share")]
        ])
    else:
        buttons.append([InlineKeyboardButton(text="➕ Создать ТГК", callback_data="mentor_channel_create")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Панель наставника", callback_data="mentor_panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_mentor_broadcast_history_keyboard(page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Get mentor broadcast history keyboard."""
    buttons = []
    
    # Pagination
    if total_pages > 1:
        pagination_row = []
        
        if page > 0:
            pagination_row.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"mentor_broadcast_history_page_{page - 1}"
            ))
        
        pagination_row.append(InlineKeyboardButton(
            text=f"Стр. {page + 1}/{total_pages}", 
            callback_data="none"
        ))
        
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"mentor_broadcast_history_page_{page + 1}"
            ))
        
        buttons.append(pagination_row)
    
    # Navigation
    buttons.extend([
        [InlineKeyboardButton(text="📢 Новая рассылка", callback_data="mentor_broadcast")],
        [InlineKeyboardButton(text="🔙 Панель наставника", callback_data="mentor_panel")]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_detail_keyboard(broadcast_id: int) -> InlineKeyboardMarkup:
    """Get broadcast detail keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Получатели", callback_data=f"broadcast_recipients_{broadcast_id}")],
        [InlineKeyboardButton(text="🔙 История рассылок", callback_data="mentor_broadcast_history")]
    ])


def get_broadcast_recipients_keyboard(broadcast_id: int, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Get broadcast recipients keyboard."""
    buttons = []
    
    # Pagination
    if total_pages > 1:
        pagination_row = []
        
        if page > 0:
            pagination_row.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"broadcast_recipients_{broadcast_id}_page_{page - 1}"
            ))
        
        pagination_row.append(InlineKeyboardButton(
            text=f"Стр. {page + 1}/{total_pages}", 
            callback_data="none"
        ))
        
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"broadcast_recipients_{broadcast_id}_page_{page + 1}"
            ))
        
        buttons.append(pagination_row)
    
    # Navigation
    buttons.append([InlineKeyboardButton(text="🔙 К рассылке", callback_data=f"broadcast_detail_{broadcast_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_mentor_earnings_keyboard(page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Get mentor earnings keyboard."""
    buttons = []
    
    # Pagination
    if total_pages > 1:
        pagination_row = []
        
        if page > 0:
            pagination_row.append(InlineKeyboardButton(
                text="⬅️ Назад", 
                callback_data=f"mentor_earnings_page_{page - 1}"
            ))
        
        pagination_row.append(InlineKeyboardButton(
            text=f"Стр. {page + 1}/{total_pages}", 
            callback_data="none"
        ))
        
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(
                text="Вперед ➡️", 
                callback_data=f"mentor_earnings_page_{page + 1}"
            ))
        
        buttons.append(pagination_row)
    
    # Navigation
    buttons.append([InlineKeyboardButton(text="🔙 Панель наставника", callback_data="mentor_panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get broadcast confirmation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="mentor_broadcast_confirm"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="mentor_broadcast_cancel")
        ]
    ])


def get_channel_create_keyboard() -> InlineKeyboardMarkup:
    """Get channel creation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data="mentor_channel")]
    ])


def get_back_to_mentor_panel_keyboard() -> InlineKeyboardMarkup:
    """Get back to mentor panel keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Панель наставника", callback_data="mentor_panel")]
    ])