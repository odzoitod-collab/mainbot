"""Optimized message utilities for sending messages with brand image."""
import logging
import asyncio
from typing import Optional, Union, Dict
from contextlib import suppress

from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

from config import BRAND_IMAGE_HOME

logger = logging.getLogger(__name__)

# Global cache for uploaded file IDs (persists across requests)
_image_cache: Dict[str, str] = {}


async def send_with_brand(
    target: Union[Message, CallbackQuery],
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = "HTML",
    image_path: Optional[str] = None
) -> Optional[Message]:
    """Send message with brand image (optimized with file_id caching)."""
    try:
        if isinstance(target, CallbackQuery):
            bot = target.bot
            chat_id = target.message.chat.id
        else:
            bot = target.bot
            chat_id = target.chat.id
        
        img_path = image_path or BRAND_IMAGE_HOME
        
        # Use cached file_id if available (much faster)
        if img_path in _image_cache:
            return await bot.send_photo(
                chat_id=chat_id,
                photo=_image_cache[img_path],
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        
        # First time - upload and cache
        photo = FSInputFile(img_path)
        sent = await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        
        if sent.photo:
            _image_cache[img_path] = sent.photo[-1].file_id
        
        return sent
        
    except Exception as e:
        logger.error(f"send_with_brand failed: {e}")
        # Fallback to text
        with suppress(Exception):
            if isinstance(target, CallbackQuery):
                return await target.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
            return await target.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        return None


async def edit_with_brand(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = "HTML",
    image_path: Optional[str] = None
) -> bool:
    """Edit message caption or replace with new image (optimized)."""
    try:
        msg = callback.message
        
        # If message has photo and we want same/no image - just edit caption
        if msg.photo and not image_path:
            try:
                await msg.edit_caption(
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
                return True
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    return True
                raise
        
        # Need to change image or add image - delete and send new
        with suppress(Exception):
            await msg.delete()
        
        await send_with_brand(callback, text, reply_markup, parse_mode, image_path)
        return True
        
    except Exception as e:
        logger.error(f"edit_with_brand failed: {e}")
        # Last resort fallback
        with suppress(Exception):
            await callback.message.delete()
            await send_with_brand(callback, text, reply_markup, parse_mode, image_path)
            return True
        return False


async def answer_with_brand(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = "HTML",
    image_path: Optional[str] = None
) -> Optional[Message]:
    """Answer to message with brand image."""
    return await send_with_brand(message, text, reply_markup, parse_mode, image_path)


def get_cached_file_id(image_path: str) -> Optional[str]:
    """Get cached file_id for image path."""
    return _image_cache.get(image_path)


def set_cached_file_id(image_path: str, file_id: str) -> None:
    """Manually set cached file_id."""
    _image_cache[image_path] = file_id
