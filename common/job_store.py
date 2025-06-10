import logging
import redis.asyncio as aioredis
from typing import Optional, Dict

logger = logging.getLogger("common.job_store")

class JobStore:
    def __init__(self, url: str):
        self._url = url
        self._redis = None

    async def _client(self):
        if not self._redis:
            self._redis = aioredis.from_url(self._url, encoding="utf-8", decode_responses=True)
            logger.info("Connected to Redis for JobStore")
        return self._redis

    def _make_key(self, job_id: str, field: str) -> str:
        return f"job:{job_id}:{field}"

    async def set_field(self, job_id: str, field: str, value: str):
        r = await self._client()
        key = self._make_key(job_id, field)
        await r.set(key, value)
        logger.debug("SET %s = %r", key, value)

    async def get_field(self, job_id: str, field: str) -> Optional[str]:
        r = await self._client()
        key = self._make_key(job_id, field)
        val = await r.get(key)
        logger.debug("GET %s → %r", key, val)
        return val

    async def delete_field(self, job_id: str, field: str):
        r = await self._client()
        key = self._make_key(job_id, field)
        await r.delete(key)
        logger.debug("DEL %s", key)

    async def get_all_fields(self, job_id: str) -> Dict[str, str]:
        r = await self._client()
        pattern = f"job:{job_id}:*"
        cursor = b"0"
        results = {}
        while cursor:
            cursor, keys = await r.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                vals = await r.mget(*keys)
                for k, v in zip(keys, vals):
                    # strip off the prefix and colon
                    field = k.decode().split(f"job:{job_id}:", 1)[1]
                    results[field] = v
        logger.debug("SCAN %s → %r", pattern, results)
        return results
