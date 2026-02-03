import redis
from typing import Optional


def get_redis(host: str = 'localhost', port: int = 6379, db: int = 0) -> Optional[redis.Redis]:
    try:
        client = redis.Redis(host=host, port=port, db=db)
        client.ping()
        return client
    except Exception:
        return None


def get_redis_async(host: str = 'localhost', port: int = 6379, db: int = 0):
    try:
        # redis-py exposes asyncio client under redis.asyncio
        import redis.asyncio as aioredis
        client = aioredis.Redis(host=host, port=port, db=db)
        return client
    except Exception:
        return None
