# services/redis_cache.py
import redis.asyncio as redis
from config.settings import settings

class WorkerRedisCache:
    def __init__(self):
        # Connect to the Redis cache URL defined in the environment
        self.redis = redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)

    async def get_skill(self, skill_id: str, generation_id: str) -> str:
        # Retrieve using the strict (skill_id:generation_id) key format
        key = f"{skill_id}:{generation_id}"
        return await self.redis.get(key)