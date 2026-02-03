from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .scanner import analyze_domain_async
from backend.cache.redis_client import get_redis_async
from .cache_local import AsyncInMemoryCache
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hashtrack")

app = FastAPI(title="HashTrack API")

# In-process fallback cache
fallback_cache = AsyncInMemoryCache()


class AnalyzeRequest(BaseModel):
    url: str


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    try:
        domain = req.url
        from .utils import extract_domain
        d = extract_domain(domain)

        cache_key = f"hashtrack:{d}"

        redis_client = get_redis_async()
        use_redis = False
        if redis_client is not None:
            try:
                # verify connection
                pong = await redis_client.ping()
                use_redis = bool(pong)
            except Exception as e:
                logger.info("Redis not available, falling back to in-memory cache: %s", e)
                use_redis = False

        # try cache
        if use_redis:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    logger.info("Cache hit (redis) %s", d)
                    try:
                        return json.loads(cached)
                    except Exception:
                        logger.info("Failed to parse cached JSON, re-analyzing %s", d)
            except Exception as e:
                logger.info("Redis get failed, falling back: %s", e)

        else:
            cached = await fallback_cache.get(cache_key)
            if cached:
                logger.info("Cache hit (local) %s", d)
                try:
                    return json.loads(cached)
                except Exception:
                    logger.info("Failed to parse local cached JSON, re-analyzing %s", d)

        # perform analysis
        logger.info("Analyzing domain %s", d)
        result = await analyze_domain_async(req.url)

        # store in cache
        serialized = json.dumps(result)
        if use_redis:
            try:
                await redis_client.set(cache_key, serialized, ex=24 * 3600)
                logger.info("Stored result in redis for %s", d)
            except Exception as e:
                logger.info("Failed to set redis cache: %s", e)
        else:
            await fallback_cache.set(cache_key, serialized, ex=24 * 3600)
            logger.info("Stored result in local cache for %s", d)

        return result
    except Exception as e:
        logger.exception("Error in /analyze")
        raise HTTPException(status_code=500, detail=str(e))
