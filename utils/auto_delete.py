"""Auto-delete messages utility."""
import asyncio
import logging
from typing import Union, Optional
from functools import wraps
from aiogram import Bot
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


def is_group_chat(message: Message) -> bool:
    """Check if message is from a group chat."""
    return message.chat.type in ['group', 'supergroup']


async def delete_messages_after_delay(
    bot: Bot,
    chat_id: int,
    message_ids: list,
    delay: int = 10
):
    """Delete messages after delay."""
    try:
        await asyncio.sleep(delay)
        
        for message_id in message_ids:
            try:
                await bot.delete_message(chat_id, message_id)
                logger.debug(f"Deleted message {message_id} in chat {chat_id}")
            except TelegramBadRequest as e:
                if "message to delete not found" not in str(e).lower():
                    logger.warning(f"Failed to delete message {message_id}: {e}")
    except Exception as e:
        logger.error(f"Error in delete_messages_after_delay: {e}")


async def reply_with_auto_delete(
    message: Message,
    text: str,
    delay: int = 10,
    delete_original: bool = True,
    **kwargs
) -> Message:
    """
    Reply to message with auto-deletion in group chats.
    
    Args:
        message: Original message
        text: Reply text
        delay: Auto-delete delay (only in groups)
        delete_original: Delete original message too
        **kwargs: Additional arguments for reply
    
    Returns:
        Sent message
    """
    # Send reply
    sent_message = await message.reply(text, **kwargs)
    
    # Schedule auto-deletion only in group chats
    if is_group_chat(message):
        messages_to_delete = [sent_message.message_id]
        if delete_original:
            messages_to_delete.append(message.message_id)
        
        asyncio.create_task(
            delete_messages_after_delay(
                message.bot,
                message.chat.id,
                messages_to_delete,
                delay
            )
        )
    
    return sent_message


async def reply_photo_with_auto_delete(
    message: Message,
    photo,
    caption: str = None,
    delay: int = 10,
    delete_original: bool = True,
    **kwargs
) -> Message:
    """
    Reply with photo and auto-deletion in group chats.
    
    Args:
        message: Original message
        photo: Photo to send
        caption: Photo caption
        delay: Auto-delete delay (only in groups)
        delete_original: Delete original message too
        **kwargs: Additional arguments for reply_photo
    
    Returns:
        Sent message
    """
    # Send photo reply
    sent_message = await message.reply_photo(photo, caption=caption, **kwargs)
    
    # Schedule auto-deletion only in group chats
    if is_group_chat(message):
        messages_to_delete = [sent_message.message_id]
        if delete_original:
            messages_to_delete.append(message.message_id)
        
        asyncio.create_task(
            delete_messages_after_delay(
                message.bot,
                message.chat.id,
                messages_to_delete,
                delay
            )
        )
    
    return sent_message