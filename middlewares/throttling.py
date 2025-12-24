"""Throttling middleware to prevent spam and rate limiting."""
import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    """Simple throttling to prevent spam."""
    
    def __init__(self, rate_limit: float = 0.5):
        self.rate_limit = rate_limit
        self.user_last_request: Dict[int, float] = {}
        # Cleanup old entries periodically
        self._cleanup_counter = 0
    
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
        
        user_id = user.id
        current_time = time.time()
        
        # Check rate limit
        last_request = self.user_last_request.get(user_id, 0)
        if current_time - last_request < self.rate_limit:
            # Too fast - ignore silently for messages, answer for callbacks
            if isinstance(event, CallbackQuery):
                await event.answer()
            return
        
        # Update last request time
        self.user_last_request[user_id] = current_time
        
        # Periodic cleanup (every 100 requests)
        self._cleanup_counter += 1
        if self._cleanup_counter >= 100:
            self._cleanup_counter = 0
            self._cleanup_old_entries(current_time)
        
        return await handler(event, data)
    
    def _cleanup_old_entries(self, current_time: float) -> None:
        """Remove entries older than 60 seconds."""
        cutoff = current_time - 60
        self.user_last_request = {
            uid: ts for uid, ts in self.user_last_request.items()
            if ts > cutoff
        }
