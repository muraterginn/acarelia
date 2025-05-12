import logging
import redis.asyncio as aioredis
from typing import Optional

logger = logging.getLogger("common.state_store")

class StateStore:
    """
    Job bazlı durum güncellemeleri için Redis client.
    """

    def __init__(self, url: str):
        self._url = url
        self._redis: Optional[aioredis.Redis] = None

    async def _get_client(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis for StateStore")
        return self._redis

    async def set_status(self, job_id: str, status: str):
        r = await self._get_client()
        key = f"job:{job_id}:status"
        await r.set(key, status)
        logger.debug("Set %s = %r", key, status)

    async def get_status(self, job_id: str) -> str:
        r = await self._get_client()
        key = f"job:{job_id}:status"
        val = await r.get(key)
        return val or "pending"