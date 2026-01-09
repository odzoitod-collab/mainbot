"""Middleware to remove reply keyboard in group chats."""
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.enums import ChatType

logger = logging.getLogger(__name__)

# Track chats where keyboard was already removed (to avoid spam)
_processed_chats: set = set()


class GroupKeyboardRemoveMiddleware(BaseMiddleware):
    """Remove reply keyboard in group/supergroup chats on first message."""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Only for group/supergroup chats
        if event.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
            chat_id = event.chat.id
            
            # Remove keyboard once per chat (first interaction)
            if chat_id not in _processed_chats:
                _processed_chats.add(chat_id)
                try:
                    # Send invisible message with keyboard removal
                    msg = await event.answer("⠀", reply_markup=ReplyKeyboardRemove())
                    # Delete the message immediately
                    await msg.delete()
                except Exception as e:
                    logger.debug(f"Could not remove keyboard in chat {chat_id}: {e}")
        
        return await handler(event, data)
