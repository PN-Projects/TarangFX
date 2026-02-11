"""Start command handler"""
from telethon import Button
from loguru import logger
from core.database import db

async def handle_start(event, bot):
    """Handle /start command - ASYNC"""
    user = event.sender
    
    await db.create_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name
    )
    is_premium = await db.is_premium(user.id)
    status = "🌟 PREMIUM" if is_premium else "🆓 FREE"
    
    message = (
        f"👋 <b>Welcome to TarangFX!</b>\n"
        f"🎵 Professional Audio Processing Bot\n\n"
        f"👤 <b>Status:</b> {status}\n\n"
        f"<b>Features:</b>\n"
        f"• Convert Formats (MP3, AAC, OGG, Opus)\n"
        f"• Change Bitrate & Sample Rate\n"
        f"• Normalize Audio\n\n"
        f"<b>🌟 Premium Features:</b>\n"
        f"• Lossless Formats (FLAC, WAV, AIFF, ALAC)\n"
        f"• High-Res Audio (48kHz, 96kHz)\n"
        f"• Advanced Effects (Reverb, Bass Boost, Vocal Enhance)\n"
        f"• Trim Audio Tool\n"
        f"• Unlimited Duration\n\n"
        f"<b>How to use:</b>\n"
        f"Send me any audio file to start processing!"
    )
    
    buttons = []
    if not is_premium:
        buttons.append([Button.url("⭐ Buy Premium", "https://t.me/dotenv")])
    
    buttons.append([Button.inline("📖 Help", data="help_main")])
    
    await event.respond(message, buttons=buttons, parse_mode='html')
    logger.info(f"User {user.id} started bot")
