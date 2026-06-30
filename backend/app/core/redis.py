import json
import time
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Local in-memory cache for development."""
    def __init__(self):
        self._data = {}
        logger.info("Initialized local In-Memory Cache.")

    async def initialize(self):
        # No-op for in-memory cache
        pass

    async def get(self, key: str) -> Optional[str]:
        if key not in self._data:
            return None
        value, expiry = self._data[key]
        if expiry is not None and time.time() > expiry:
            del self._data[key]
            return None
        return value

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        # Auto-serialize objects if they are not strings/bytes
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value)
            
        expiry = time.time() + ex if ex is not None else None
        self._data[key] = (value, expiry)
        return True

    async def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False

    async def delete_pattern(self, pattern: str) -> int:
        """Find and delete keys matching a pattern."""
        count = 0
        keys_to_delete = await self.keys(pattern)
        for k in keys_to_delete:
            await self.delete(k)
            count += 1
        return count

    async def keys(self, pattern: str) -> list[str]:
        # Simple glob-like filter
        clean_pat = pattern.replace("*", "")
        return [k for k in self._data.keys() if clean_pat in k]

    async def ping(self) -> bool:
        return True


# Global Cache Instance
cache = InMemoryCache()
