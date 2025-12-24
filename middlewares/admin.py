"""Admin middleware and decorator."""
from functools import wraps
from typing import Callable, Any
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS


def admin_only(handler: Callable) -> Callable:
    """Decorator to restrict handler to admin users only."""
    @wraps(handler)
    async def wrapper(event: Message | CallbackQuery, *args: Any, **kwargs: Any) -> Any:
        user_id = event.from_user.id
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Admin check: user_id={user_id}, ADMIN_IDS={ADMIN_IDS}, is_admin={user_id in ADMIN_IDS}")
        
        if user_id not in ADMIN_IDS:
            if isinstance(event, CallbackQuery):
                await event.answer("❌ Access denied\nThis command is for admins only.", show_alert=True)
            else:
                await event.answer("❌ <b>Access denied</b>\n\nThis command is for admins only.")
            return
        
        return await handler(event, *args, **kwargs)
    
    return wrapper
