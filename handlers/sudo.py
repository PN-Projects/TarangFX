"""Sudo command handlers"""
from loguru import logger
from config import config
from core.database import db

async def handle_adduser(event, bot):
    """Handle /adduser command - ASYNC"""
    if not config.is_sudo_user(event.sender_id):
        await event.respond("❌ Unauthorized")
        return
    
    try:
        user_id = int(event.text.split()[1])
        await db.set_premium_status(user_id, True)
        await event.respond(f"✅ User {user_id} is now premium")
        logger.info(f"Admin {event.sender_id} added premium: {user_id}")
    except (IndexError, ValueError):
        await event.respond("Usage: /adduser <user_id>")
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        await event.respond(f"❌ Error: {e}")

async def handle_removeuser(event, bot):
    """Handle /removeuser command - ASYNC"""
    if not config.is_sudo_user(event.sender_id):
        await event.respond("❌ Unauthorized")
        return
    
    try:
        user_id = int(event.text.split()[1])
        await db.set_premium_status(user_id, False)
        await event.respond(f"✅ User {user_id} is now free tier")
        logger.info(f"Admin {event.sender_id} removed premium: {user_id}")
    except (IndexError, ValueError):
        await event.respond("Usage: /removeuser <user_id>")
    except Exception as e:
        logger.error(f"Error removing user: {e}")
        await event.respond(f"❌ Error: {e}")
