# services/redis_cache.py
import redis.asyncio as redis
from config.settings import settings
from services.base_service import BaseService


class WorkerRedisCache(BaseService):
    def __init__(self):
        super().__init__()
        self.redis = redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)

    # Retrieve skill to be cached by worker based on skill_id:generation_id key
    async def get_skill(self, skill_id: str, generation_id: str) -> str | None:
        """Retrieves cached skill markdown string with fallback exception handling."""
        key = f"{skill_id}:{generation_id}"
        try:
            return await self.redis.get(key)
        except Exception:
            return None  # Triggers fallback to GCS download in agents

    # Inserts new skill via skill_id:generation_id key to the cache.
    async def set_skill(self, skill_id: str, generation_id: str, markdown_content: str):
        """Caches skill markdown string safely."""
        key = f"{skill_id}:{generation_id}"
        try:
            await self.redis.set(key, markdown_content)
        except Exception:
            pass  # Non-fatal if cache write fails

    async def invalidate_skill(self, skill_id: str, generation_id: str):
        """Invalidates a specific skill key."""
        key = f"{skill_id}:{generation_id}"
        try:
            await self.redis.delete(key)
        except Exception:
            pass