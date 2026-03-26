"""
TarangFX Telethon Bot - Fully Async, No Blocking
Handles 100K+ concurrent users with async operations
"""

import sys
import asyncio
from pathlib import Path
from loguru import logger
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
from telethon.tl.types import DocumentAttributeAudio

# Use uvloop for 2x performance boost
from config import config
from aiohttp import web
if config.USE_UVLOOP:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logger.info("✅ Using uvloop (2x faster event loop)")

from core.database import db
from core.cache import cache
from core.concurrency import ConcurrencyManager
from handlers.start import handle_start
from handlers.help import handle_help
from handlers.audio import handle_audio_file
from handlers.sudo import handle_adduser, handle_removeuser
from handlers.callbacks import handle_callback


logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>",
    level=config.LOG_LEVEL,
    colorize=True,
)

if config.LOG_TO_FILE:
    logger.add(
        config.LOG_DIR / "tarangfx_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
    )


concurrency = ConcurrencyManager()


bot = TelegramClient(
    config.SESSION_NAME,
    config.API_ID,
    config.API_HASH,
    # Performance optimizations
    connection_retries=10,
    retry_delay=5,
    auto_reconnect=True,
    flood_sleep_threshold=60, # Wait up to 60s automatically
    receive_updates=True,
    # Use faster protocol
    use_ipv6=False,
)


logger.info("=" * 80)
logger.info("TarangFX Telethon Bot - Async Architecture")
logger.info("=" * 80)



@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """
    Handle /start command - ASYNC
    No blocking operations
    """
    try:
        await handle_start(event, bot)
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await event.respond("❌ An error occurred. Please try again.")


@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Handle /help command - ASYNC"""
    try:
        await handle_help(event, bot)
    except Exception as e:
        logger.error(f"Error in help handler: {e}")
        await event.respond("❌ An error occurred. Please try again.")


@bot.on(events.NewMessage(pattern='/adduser'))
async def adduser_handler(event):
    """Handle /adduser command - ASYNC, sudo only"""
    try:
        await handle_adduser(event, bot)
    except Exception as e:
        logger.error(f"Error in adduser handler: {e}")


@bot.on(events.NewMessage(pattern='/removeuser'))
async def removeuser_handler(event):
    """Handle /removeuser command - ASYNC, sudo only"""
    try:
        await handle_removeuser(event, bot)
    except Exception as e:
        logger.error(f"Error in removeuser handler: {e}")


@bot.on(events.NewMessage())
async def audio_handler(event):
    """
    Handle audio file uploads - FULLY ASYNC
    
    Key Features:
    - Semaphore-limited concurrent downloads
    - Non-blocking file operations
    - Per-user concurrency limits
    - Automatic cleanup
    """
    # Check if message has audio file
    if not event.message.media:
        return
    
    # Check if it's an audio file or document with audio
    is_audio = (
        event.message.audio or
        (event.message.document and any(
            isinstance(attr, DocumentAttributeAudio)
            for attr in event.message.document.attributes
        ))
    )
    
    if not is_audio:
        return
    
    try:
        # Handle audio file asynchronously
        await handle_audio_file(event, bot, concurrency)
        
    except Exception as e:
        logger.error(f"Error in audio handler: {e}")
        await event.respond("❌ An error occurred processing your file.")


@bot.on(events.CallbackQuery())
async def callback_handler(event):
    """
    Handle inline button callbacks - ASYNC
    All UI interactions handled here
    """
    try:
        await handle_callback(event, bot, concurrency)
    except Exception as e:
        logger.error(f"Error in callback handler: {e}")
        try:
            await event.answer("❌ An error occurred", alert=True)
        except:
            pass


# ============================================================================
# STARTUP & SHUTDOWN
# ============================================================================

async def startup():
    """Initialize services on startup"""
    logger.info("🚀 Starting TarangFX Telethon Bot...")
    
    try:
        # Connect to database (async)
        await db.connect()
        
        # Connect to cache (async)
        await cache.connect()
        
        # Start background cleanup task
        asyncio.create_task(cleanup_loop())
        
        logger.info("=" * 80)
        logger.info("✅ Bot initialized successfully")
        logger.info(f"✅ Database: Connected (pool size: {config.DB_POOL_MIN_SIZE}-{config.DB_POOL_MAX_SIZE})")
        logger.info(f"✅ Cache: Connected (pool size: {config.REDIS_POOL_SIZE})")
        logger.info(f"✅ Max concurrent downloads: {config.MAX_CONCURRENT_DOWNLOADS}")
        logger.info(f"✅ Max concurrent processing: {config.MAX_CONCURRENT_PROCESSING}")
        logger.info(f"✅ Max operations per user: {config.MAX_OPERATIONS_PER_USER}")
        logger.info("=" * 80)
        logger.info("🎉 Bot is ready to handle 100K+ concurrent users!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise


async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down bot...")
    
    try:
        # Disconnect from database
        await db.disconnect()
        
        # Disconnect from cache
        await cache.disconnect()
        
        # Cleanup all temp files
        await concurrency.cleanup_all()
        
        logger.info("✅ Bot shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


async def cleanup_loop():
    """Background task to cleanup expired sessions and files"""
    logger.info("Started cleanup background task")
    
    while True:
        try:
            await asyncio.sleep(config.CLEANUP_INTERVAL)
            
            # Cleanup expired files
            await concurrency.cleanup_expired()
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in cleanup loop: {e}")


async def health_check_handler(request):
    """Handle incoming pings from HF infrastructure or cron-job"""
    return web.Response(text="Bot is awake and running!")

async def start_health_server():
    """Start the aiohttp server on port 7860 for Hugging Face Spaces"""
    app = web.Application()
    app.router.add_get('/', health_check_handler)
    app.router.add_get('/health', health_check_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # HF Spaces strictly requires port 7860
    site = web.TCPSite(runner, '0.0.0.0', 7860)
    logger.info("Starting health check server on port 7860...")
    await site.start()


async def self_ping_loop():
    """Self-ping every 50 minutes to prevent HF Space from going idle"""
    import aiohttp
    PING_INTERVAL = 50 * 60  # 50 minutes in seconds
    # Wait a bit before starting so the server is up
    await asyncio.sleep(30)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:7860/health', timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    logger.info(f"[KeepAlive] Self-ping OK: {resp.status}")
        except Exception as e:
            logger.warning(f"[KeepAlive] Self-ping failed: {e}")
        await asyncio.sleep(PING_INTERVAL)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point with FloodWait handling"""
    while True:
        try:
            await bot.start(bot_token=config.BOT_TOKEN)
            await startup()
            
            # Start health check server for HF Spaces
            await start_health_server()
            
            # Start self-ping loop to prevent HF Space from going idle
            asyncio.create_task(self_ping_loop())
            
            logger.info("Bot is running... Press Ctrl+C to stop")
            await bot.run_until_disconnected()
            break  # Clean exit
            
        except FloodWaitError as e:
            wait_sec = e.seconds
            logger.warning(f"⏳ Telegram FloodWait: need to wait {wait_sec}s before reconnecting...")
            await asyncio.sleep(wait_sec + 5)  # +5s buffer
            logger.info("Retrying bot.start() after FloodWait...")
            continue
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            break
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            break
        finally:
            await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
