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
    """Edit message - keep the same photo, just change caption and keyboard."""
    try:
        msg = callback.message
        
        # If message has photo - edit caption
        if msg.photo:
            await msg.edit_caption(
                caption=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        
        # If message has text only - edit text
        if msg.text:
            await msg.edit_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return True
        
        # Fallback - delete and send new (shouldn't happen normally)
        logger.warning(f"Message has no photo or text, falling back to delete+send")
        with suppress(Exception):
            await msg.delete()
        await send_with_brand(callback, text, reply_markup, parse_mode, image_path)
        return True
        
    except TelegramBadRequest as e:
        # If edit fails (e.g., message is too old or content is the same)
        logger.warning(f"edit_with_brand TelegramBadRequest: {e}")
        
        # Try to delete and send new as fallback
        try:
            with suppress(Exception):
                await callback.message.delete()
            await send_with_brand(callback, text, reply_markup, parse_mode, image_path)
            return True
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            return False
        
    except Exception as e:
        logger.error(f"edit_with_brand failed: {e}")
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
    # Set static keyboard only in private chats (not in groups)
    if static_keyboard and message.chat.type == "private":
        try:
            await message.answer("📱", reply_markup=static_keyboard, parse_mode="HTML")
            # Try to delete the phone message
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
