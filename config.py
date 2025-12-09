"""
Configuration module for PnProjects Audio Bot
Loads and validates environment variables
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for bot settings"""

    # Required Telegram Bot Credentials
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    API_ID: int = int(os.getenv("API_ID", "0"))
    API_HASH: str = os.getenv("API_HASH", "")

    # Optional Force Subscription
    FORCE_SUB_CHANNEL: Optional[str] = os.getenv("FORCE_SUB_CHANNEL", None)

    # Bot Settings
    BOT_NAME: str = "PnProjects Audio Bot"
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "audio_processor_bot")

    # File Settings
    DOWNLOAD_LOCATION: str = "./downloads"
    MAX_FILE_SIZE: int = 2000 * 1024 * 1024  # 2GB in bytes

    # Processing Settings
    DEFAULT_BITRATE: str = "320k"
    DEFAULT_SAMPLE_RATE: int = 48000
    DEFAULT_CHANNELS: int = 2

    # Supported Audio Formats
    SUPPORTED_FORMATS = [
        # Lossy formats
        "mp3", "m4a", "aac", "ogg", "opus", "wma", "ac3", "amr",
        # Lossless formats
        "flac", "wav", "alac", "ape", "wv", "tta", "aiff", "aif",
        # Other formats
        "webm", "mka", "dts", "mp2", "mp1", "spx", "oga"
    ]

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required in .env file")
        if not cls.API_ID or cls.API_ID == 0:
            raise ValueError("API_ID is required in .env file")
        if not cls.API_HASH:
            raise ValueError("API_HASH is required in .env file")

        # Create download directory if not exists
        os.makedirs(cls.DOWNLOAD_LOCATION, exist_ok=True)

        # Normalize force-sub channel to a format pyrogram accepts
        cls.FORCE_SUB_CHANNEL = cls.normalize_force_sub_channel(cls.FORCE_SUB_CHANNEL)

        return True

    @classmethod
    def get_format_display_name(cls, format_code: str) -> str:
        """Get display name for audio format"""
        format_names = {
            "mp3": "MP3 (Lossy)",
            "m4a": "M4A/AAC (Lossy)",
            "aac": "AAC (Lossy)",
            "ogg": "OGG Vorbis (Lossy)",
            "opus": "OPUS (Lossy)",
            "flac": "FLAC (Lossless)",
            "wav": "WAV (Lossless)",
            "alac": "ALAC (Lossless)",
            "ape": "APE (Lossless)",
            "wv": "WavPack (Lossless)",
            "tta": "TTA (Lossless)",
            "aiff": "AIFF (Lossless)",
            "wma": "WMA (Lossy)",
            "webm": "WebM Audio"
        }
        return format_names.get(format_code, format_code.upper())

    @classmethod
    def normalize_force_sub_channel(cls, channel: Optional[str]) -> Optional[str]:
        """
        Normalize FORCE_SUB_CHANNEL to something pyrogram accepts.

        Supports:
        - Full t.me URLs
        - Handles leading @username
        - Adds -100 prefix for numeric IDs missing it
        """
        if not channel:
            return None

        chan = channel.strip()
        if not chan:
            return None

        # Strip common URL prefixes
        prefixes = ("https://t.me/", "http://t.me/", "t.me/")
        for prefix in prefixes:
            if chan.startswith(prefix):
                chan = chan[len(prefix):]
                break

        # Remove leading '@'
        if chan.startswith("@"):
            chan = chan[1:]

        # If numeric ID, ensure -100 prefix
        if chan.lstrip("-").isdigit():
            if not chan.startswith("-100"):
                chan = f"-100{chan.lstrip('-')}"
            # Return int for numeric IDs; pyrogram accepts int and avoids PeerIdInvalid
            try:
                return int(chan)
            except ValueError:
                return chan

        return chan


# Validate configuration on import
Config.validate()
