"""Improved admin keyboards with better UX."""
from typing import List, Dict, Any, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Get admin menu keyboard with organized sections."""
    return InlineKeyboardMarkup(inline_keyboard=[
        # Main actions
        [InlineKeyboardButton(text="💰 Создать профит", callback_data="create_profit")],
        # Payouts section
        [
            InlineKeyboardButton(text="💸 Выплаты", callback_data="view_payouts"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        ],
        # Management section
        [
            InlineKeyboardButton(text="🛠 Контент", callback_data="manage_content"),
            InlineKeyboardButton(text="👨‍🏫 Наставники", callback_data="manage_mentors")
        ],
        [
            InlineKeyboardButton(text="👥 Комьюнити", callback_data="manage_communities"),
            InlineKeyboardButton(text="👤 Пользователи", callback_data="manage_users")
        ],
        # Settings section
        [InlineKeyboardButton(text="💳 Прямики", callback_data="manage_direct_payments")],
        # Communication
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="broadcast")],
        # Navigation
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


def get_stage_keyboard() -> InlineKeyboardMarkup:
    """Get stage selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💳 Депозит", callback_data="stage_deposit"),
            InlineKeyboardButton(text="📋 Налог", callback_data="stage_tax")
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_profit_creation")]
    ])


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_profit"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_profit")
        ]
    ])


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    """Get back to admin menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Админ меню", callback_data="admin_menu")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])


def get_cancel_keyboard(callback_data: str = "admin_menu") -> InlineKeyboardMarkup:
    """Get cancel keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=callback_data)]
    ])


def get_service_selection_keyboard(services: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get service selection keyboard for profit creation."""
    buttons = []
    
    for i in range(0, len(services), 2):
        row = []
        for j in range(i, min(i + 2, len(services))):
            service = services[j]
            icon = service.get("icon", "🔹")
            row.append(InlineKeyboardButton(
                text=f"{icon} {service['name']}",
                callback_data=f"select_service_{service['id']}"
            ))
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_profit_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================
# PAYOUTS
# ============================================

def get_payout_type_keyboard() -> InlineKeyboardMarkup:
    """Get payout type selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Воркеры", callback_data="payouts_workers")],
        [InlineKeyboardButton(text="🔗 Рефералы", callback_data="payouts_referrals")],
        [InlineKeyboardButton(text="👨‍🏫 Наставники", callback_data="payouts_mentors")],
        [InlineKeyboardButton(text="✅ Выплатить всем", callback_data="payout_all")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])


def get_payout_keyboard(summary: List[Dict[str, Any]], payout_type: str = "payout") -> InlineKeyboardMarkup:
    """Get payout keyboard with user list."""
    buttons = []
    
    for item in summary[:15]:  # Limit to 15 items
        username = f"@{item['username']}" if item.get('username') else item.get('full_name', 'User')
        amount = item.get('total_unpaid', 0)
        buttons.append([InlineKeyboardButton(
            text=f"✅ {username} • {amount:.0f} ₽",
            callback_data=f"{payout_type}_{item['user_id']}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="view_payouts")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_referral_payout_keyboard(summary: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get referral payout keyboard."""
    return get_payout_keyboard(summary, "refpayout")


def get_mentor_payout_keyboard(summary: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get mentor payout keyboard."""
    return get_payout_keyboard(summary, "mentorpayout")


# ============================================
# CONTENT MANAGEMENT
# ============================================

def get_content_category_keyboard() -> InlineKeyboardMarkup:
    """Get content category selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛠 Сервисы", callback_data="manage_services"),
            InlineKeyboardButton(text="📚 Ресурсы", callback_data="manage_resources")
        ],
        [InlineKeyboardButton(text="🔙 Админ меню", callback_data="admin_menu")]
    ])


def get_content_action_keyboard(category: str = "services") -> InlineKeyboardMarkup:
    """Get content action keyboard."""
    back_callback = "manage_content"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="content_add"),
            InlineKeyboardButton(text="📋 Список", callback_data="content_list")
        ],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data="content_delete")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=back_callback)]
    ])


