"""Middleware to check user status with caching."""
import logging
import time
from typing import Callable, Dict, Any, Awaitable, Optional, Tuple
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from database import get_user

logger = logging.getLogger(__name__)

# Registration callbacks that should bypass user check
REGISTRATION_CALLBACKS = frozenset({
    "accept_agreement", "decline_agreement", "exp_yes", "exp_no", "join_team",
    "age_18_25", "age_26_35", "age_36_plus",
    "hours_1_3", "hours_4_6", "hours_7_plus", "hours_full",
    "motivation_money", "motivation_learning", "motivation_career", "motivation_network",
    "source_telegram", "source_friend", "source_internet", "source_ads", "source_other"
})

REGISTRATION_PREFIXES = ("approve_", "decline_")


class UserCheckMiddleware(BaseMiddleware):
    """Check if user is active before processing with local caching."""
    
    def __init__(self):
        # Local cache: user_id -> (user_data, timestamp)
        self._cache: Dict[int, Tuple[Optional[dict], float]] = {}
        self._cache_ttl = 30  # 30 seconds cache
        self._cleanup_counter = 0
    
    def _get_cached_user(self, user_id: int) -> Optional[dict]:
        """Get user from local cache if not expired."""
        if user_id in self._cache:
            user_data, timestamp = self._cache[user_id]
            if time.time() - timestamp < self._cache_ttl:
                return user_data
            del self._cache[user_id]
        return None
    
    def _set_cached_user(self, user_id: int, user_data: Optional[dict]) -> None:
        """Set user in local cache."""
        self._cache[user_id] = (user_data, time.time())
    
    def _cleanup_cache(self) -> None:
        """Remove expired cache entries."""
        current_time = time.time()
        self._cache = {
            uid: (data, ts) for uid, (data, ts) in self._cache.items()
            if current_time - ts < self._cache_ttl
        }
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        
        if not user:
            return await handler(event, data)
        
        # Periodic cache cleanup
        self._cleanup_counter += 1
        if self._cleanup_counter >= 50:
            self._cleanup_counter = 0
            self._cleanup_cache()
        
        # Allow /start - always fetch fresh
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            db_user = await get_user(user.id)
            self._set_cached_user(user.id, db_user)
            data["db_user"] = db_user
            return await handler(event, data)
        
        # Allow registration callbacks
        if isinstance(event, CallbackQuery):
            if event.data in REGISTRATION_CALLBACKS:
                return await handler(event, data)
            if any(event.data.startswith(p) for p in REGISTRATION_PREFIXES):
                return await handler(event, data)
        
        # Try cache first, then database
        db_user = self._get_cached_user(user.id)
        if db_user is None:
            db_user = await get_user(user.id)
            self._set_cached_user(user.id, db_user)
        
        if not db_user:
            if isinstance(event, Message):
                await event.answer("❌ Используйте /start")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ /start", show_alert=True)
            return
        
        if db_user["status"] == "pending":
            if isinstance(event, Message):
                await event.answer("⏳ Анкета на рассмотрении")
            elif isinstance(event, CallbackQuery):
                await event.answer("⏳ Ждите одобрения", show_alert=True)
            return
        
        if db_user["status"] == "banned":
            if isinstance(event, Message):
                await event.answer("🚫 Доступ запрещен")
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫 Запрещено", show_alert=True)
            return
        
        # Pass user to handler
        data["db_user"] = db_user
        return await handler(event, data)
    
    def invalidate_user(self, user_id: int) -> None:
        """Invalidate user cache (call after status change)."""
        self._cache.pop(user_id, None)
