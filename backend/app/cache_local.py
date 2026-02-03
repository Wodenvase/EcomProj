import asyncio
import time
from typing import Optional


class AsyncInMemoryCache:
    """Simple async in-memory TTL cache. Not persisted; intended as Redis fallback for dev."""

    def __init__(self):
        self._store = {}  # key -> (value_str, expires_at)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            value, expires_at = entry
            if expires_at is not None and time.time() > expires_at:
                del self._store[key]
                return None
            return value

    async def set(self, key: str, value: str, ex: Optional[int] = None):
        expires_at = time.time() + ex if ex else None
        async with self._lock:
            self._store[key] = (value, expires_at)
