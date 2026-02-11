"""
Configuration for TarangFX Telethon Bot
Pure async, no blocking operations
"""

import os
from pathlib import Path
from typing import Set
from pydantic_settings import BaseSettings
from pydantic import Field
from loguru import logger


class Config(BaseSettings):
    """Main configuration - designed for async operation"""
    
    # ========================================================================
    # TELETHON CONFIGURATION
    # ========================================================================
    API_ID: int = Field(..., description="Telegram API ID from my.telegram.org")
    API_HASH: str = Field(..., description="Telegram API Hash from my.telegram.org")
    BOT_TOKEN: str = Field(..., description="Bot token from @BotFather")
    
    # Session configuration
    SESSION_NAME: str = Field(default="tarangfx_bot", description="Session file name")
    
    # ========================================================================
    # CONCURRENCY LIMITS (Prevent overwhelming system)
    # ========================================================================
    MAX_CONCURRENT_DOWNLOADS: int = Field(
        default=100,
        description="Max simultaneous file downloads (semaphore limit)"
    )
    MAX_CONCURRENT_UPLOADS: int = Field(
        default=100,
        description="Max simultaneous file uploads"
    )
    MAX_CONCURRENT_PROCESSING: int = Field(
        default=50,
        description="Max simultaneous audio processing tasks"
    )
    
    # Per-user limits (prevent single user from hogging resources)
    MAX_OPERATIONS_PER_USER: int = Field(
        default=3,
        description="Max concurrent operations per user"
    )
    
    # ========================================================================
    # DATABASE (PostgreSQL - Async)
    # ========================================================================
    DATABASE_URL: str = Field(
        default="postgresql://tarangfx:password@localhost:5432/tarangfx",
        description="PostgreSQL connection URL"
    )
    DB_POOL_MIN_SIZE: int = Field(default=10, description="Min pool connections")
    DB_POOL_MAX_SIZE: int = Field(default=100, description="Max pool connections")
    DB_POOL_TIMEOUT: float = Field(default=30.0, description="Pool timeout in seconds")
    
    # ========================================================================
    # CACHE (Redis - Async)
    # ========================================================================
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    REDIS_POOL_SIZE: int = Field(default=50, description="Redis connection pool size")
    CACHE_TTL: int = Field(default=300, description="Default cache TTL (5 minutes)")
    
    # ========================================================================
    # FILE STORAGE
    # ========================================================================
    TEMP_DIR: Path = Field(
        default=Path("/tmp/tarangfx"),
        description="Temporary file storage"
    )
    USE_S3: bool = Field(default=False, description="Use S3 for file storage")
    S3_BUCKET: str = Field(default="tarangfx-files", description="S3 bucket name")
    S3_ENDPOINT: str = Field(default="", description="S3 endpoint URL")
    S3_ACCESS_KEY: str = Field(default="", description="S3 access key")
    S3_SECRET_KEY: str = Field(default="", description="S3 secret key")
    
    # ========================================================================
    # AUDIO PROCESSING LIMITS
    # ========================================================================
    MAX_FILE_SIZE_MB: int = Field(default=2048, description="Max file size in MB (2GB)")
    FREE_TIER_MAX_DURATION_MIN: int = Field(
        default=30,
        description="Free tier max audio duration (minutes)"
    )
    
    # Quality limits
    FREE_MAX_SAMPLE_RATE: int = Field(default=44100, description="Free tier max sample rate")
    PREMIUM_MAX_SAMPLE_RATE: int = Field(default=96000, description="Premium max sample rate")
    
    # ========================================================================
    # RATE LIMITING (Per user)
    # ========================================================================
    FREE_REQUESTS_PER_MINUTE: int = Field(default=10, description="Free tier rate limit")
    FREE_REQUESTS_PER_HOUR: int = Field(default=100, description="Free tier hourly limit")
    PREMIUM_REQUESTS_PER_MINUTE: int = Field(default=100, description="Premium rate limit")
    PREMIUM_REQUESTS_PER_HOUR: int = Field(default=10000, description="Premium hourly limit")
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    SESSION_TTL: int = Field(default=300, description="Session timeout (5 minutes)")
    CLEANUP_INTERVAL: int = Field(default=60, description="Cleanup task interval (seconds)")
    
    # ========================================================================
    # ADMIN USERS
    # ========================================================================
    SUDO_USERS: str = Field(default="", description="Comma-separated admin user IDs")
    SUPPORT_USERNAME: str = Field(default="dotenv", description="Support contact")
    
    # ========================================================================
    # LOGGING
    # ========================================================================
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_TO_FILE: bool = Field(default=True, description="Log to file")
    LOG_DIR: Path = Field(default=Path("logs"), description="Log directory")
    
    # ========================================================================
    # PERFORMANCE TUNING
    # ========================================================================
    USE_UVLOOP: bool = Field(default=True, description="Use uvloop (faster event loop)")
    EXECUTOR_MAX_WORKERS: int | None = Field(
        default=None,  # None = CPU count * 5
        description="Max workers for CPU-bound tasks"
    )
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def free_max_duration_seconds(self) -> int:
        """Get free tier max duration in seconds"""
        return self.FREE_TIER_MAX_DURATION_MIN * 60
    
    @property
    def sudo_users_set(self) -> Set[int]:
        """Parse sudo users into set"""
        if not self.SUDO_USERS:
            return set()
        return {int(uid.strip()) for uid in self.SUDO_USERS.split(',') if uid.strip()}
    
    def is_sudo_user(self, user_id: int) -> bool:
        """Check if user is sudo"""
        return user_id in self.sudo_users_set
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


# ============================================================================
# GLOBAL CONFIG INSTANCE
# ============================================================================
config = Config()


# ============================================================================
# VALIDATION
# ============================================================================
def validate_config():
    """Validate critical configuration"""
    errors = []
    
    if not config.API_ID or not config.API_HASH:
        errors.append("API_ID and API_HASH are required (get from my.telegram.org)")
    
    if not config.BOT_TOKEN:
        errors.append("BOT_TOKEN is required (get from @BotFather)")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    # Create directories
    config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 80)
    logger.info("TarangFX Telethon - Async Configuration")
    logger.info("=" * 80)
    logger.info(f"Max Concurrent Downloads: {config.MAX_CONCURRENT_DOWNLOADS}")
    logger.info(f"Max Concurrent Processing: {config.MAX_CONCURRENT_PROCESSING}")
    logger.info(f"Max Operations Per User: {config.MAX_OPERATIONS_PER_USER}")
    logger.info(f"Database Pool: {config.DB_POOL_MIN_SIZE}-{config.DB_POOL_MAX_SIZE}")
    logger.info(f"Redis Pool: {config.REDIS_POOL_SIZE}")
    logger.info(f"Use uvloop: {config.USE_UVLOOP}")
    logger.info(f"Temp Directory: {config.TEMP_DIR}")
    logger.info("=" * 80)
    
    return True


# Validate on import
validate_config()
