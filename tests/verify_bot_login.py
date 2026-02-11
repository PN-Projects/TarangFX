import asyncio
import os
from telethon import TelegramClient
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

async def main():
    logger.info("Starting minimal Telethon authentication check...")
    
    if not api_id or not api_hash or not bot_token:
        logger.error("Missing credentials in .env")
        return

    try:
        client = TelegramClient('check_login_session', int(api_id), api_hash)
        await client.start(bot_token=bot_token)
        
        me = await client.get_me()
        logger.info(f"✅ Successfully logged in as: {me.username} (ID: {me.id})")
        
        logger.info("Keep running for 5 seconds...")
        await asyncio.sleep(5)
        
        await client.disconnect()
        logger.info("Disconnected cleanly.")
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
