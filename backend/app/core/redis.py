import json
import time
import logging
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Fallback in-memory cache when Redis is unavailable."""
    def __init__(self):
        self._data = {}
        logger.warning("Redis is not configured or unavailable. Falling back to local In-Memory Cache.")

    async def get(self, key: str) -> Optional[str]:
        if key not in self._data:
            return None
        value, expiry = self._data[key]
        if expiry is not None and time.time() > expiry:
            del self._data[key]
            return None
        return value

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        expiry = time.time() + ex if ex is not None else None
        self._data[key] = (value, expiry)
        return True

    async def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    async def keys(self, pattern: str) -> list[str]:
        # Simple glob-like filter
        clean_pat = pattern.replace("*", "")
        return [k for k in self._data.keys() if clean_pat in k]

    async def ping(self) -> bool:
        return True


class RedisCacheWrapper:
    """Wrapper that tries connecting to Redis, otherwise falls back to InMemoryCache."""
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.fallback = InMemoryCache()
        self.is_redis_active = False

    async def initialize(self):
        redis_url = getattr(settings, "REDIS_URL", None) or "redis://localhost:6379/0"
        try:
            # Short connection timeout so it doesn't block startup
            self.redis = aioredis.from_url(
                redis_url, 
                socket_timeout=2.0, 
                socket_connect_timeout=2.0,
                decode_responses=True
            )
            await self.redis.ping()
            self.is_redis_active = True
            logger.info("Connected to Redis server successfully.")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}. Activating in-memory fallback cache.")
            self.redis = None
            self.fallback = InMemoryCache()
            self.is_redis_active = False

    async def get(self, key: str) -> Optional[str]:
        if self.is_redis_active and self.redis:
            try:
                return await self.redis.get(key)
            except Exception as e:
                logger.error(f"Redis get failed: {e}. Falling back...")
                self.is_redis_active = False
                self.fallback = InMemoryCache()
        return await self.fallback.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        # Auto-serialize objects if they are not strings/bytes
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value)
            
        if self.is_redis_active and self.redis:
            try:
                await self.redis.set(key, value, ex=ex)
                return True
            except Exception as e:
                logger.error(f"Redis set failed: {e}. Falling back...")
                self.is_redis_active = False
                self.fallback = InMemoryCache()
        return await self.fallback.set(key, value, ex=ex)

    async def delete(self, key: str) -> bool:
        if self.is_redis_active and self.redis:
            try:
                await self.redis.delete(key)
                return True
            except Exception as e:
                logger.error(f"Redis delete failed: {e}. Falling back...")
                self.is_redis_active = False
                self.fallback = InMemoryCache()
        return await self.fallback.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Find and delete keys matching a pattern."""
        count = 0
        if self.is_redis_active and self.redis:
            try:
                matching_keys = await self.redis.keys(pattern)
                if matching_keys:
                    await self.redis.delete(*matching_keys)
                    count = len(matching_keys)
                return count
            except Exception as e:
                logger.error(f"Redis delete pattern failed: {e}. Falling back...")
                self.is_redis_active = False
                self.fallback = InMemoryCache()
        
        fallback_keys = await self.fallback.keys(pattern)
        for k in fallback_keys:
            await self.fallback.delete(k)
            count += 1
        return count

    async def ping(self) -> bool:
        if self.is_redis_active and self.redis:
            try:
                return await self.redis.ping()
            except Exception:
                return False
        return True


# Global Cache Instance
cache = RedisCacheWrapper()