def get_service_list_keyboard(services: List[Dict[str, Any]], for_delete: bool = True) -> InlineKeyboardMarkup:
    """Get service list keyboard."""
    buttons = []
    
    for service in services:
        icon = service.get("icon", "🔹")
        prefix = "🗑 " if for_delete else ""
        callback = f"delete_service_{service['id']}" if for_delete else f"view_service_{service['id']}"
        buttons.append([InlineKeyboardButton(
            text=f"{prefix}{icon} {service['name']}",
            callback_data=callback
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="manage_services")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_resource_list_keyboard(resources: List[Dict[str, Any]], for_delete: bool = True) -> InlineKeyboardMarkup:
    """Get resource list keyboard."""
    buttons = []
    
    for resource in resources:
        type_icon = "👥" if resource["type"] == "community" else "📚"
        prefix = "🗑 " if for_delete else ""
        callback = f"delete_resource_{resource['id']}" if for_delete else f"view_resource_{resource['id']}"
        title = resource['title'][:25] + "..." if len(resource['title']) > 25 else resource['title']
        buttons.append([InlineKeyboardButton(
            text=f"{prefix}{type_icon} {title}",
            callback_data=callback
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="manage_resources")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_resource_type_keyboard() -> InlineKeyboardMarkup:
    """Get resource type selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Чат/Канал", callback_data="resource_type_community"),
            InlineKeyboardButton(text="📚 Материал", callback_data="resource_type_resource")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="manage_resources")]
    ])


# ============================================
# MENTORS
# ============================================

def get_mentor_list_keyboard(mentors: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get mentor list keyboard."""
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить наставника", callback_data="add_mentor")]
    ]
    
    if mentors:
        buttons.append([InlineKeyboardButton(text="━━━ НАСТАВНИКИ ━━━", callback_data="none")])
        for mentor in mentors[:10]:
            username = f"@{mentor['username']}" if mentor.get('username') else mentor.get('full_name', 'N/A')
            service = mentor.get('service_name', 'N/A')[:15]
            percent = mentor.get('percent', 0)
            buttons.append([InlineKeyboardButton(
                text=f"🗑 {username} • {service} • {percent}%",
                callback_data=f"delete_mentor_{mentor['id']}"
            )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Админ меню", callback_data="admin_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_mentor_service_keyboard(services: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get service selection for mentor."""
    buttons = []
    for service in services:
        icon = service.get("icon", "🔹")
        buttons.append([InlineKeyboardButton(
            text=f"{icon} {service['name']}",
            callback_data=f"mentor_select_service_{service['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="manage_mentors")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================
# BROADCAST
# ============================================

def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get broadcast confirmation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_broadcast")
        ]
    ])


def get_broadcast_type_keyboard() -> InlineKeyboardMarkup:
    """Get broadcast type selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Текст", callback_data="broadcast_text")],
        [InlineKeyboardButton(text="🖼 Фото + текст", callback_data="broadcast_photo")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])


# ============================================
# USERS MANAGEMENT
# ============================================

def get_users_management_keyboard() -> InlineKeyboardMarkup:
    """Get users management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="find_user")],
        [InlineKeyboardButton(text="📋 Активные", callback_data="list_active_users")],
        [InlineKeyboardButton(text="⏳ Ожидающие", callback_data="list_pending_users")],
        [InlineKeyboardButton(text="🚫 Заблокированные", callback_data="list_banned_users")],
        [InlineKeyboardButton(text="🔙 Админ меню", callback_data="admin_menu")]
    ])


def get_user_action_keyboard(user_id: int, status: str) -> InlineKeyboardMarkup:
    """Get user action keyboard."""
    buttons = []
    
    if status == "pending":
        buttons.append([
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_{user_id}")
        ])
    elif status == "active":
        buttons.append([InlineKeyboardButton(text="🚫 Заблокировать", callback_data=f"ban_user_{user_id}")])
    elif status == "banned":
        buttons.append([InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"unban_user_{user_id}")])
    
    buttons.append([InlineKeyboardButton(text="💰 Профиты", callback_data=f"user_profits_{user_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="manage_users")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_list_keyboard(users: List[Dict[str, Any]], page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
    """Get paginated user list keyboard."""
    buttons = []
    total_pages = max(1, (len(users) + per_page - 1) // per_page)
    start = page * per_page
    page_users = users[start:start + per_page]
    
    for user in page_users:
        username = f"@{user['username']}" if user.get('username') else user.get('full_name', 'N/A')
        status_icon = "🟢" if user['status'] == 'active' else "⏳" if user['status'] == 'pending' else "🔴"
        buttons.append([InlineKeyboardButton(
            text=f"{status_icon} {username}",
            callback_data=f"view_user_{user['id']}"
        )])
    
    # Pagination
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"users_page_{page-1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="none"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"users_page_{page+1}"))
        buttons.append(nav_row)
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="manage_users")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================
# STATISTICS
# ============================================

def get_stats_keyboard() -> InlineKeyboardMarkup:
    """Get statistics keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="stats_today"),
            InlineKeyboardButton(text="📆 Неделя", callback_data="stats_week")
        ],
        [
            InlineKeyboardButton(text="📊 Месяц", callback_data="stats_month"),
            InlineKeyboardButton(text="📈 Всё время", callback_data="stats_all")
        ],
        [InlineKeyboardButton(text="🏆 Топ воркеров", callback_data="stats_top")],
        [InlineKeyboardButton(text="🔙 Админ меню", callback_data="admin_menu")]
    ])


# ============================================
# DIRECT PAYMENTS
# ============================================

def get_direct_payments_admin_keyboard() -> InlineKeyboardMarkup:
    """Get direct payments admin keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить реквизиты", callback_data="edit_requisites")],
        [InlineKeyboardButton(text="📝 Изменить инфо", callback_data="edit_dp_info")],
        [InlineKeyboardButton(text="👤 Изменить поддержку", callback_data="edit_support")],
        [InlineKeyboardButton(text="🔙 Админ меню", callback_data="admin_menu")]
    ])


# ============================================
# COMMUNITIES MANAGEMENT
# ============================================

def get_communities_admin_keyboard() -> InlineKeyboardMarkup:
    """Get communities admin management keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Заявки на модерацию", callback_data="pending_communities")],
        [InlineKeyboardButton(text="📋 Все комьюнити", callback_data="all_communities")],
        [InlineKeyboardButton(text="🔙 Админ меню", callback_data="admin_menu")]
    ])


