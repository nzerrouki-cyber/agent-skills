# services/redis_cache.py
import logging
import redis.asyncio as redis
from config.settings import settings
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class WorkerRedisCache(BaseService):
    def __init__(self):
        super().__init__()
        self.redis = redis.from_url(settings.REDIS_CACHE_URL, decode_responses=True)

    async def is_connected(self) -> bool:
        """Health check probe verifying Memorystore Redis connectivity."""
        try:
            return await self.redis.ping()
        except Exception:
            return False

    async def get_skill(self, skill_id: str, generation_id: str) -> str | None:
        """Retrieves cached skill markdown string with fallback exception handling."""
        key = f"{skill_id}:{generation_id}"
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.warning(f"Redis Cache Miss/Error for key '{key}': {str(e)}")
            return None

    async def set_skill(
        self, 
        skill_id: str, 
        generation_id: str, 
        markdown_content: str, 
        ttl_seconds: int = 86400
    ):
        """Caches skill markdown string safely with default 24-hour TTL."""
        key = f"{skill_id}:{generation_id}"
        try:
            await self.redis.set(key, markdown_content, ex=ttl_seconds)
        except Exception as e:
            logger.error(f"Failed to write key '{key}' to Redis: {str(e)}")

    async def invalidate_skill(self, skill_id: str, generation_id: str):
        """Invalidates a specific skill key across worker instances."""
        key = f"{skill_id}:{generation_id}"
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Failed to invalidate key '{key}' in Redis: {str(e)}")