"""Mentor broadcast system."""
import logging
import asyncio
from typing import List, Dict, Any

from aiogram import Bot
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from database import (
    get_pending_broadcasts, get_broadcast_recipients, 
    update_broadcast_recipient_status, update_broadcast_status
)

logger = logging.getLogger(__name__)


class MentorBroadcastManager:
    """Manager for mentor broadcasts."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.is_running = False
    
    async def start_processing(self):
        """Start broadcast processing loop."""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Mentor broadcast manager started")
        
        while self.is_running:
            try:
                await self._process_pending_broadcasts()
                await asyncio.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in broadcast processing: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    def stop_processing(self):
        """Stop broadcast processing."""
        self.is_running = False
        logger.info("Mentor broadcast manager stopped")
    
    async def _process_pending_broadcasts(self):
        """Process pending broadcasts."""
        broadcasts = await get_pending_broadcasts()
        
        for broadcast in broadcasts:
            try:
                await self._process_broadcast(broadcast)
            except Exception as e:
                logger.error(f"Error processing broadcast {broadcast['id']}: {e}")
                await update_broadcast_status(broadcast['id'], 'failed')
    
    async def _process_broadcast(self, broadcast: Dict[str, Any]):
        """Process single broadcast."""
        broadcast_id = broadcast['id']
        message_text = broadcast['message_text']
        message_type = broadcast['message_type']
        media_file_id = broadcast.get('media_file_id')
        
        logger.info(f"Processing broadcast {broadcast_id}")
        
        # Update status to sending
        await update_broadcast_status(broadcast_id, 'sending')
        
        # Get recipients
        recipients = await get_broadcast_recipients(broadcast_id)
        sent_count = 0
        
        for recipient in recipients:
            if recipient['status'] != 'pending':
                continue
            
            student_id = recipient['student_id']
            
            try:
                # Send message based on type
                if message_type == 'photo' and media_file_id:
                    await self.bot.send_photo(
                        chat_id=student_id,
                        photo=media_file_id,
                        caption=message_text,
                        parse_mode='HTML'
                    )
                else:
                    await self.bot.send_message(
                        chat_id=student_id,
                        text=message_text,
                        parse_mode='HTML'
                    )
                
                # Mark as sent
                await update_broadcast_recipient_status(broadcast_id, student_id, 'sent')
                sent_count += 1
                
                # Small delay to avoid rate limits
                await asyncio.sleep(0.1)
                
            except TelegramForbiddenError:
                # User blocked the bot
                await update_broadcast_recipient_status(
                    broadcast_id, student_id, 'failed', 'Пользователь заблокировал бота'
                )
                logger.warning(f"User {student_id} blocked the bot")
                
            except TelegramBadRequest as e:
                # Invalid user or other error
                await update_broadcast_recipient_status(
                    broadcast_id, student_id, 'failed', str(e)
                )
                logger.warning(f"Failed to send to {student_id}: {e}")
                
            except Exception as e:
                # Other errors
                await update_broadcast_recipient_status(
                    broadcast_id, student_id, 'failed', str(e)
                )
                logger.error(f"Unexpected error sending to {student_id}: {e}")
        
        # Update final status
        await update_broadcast_status(broadcast_id, 'completed', sent_count)
        logger.info(f"Broadcast {broadcast_id} completed: {sent_count} sent")


# Global broadcast manager instance
broadcast_manager: MentorBroadcastManager = None


def init_broadcast_manager(bot: Bot):
    """Initialize broadcast manager."""
    global broadcast_manager
    broadcast_manager = MentorBroadcastManager(bot)


async def start_broadcast_manager():
    """Start broadcast manager."""
    if broadcast_manager:
        await broadcast_manager.start_processing()


def stop_broadcast_manager():
    """Stop broadcast manager."""
    if broadcast_manager:
        broadcast_manager.stop_processing()