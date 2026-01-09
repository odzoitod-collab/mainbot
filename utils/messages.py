"""Optimized message utilities - always show brand image."""
import asyncio
import logging
from typing import Optional, Union, Dict
from contextlib import suppress

from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest

from config import BRAND_IMAGE_LOGO

logger = logging.getLogger(__name__)

# Global cache for uploaded file IDs
_image_cache: Dict[str, str] = {}


async def send_with_brand(
    target: Union[Message, CallbackQuery],
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = "HTML",
    image_path: Optional[str] = None
) -> Optional[Message]:
    """Send message with brand image."""
    try:
        if isinstance(target, CallbackQuery):
            bot = target.bot
            chat_id = target.message.chat.id
        else:
            bot = target.bot
            chat_id = target.chat.id
        
        img_path = image_path or BRAND_IMAGE_LOGO
        
        # Use cached file_id if available (faster)
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
        
        if sent and sent.photo:
            _image_cache[img_path] = sent.photo[-1].file_id
        
        return sent
        
    except Exception as e:
        logger.error(f"send_with_brand failed: {e}")
        # Fallback to text only
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
    """Edit message - always use correct image for the section."""
    try:
        msg = callback.message
        img_path = image_path or BRAND_IMAGE_LOGO
        
        # Always delete old message and send new with correct image
        # This ensures the right image is always shown
        with suppress(Exception):
            await msg.delete()
        
        await send_with_brand(callback, text, reply_markup, parse_mode, img_path)
        return True
        
    except Exception as e:
        logger.error(f"edit_with_brand failed: {e}")
        # Last resort - try to send new message
        with suppress(Exception):
            await callback.message.delete()
        with suppress(Exception):
            await send_with_brand(callback, text, reply_markup, parse_mode, img_path)
        return False


async def answer_with_brand(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: str = "HTML",
    image_path: Optional[str] = None,
    static_keyboard = None
) -> Optional[Message]:
    """Answer with brand image and optional static keyboard."""
    # Set static keyboard if provided (silently)
    if static_keyboard:
        try:
            await message.answer(".", reply_markup=static_keyboard, parse_mode="HTML")
            # Try to delete the dot message
            await asyncio.sleep(0.1)
        except:
            pass
    
    return await send_with_brand(message, text, reply_markup, parse_mode, image_path)


def get_cached_file_id(image_path: str) -> Optional[str]:
    """Get cached file_id."""
    return _image_cache.get(image_path)


def set_cached_file_id(image_path: str, file_id: str) -> None:
    """Set cached file_id."""
    _image_cache[image_path] = file_id
