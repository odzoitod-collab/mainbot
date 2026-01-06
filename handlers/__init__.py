"""Handlers package."""
from handlers.registration import router as registration_router
from handlers.user_menu import router as user_menu_router
from handlers.chat_commands import router as chat_commands_router
from handlers.admin_profit import router as admin_profit_router
from handlers.admin_manage import router as admin_manage_router
from handlers.admin_mentors import router as admin_mentors_router
from handlers.admin_broadcast import router as admin_broadcast_router
from handlers.admin_close import router as admin_close_router
from handlers.admin_direct_payments import router as admin_direct_payments_router
from handlers.community_create import router as community_create_router
from handlers.admin_communities import router as admin_communities_router

__all__ = [
    "registration_router",
    "user_menu_router", 
    "chat_commands_router",
    "admin_profit_router",
    "admin_manage_router",
    "admin_mentors_router",
    "admin_broadcast_router",
    "admin_close_router",
    "admin_direct_payments_router",
    "community_create_router",
    "admin_communities_router",
]
