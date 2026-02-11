"""Help command handler"""
from loguru import logger

async def handle_help(event, bot):
    """Handle /help command - ASYNC"""
    message = (
        "<b>🎵 TarangFX Help</b>\n\n"
        "<b>Supported Operations:</b>\n"
        "• Format Conversion (MP3, AAC, FLAC, etc.)\n"
        "• Sample Rate Adjustment\n"
        "• Bitrate Control\n"
        "• Audio Effects (Reverb, Delay, etc.)\n"
        "• Normalization\n"
        "• Trimming\n\n"
        "<b>Free Tier:</b>\n"
        "• Max 30 min duration\n"
        "• Lossy formats only\n"
        "• Up to 44.1kHz sample rate\n\n"
        "<b>Premium Tier:</b>\n"
        "• Unlimited duration\n"
        "• Lossless formats\n"
        "• Up to 96kHz sample rate\n"
        "• All effects available\n\n"
        "Contact @dotenv for premium"
    )
    
    await event.respond(message, parse_mode='html')
    logger.info(f"User {event.sender_id} requested help")
