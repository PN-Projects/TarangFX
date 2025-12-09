"""
Custom Pyrogram Client for PnProjects Audio Bot
Provides enhanced client functionality with custom name
"""

import logging
from pyrogram import Client
from config import Config

logger = logging.getLogger(__name__)


class PnProjects(Client):
    """
    Custom Pyrogram Client class named PnProjects
    Extends base Client with additional functionality
    """

    def __init__(self):
        super().__init__(
            name="PnProjects",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=8,
            sleep_threshold=10,
            max_concurrent_transmissions=4
        )

    async def start(self):
        """Start the bot with custom initialization"""
        await super().start()
        bot_info = await self.get_me()
        Config.BOT_USERNAME = bot_info.username
        logger.info("✓ %s started successfully!", Config.BOT_NAME)
        logger.info("✓ Username: @%s", bot_info.username)
        logger.info("✓ Bot ID: %s", bot_info.id)
        if Config.FORCE_SUB_CHANNEL:
            logger.info(
                "✓ Force-sub channel configured as: %s (type: %s)",
                Config.FORCE_SUB_CHANNEL,
                type(Config.FORCE_SUB_CHANNEL).__name__,
            )
        logger.info("=" * 50)

    async def stop(self, *args):
        """Stop the bot with cleanup"""
        await super().stop()
        logger.info("✓ %s stopped successfully!", Config.BOT_NAME)
