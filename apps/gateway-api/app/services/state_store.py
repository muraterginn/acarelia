import redis.asyncio as aioredis
from app.config import settings

_redis: aioredis.Redis | None = None

async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        # from_url yerine doğrudan aioredis.from_url kullanabilirsiniz
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return _redis

async def set_status(job_id: str, status: str):
    r = await get_redis()
    await r.set(f"job:{job_id}:status", status)

async def get_status(job_id: str) -> str:
    r = await get_redis()
    status = await r.get(f"job:{job_id}:status")
    return status or "pending"