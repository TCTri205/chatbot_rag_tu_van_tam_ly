"""
Redis client module - separate to avoid circular imports.
"""
import redis.asyncio as aioredis
from typing import Optional

from src.config import settings

# Global Redis connection
redis_client: Optional[aioredis.Redis] = None


async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    redis_client = await aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    return redis_client


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


def get_redis_client() -> Optional[aioredis.Redis]:
    """Get the current Redis client instance."""
    return redis_client


# Alias for convenience (used in Phase 2 APIs)
def get_redis() -> Optional[aioredis.Redis]:
    """Get the current Redis client instance (alias for get_redis_client)."""
    return redis_client

