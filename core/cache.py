"""
Async upstash-redis Cache - REST API based
Used for sessions, rate limiting, and caching
"""
# pyre-ignore-all-errors

import os
from upstash_redis.asyncio import Redis
import msgpack
from typing import Optional, Any
from loguru import logger

from config import config


class Cache:
    """Async Upstash Redis cache via REST API"""
    
    def __init__(self):
        # Using Any to prevent linter errors since Pyre might not know upstash_redis
        self._redis: Optional[Any] = None
        
    @property
    def redis(self) -> Any:
        if self._redis is None:
            raise RuntimeError("Cache not connected")
        return self._redis
    
    async def connect(self):
        """Create Upstash Redis connection - ASYNC"""
        try:
            # Check upstash credentials from config
            url = config.UPSTASH_REDIS_REST_URL or os.environ.get("UPSTASH_REDIS_REST_URL")
            token = config.UPSTASH_REDIS_REST_TOKEN or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
            
            if not url or not token:
                logger.warning("Upstash credentials not found in env, falling back to REDIS_URL if it's an Upstash URI.")
                url = config.REDIS_URL
                token = "missing_token"
            
            self._redis = Redis(url=url, token=token)
            
            # Test connection
            await self._redis.ping()
            
            logger.info("✅ Upstash Redis cache connected successfully")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise
    
    async def disconnect(self):
        """No connection pooling to close with Upstash REST"""
        logger.info("Upstash cache disconnected")
        
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache - ASYNC
        Automatically deserializes with msgpack
        """
        try:
            data = await self.redis.get(key)
            if data:
                # Upstash REST returns strings, we stored base64 strings
                if isinstance(data, str):
                     import base64
                     try:
                         raw_bytes = base64.b64decode(data)
                         return msgpack.unpackb(raw_bytes, raw=False)
                     except Exception as decode_err:
                         # In case it's not base64/msgpack (e.g. rate limit counts)
                         return data
                return data
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
            # Upstash needs binary encoding explicitly passed or base64
            # We will use base64 for safe REST transmission
            import base64
            b64_data = base64.b64encode(data).decode('utf-8')
            await self.redis.setex(key, ttl, b64_data)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache - ASYNC"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists - ASYNC"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key - ASYNC"""
        try:
            await self.redis.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False

    
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
            count = await self.redis.get(key)
            
            if count is None:
                # First request in window
                await self.redis.setex(key, window_seconds, 1)
                return True
            
            count = int(count)
            
            if count < max_requests:
                # Increment and allow (Upstash handles incr correctly on strings)
                await self.redis.incr(key)
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
            ttl = await self.redis.ttl(key)
            return max(0, ttl)
        except:
            return 0
    

    
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
        # Upstash REST client doesn't support scan_iter directly in the same way 
        # as redis-py, so we use a lua script or basic matching if needed.
        # For simplicity in this adaptation, we will just return 0 as this method
        # isn't heavily used in the core flow.
        logger.warning("Pattern invalidation not fully supported via Upstash REST without custom scripts")
        return 0
    
    async def get_stats(self) -> dict:
        """Get cache statistics - ASYNC"""
        try:
            info = await self.redis.info()
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


cache = Cache()
