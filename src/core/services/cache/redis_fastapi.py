from redis.asyncio import Redis

from src.core.config import settings


redis = Redis(
    host=settings.redis_settings.host, 
    port=settings.redis_settings.port,
    db=settings.redis_settings.db
)