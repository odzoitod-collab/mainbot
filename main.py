"""Main bot entry point with optimizations."""
import asyncio
import logging
import sys
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramRetryAfter, TelegramAPIError

import config
from database import init_db
from middlewares.user_check import UserCheckMiddleware
from middlewares.throttling import ThrottlingMiddleware

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logging.getLogger("aiogram").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the bot."""
    logger.info("🚀 Starting bot...")
    
    # Init database
    await init_db()
    
    # Optimized session with connection pooling
    session = AiohttpSession(
        timeout=60,
    )
    
    # Init bot with optimized settings
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session
    )
    
    dp = Dispatcher()
    
    # Middlewares (order matters - throttling first)
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.5))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.3))
    dp.message.middleware(UserCheckMiddleware())
    dp.callback_query.middleware(UserCheckMiddleware())
    
    # Error handler with retry logic
    @dp.error()
    async def error_handler(event: ErrorEvent) -> bool:
        exception = event.exception
        
        # Handle rate limiting
        if isinstance(exception, TelegramRetryAfter):
            logger.warning(f"Rate limited, retry after {exception.retry_after}s")
            await asyncio.sleep(exception.retry_after)
            return True
        
        # Log other errors
        logger.error(f"Error: {exception}", exc_info=exception)
        
        # Try to notify user
        with suppress(Exception):
            if event.update.message:
                await event.update.message.answer("❌ Ошибка. Попробуйте снова.")
            elif event.update.callback_query:
                await event.update.callback_query.answer("❌ Ошибка", show_alert=True)
        
        return True
    
    # Register routers
    from handlers import (
        chat_commands_router, registration_router, user_menu_router,
        admin_profit_router, admin_manage_router, admin_mentors_router,
        admin_broadcast_router, admin_close_router, admin_direct_payments_router,
        community_create_router, admin_communities_router
    )
    
    dp.include_router(chat_commands_router)
    dp.include_router(registration_router)
    dp.include_router(user_menu_router)
    dp.include_router(community_create_router)
    dp.include_router(admin_profit_router)
    dp.include_router(admin_manage_router)
    dp.include_router(admin_mentors_router)
    dp.include_router(admin_broadcast_router)
    dp.include_router(admin_close_router)
    dp.include_router(admin_direct_payments_router)
    dp.include_router(admin_communities_router)
    
    logger.info("✅ Bot ready")
    
    try:
        # Drop pending updates for faster start
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            polling_timeout=30
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}", exc_info=True)
        sys.exit(1)