def get_pending_communities_keyboard(communities: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get pending communities keyboard."""
    buttons = []
    
    for community in communities:
        creator_name = community.get('creator_name', 'Неизвестный')
        name = community['name'][:20] + "..." if len(community['name']) > 20 else community['name']
        buttons.append([InlineKeyboardButton(
            text=f"📝 {name} • {creator_name}",
            callback_data=f"review_community_{community['id']}"
        )])
    
    if not communities:
        buttons.append([InlineKeyboardButton(text="✅ Нет заявок", callback_data="none")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="manage_communities")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_community_review_keyboard(community_id: int) -> InlineKeyboardMarkup:
    """Get community review keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_community_{community_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_community_{community_id}")
        ],
        [InlineKeyboardButton(text="🔙 К заявкам", callback_data="pending_communities")]
    ])


def get_all_communities_keyboard(communities: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Get all communities admin keyboard."""
    buttons = []
    
    for community in communities:
        name = community['name'][:25] + "..." if len(community['name']) > 25 else community['name']
        members = community.get('members_count', 0)
        buttons.append([InlineKeyboardButton(
            text=f"🗑 {name} ({members} чел.)",
            callback_data=f"delete_community_{community['id']}"
        )])
    
    if not communities:
        buttons.append([InlineKeyboardButton(text="📭 Нет комьюнити", callback_data="none")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="manage_communities")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
