"""
Async Database Module - PostgreSQL
Fully async, connection pooling, no blocking
"""

import asyncpg
from typing import Optional, Set
from loguru import logger

from config import config


class Database:
    """Async PostgreSQL database with connection pooling"""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create connection pool - ASYNC, NON-BLOCKING"""
        try:
            self._pool = await asyncpg.create_pool(
                config.DATABASE_URL,
                min_size=config.DB_POOL_MIN_SIZE,
                max_size=config.DB_POOL_MAX_SIZE,
                timeout=config.DB_POOL_TIMEOUT,
                command_timeout=60,
                # Performance optimizations
                max_queries=50000,
                max_inactive_connection_lifetime=300,
            )
            
            # Initialize schema
            await self._initialize_schema()
            
            logger.info("✅ Database pool created successfully")
            logger.info(f"Pool size: {config.DB_POOL_MIN_SIZE}-{config.DB_POOL_MAX_SIZE}")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()
            logger.info("Database pool closed")
    
    async def _initialize_schema(self):
        """Initialize database schema if not exists"""
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            is_premium BOOLEAN DEFAULT FALSE,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium);
        CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);
        
        -- Add any other tables here
        """
        
        async with self._pool.acquire() as conn:
            await conn.execute(schema)
            logger.info("Database schema initialized")
    

    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """
        Get user by ID - ASYNC, NON-BLOCKING
        
        Returns:
            User dict or None
        """
        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM users WHERE user_id = $1",
                    user_id
                )
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    async def create_or_update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> dict:
        """
        Create or update user - ASYNC, NON-BLOCKING
        Uses UPSERT for atomic operation
        """
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO users (user_id, username, first_name, last_active)
                    VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                    ON CONFLICT (user_id) DO UPDATE
                    SET username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_active = CURRENT_TIMESTAMP
                    """,
                    user_id, username, first_name
                )
                
                return await self.get_user(user_id)
                
        except Exception as e:
            logger.error(f"Error creating/updating user {user_id}: {e}")
            raise
    
    async def set_premium_status(self, user_id: int, is_premium: bool) -> bool:
        """
        Set user premium status - ASYNC
        
        Returns:
            True if successful
        """
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    "UPDATE users SET is_premium = $1 WHERE user_id = $2",
                    is_premium, user_id
                )
                
                # Create user if doesn't exist
                if result == "UPDATE 0":
                    await conn.execute(
                        "INSERT INTO users (user_id, is_premium) VALUES ($1, $2)",
                        user_id, is_premium
                    )
                
                logger.info(f"Set premium status for user {user_id}: {is_premium}")
                return True
                
        except Exception as e:
            logger.error(f"Error setting premium for user {user_id}: {e}")
            return False
    
    async def get_premium_users(self) -> Set[int]:
        """
        Get all premium user IDs - ASYNC
        
        Returns:
            Set of premium user IDs
        """
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT user_id FROM users WHERE is_premium = TRUE"
                )
                
                return {row['user_id'] for row in rows}
                
        except Exception as e:
            logger.error(f"Error fetching premium users: {e}")
            return set()
    
    async def update_last_active(self, user_id: int):
        """Update user's last active timestamp - ASYNC, fire-and-forget"""
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = $1",
                    user_id
                )
        except Exception as e:
            logger.debug(f"Error updating last active for user {user_id}: {e}")
            # Non-critical, don't raise
    
    async def is_premium(self, user_id: int) -> bool:
        """
        Check if user is premium - ASYNC with caching
        
        Returns:
            True if premium, False otherwise
        """
        user = await self.get_user(user_id)
        return user.get('is_premium', False) if user else False
    
    async def get_stats(self) -> dict:
        """Get database statistics - ASYNC"""
        try:
            async with self._pool.acquire() as conn:
                total = await conn.fetchval("SELECT COUNT(*) FROM users")
                premium = await conn.fetchval(
                    "SELECT COUNT(*) FROM users WHERE is_premium = TRUE"
                )
                
                return {
                    "total_users": total,
                    "premium_users": premium,
                    "free_users": total - premium,
                }
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
            return {}



db = Database()
