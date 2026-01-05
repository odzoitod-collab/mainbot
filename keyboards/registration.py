"""Keyboards for registration flow."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_agreement_keyboard() -> InlineKeyboardMarkup:
    """Get agreement acceptance keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принимаю", callback_data="accept_agreement"),
            InlineKeyboardButton(text="❌ Отклоняю", callback_data="decline_agreement")
        ]
    ])


def get_age_keyboard() -> InlineKeyboardMarkup:
    """Get age selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👶 14-18 лет", callback_data="age_18_25"),
            InlineKeyboardButton(text="🔞 18-21 лет", callback_data="age_26_35")
        ],
        [
            InlineKeyboardButton(text="👨 21+ лет", callback_data="age_36_plus")
        ]
    ])


def get_experience_keyboard() -> InlineKeyboardMarkup:
    """Get experience confirmation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, есть опыт", callback_data="exp_yes"),
            InlineKeyboardButton(text="❌ Нет, новичок", callback_data="exp_no")
        ]
    ])


def get_work_hours_keyboard() -> InlineKeyboardMarkup:
    """Get work hours selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏰ 1-3 часа", callback_data="hours_1_3"),
            InlineKeyboardButton(text="⏰ 4-6 часов", callback_data="hours_4_6")
        ],
        [
            InlineKeyboardButton(text="⏰ 7+ часов", callback_data="hours_7_plus"),
            InlineKeyboardButton(text="⏰ Полный день", callback_data="hours_full")
        ]
    ])


def get_motivation_keyboard() -> InlineKeyboardMarkup:
    """Get motivation selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Заработок", callback_data="motivation_money")],
        [InlineKeyboardButton(text="📚 Опыт и обучение", callback_data="motivation_learning")],
        [InlineKeyboardButton(text="🚀 Карьерный рост", callback_data="motivation_career")],
        [InlineKeyboardButton(text="🎯 Новые знакомства", callback_data="motivation_network")]
    ])


def get_source_keyboard() -> InlineKeyboardMarkup:
    """Get source selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 Telegram канал", callback_data="source_telegram"),
            InlineKeyboardButton(text="👥 От друга", callback_data="source_friend")
        ],
        [
            InlineKeyboardButton(text="🌐 Интернет поиск", callback_data="source_internet"),
            InlineKeyboardButton(text="📢 Реклама", callback_data="source_ads")
        ],
        [InlineKeyboardButton(text="🔍 Другое", callback_data="source_other")]
    ])


def get_admin_decision_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Get admin decision keyboard for application review."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_{user_id}")
        ]
    ])


def get_join_team_keyboard() -> InlineKeyboardMarkup:
    """Get join team keyboard."""
    from config import CHAT_GROUP_URL
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Войти в команду", callback_data="join_team")],
        [InlineKeyboardButton(text="💬 Перейти в чат", url=CHAT_GROUP_URL)]
    ])
