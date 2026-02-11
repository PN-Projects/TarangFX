"""
Async Redis Cache - Fully async, connection pooling
Used for sessions, rate limiting, and caching
"""

import redis.asyncio as redis
import msgpack
from typing import Optional, Any
from loguru import logger

from config import config


class Cache:
    """Async Redis cache with connection pooling"""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Create Redis connection pool - ASYNC"""
        try:
            self._redis = await redis.from_url(
                config.REDIS_URL,
                encoding="utf-8",
                decode_responses=False,  # Binary mode for msgpack
                max_connections=config.REDIS_POOL_SIZE,
                socket_keepalive=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            
            # Test connection
            await self._redis.ping()
            
            logger.info("✅ Redis cache connected successfully")
            logger.info(f"Pool size: {config.REDIS_POOL_SIZE}")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            logger.info("Redis cache closed")
    
    # ========================================================================
    # BASIC OPERATIONS (All async)
    # ========================================================================
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache - ASYNC
        Automatically deserializes with msgpack
        """
        try:
            data = await self._redis.get(key)
            if data:
                return msgpack.unpackb(data, raw=False)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache - ASYNC
        Automatically serializes with msgpack
        
        Args:
            key: Cache key
            value: Value to cache (must be msgpack-serializable)
            ttl: TTL in seconds (None = config default)
        """
        try:
            data = msgpack.packb(value, use_bin_type=True)
            ttl = ttl or config.CACHE_TTL
            await self._redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache - ASYNC"""
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists - ASYNC"""
        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key - ASYNC"""
        try:
            await self._redis.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    # ========================================================================
    # RATE LIMITING (Token bucket algorithm)
    # ========================================================================
    
    async def check_rate_limit(
        self,
        user_id: int,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check rate limit using token bucket - ASYNC
        
        Args:
            user_id: User ID
            max_requests: Max requests in window
            window_seconds: Time window in seconds
            
        Returns:
            True if allowed, False if rate limited
        """
        key = f"rate_limit:{user_id}"
        
        try:
            # Get current count
            count = await self._redis.get(key)
            
            if count is None:
                # First request in window
                await self._redis.setex(key, window_seconds, 1)
                return True
            
            count = int(count)
            
            if count < max_requests:
                # Increment and allow
                await self._redis.incr(key)
                return True
            
            # Rate limited
            return False
            
        except Exception as e:
            logger.error(f"Rate limit check error for user {user_id}: {e}")
            # On error, allow request (fail open)
            return True
    
    async def get_rate_limit_reset(self, user_id: int) -> int:
        """Get seconds until rate limit resets - ASYNC"""
        key = f"rate_limit:{user_id}"
        try:
            ttl = await self._redis.ttl(key)
            return max(0, ttl)
        except:
            return 0
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    async def save_session(
        self,
        user_id: int,
        session_data: dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Save user session - ASYNC"""
        key = f"session:{user_id}"
        ttl = ttl or config.SESSION_TTL
        return await self.set(key, session_data, ttl)
    
    async def get_session(self, user_id: int) -> Optional[dict]:
        """Get user session - ASYNC"""
        key = f"session:{user_id}"
        return await self.get(key)
    
    async def delete_session(self, user_id: int) -> bool:
        """Delete user session - ASYNC"""
        key = f"session:{user_id}"
        return await self.delete(key)
    
    async def extend_session(self, user_id: int, ttl: Optional[int] = None) -> bool:
        """Extend session TTL - ASYNC"""
        key = f"session:{user_id}"
        ttl = ttl or config.SESSION_TTL
        return await self.expire(key, ttl)
    
    # ========================================================================
    # CACHING HELPERS
    # ========================================================================
    
    async def get_or_set(
        self,
        key: str,
        fetch_func,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get from cache or fetch and cache - ASYNC
        
        Args:
            key: Cache key
            fetch_func: Async function to call if cache miss
            ttl: Cache TTL
            
        Returns:
            Cached or fetched value
        """
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached
        
        # Cache miss - fetch
        value = await fetch_func()
        
        # Cache for next time
        if value is not None:
            await self.set(key, value, ttl)
        
        return value
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern - ASYNC
        
        Args:
            pattern: Redis pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = []
            async for key in self._redis.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                await self._redis.delete(*keys)
                return len(keys)
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidate error for pattern {pattern}: {e}")
            return 0
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    async def get_stats(self) -> dict:
        """Get cache statistics - ASYNC"""
        try:
            info = await self._redis.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        import asyncio
        stats = asyncio.run(self.get_stats())
        hits = stats.get("keyspace_hits", 0)
        misses = stats.get("keyspace_misses", 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0


# ============================================================================
# GLOBAL CACHE INSTANCE
# ============================================================================
cache = Cache()
