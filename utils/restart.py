"""Utilities for bot restart functionality."""
import os
import sys
import logging
import asyncio
import subprocess
from typing import Optional
from pathlib import Path

import config

logger = logging.getLogger(__name__)


async def create_restart_flag(user_id: int, reason: str = "admin_request") -> bool:
    """Create restart flag file."""
    try:
        flag_data = f"restart_requested_by_{user_id}_{reason}"
        
        with open(config.RESTART_FLAG_FILE, "w") as f:
            f.write(flag_data)
        
        logger.info(f"Restart flag created by user {user_id}: {reason}")
        return True
    except Exception as e:
        logger.error(f"Failed to create restart flag: {e}")
        return False


async def check_restart_flag() -> Optional[str]:
    """Check if restart flag exists and return its content."""
    try:
        if os.path.exists(config.RESTART_FLAG_FILE):
            with open(config.RESTART_FLAG_FILE, "r") as f:
                content = f.read().strip()
            return content
        return None
    except Exception as e:
        logger.error(f"Failed to check restart flag: {e}")
        return None


async def remove_restart_flag() -> bool:
    """Remove restart flag file."""
    try:
        if os.path.exists(config.RESTART_FLAG_FILE):
            os.remove(config.RESTART_FLAG_FILE)
            logger.info("Restart flag removed")
        return True
    except Exception as e:
        logger.error(f"Failed to remove restart flag: {e}")
        return False


async def restart_bot_process() -> bool:
    """Restart bot process using different methods."""
    try:
        # Method 1: If webhook URL is configured
        if config.RESTART_WEBHOOK_URL:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(config.RESTART_WEBHOOK_URL) as response:
                    if response.status == 200:
                        logger.info("Restart webhook called successfully")
                        return True
        
        # Method 2: If restart command is configured
        if config.RESTART_COMMAND:
            subprocess.Popen(config.RESTART_COMMAND, shell=True)
            logger.info(f"Restart command executed: {config.RESTART_COMMAND}")
            return True
        
        # Method 3: Create flag and exit (for supervisor/systemd)
        logger.info("Creating restart flag and exiting...")
        await asyncio.sleep(1)  # Give time for response
        sys.exit(1)  # Exit with error code to trigger restart
        
    except Exception as e:
        logger.error(f"Failed to restart bot: {e}")
        return False


async def graceful_restart(user_id: int, delay: int = 3) -> bool:
    """Perform graceful restart with delay."""
    try:
        # Create restart flag
        await create_restart_flag(user_id, "graceful_restart")
        
        # Wait for delay
        await asyncio.sleep(delay)
        
        # Restart
        return await restart_bot_process()
        
    except Exception as e:
        logger.error(f"Graceful restart failed: {e}")
        return False


def is_docker_environment() -> bool:
    """Check if running in Docker."""
    return os.path.exists("/.dockerenv") or os.path.exists("/proc/1/cgroup")


def get_restart_method() -> str:
    """Get recommended restart method based on environment."""
    if is_docker_environment():
        return "docker"
    elif os.getenv("SUPERVISOR_ENABLED"):
        return "supervisor"
    elif os.getenv("SYSTEMD_ENABLED"):
        return "systemd"
    else:
        return "process"


async def send_restart_notification(bot, admin_ids: list, user_id: int) -> None:
    """Send restart notification to admins."""
    try:
        message = (
            "🔄 <b>БОТ ПЕРЕЗАПУСКАЕТСЯ</b>\n\n"
            f"👤 Инициатор: <code>{user_id}</code>\n"
            f"⏰ Время: {asyncio.get_event_loop().time()}\n"
            f"🔧 Метод: {get_restart_method()}\n\n"
            "⏳ Ожидайте восстановления..."
        )
        
        for admin_id in admin_ids:
            if admin_id != user_id:  # Don't send to the user who initiated
                try:
                    await bot.send_message(admin_id, message, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")
                    
    except Exception as e:
        logger.error(f"Failed to send restart notifications: {e}")


class RestartManager:
    """Manager for bot restart operations."""
    
    def __init__(self, bot):
        self.bot = bot
        self.restart_in_progress = False
    
    async def request_restart(self, user_id: int, reason: str = "admin_request") -> bool:
        """Request bot restart."""
        if self.restart_in_progress:
            return False
        
        self.restart_in_progress = True
        
        try:
            # Send notifications to admins
            await send_restart_notification(self.bot, config.ADMIN_IDS, user_id)
            
            # Perform graceful restart
            return await graceful_restart(user_id)
            
        except Exception as e:
            logger.error(f"Restart request failed: {e}")
            self.restart_in_progress = False
            return False
    
    async def check_and_handle_restart_flag(self) -> bool:
        """Check for restart flag on startup and handle it."""
        try:
            flag_content = await check_restart_flag()
            if flag_content:
                logger.info(f"Found restart flag: {flag_content}")
                
                # Send restart completed notification
                message = (
                    "✅ <b>БОТ ПЕРЕЗАПУЩЕН</b>\n\n"
                    f"📝 Причина: {flag_content}\n"
                    f"⏰ Время: {asyncio.get_event_loop().time()}\n\n"
                    "🚀 Бот снова в работе!"
                )
                
                for admin_id in config.ADMIN_IDS:
                    try:
                        await self.bot.send_message(admin_id, message, parse_mode="HTML")
                    except Exception as e:
                        logger.error(f"Failed to notify admin {admin_id} about restart completion: {e}")
                
                # Remove flag
                await remove_restart_flag()
                return True
                
        except Exception as e:
            logger.error(f"Failed to handle restart flag: {e}")
        
        return False