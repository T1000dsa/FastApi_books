import logging
import gzip
from typing import Optional

from src.core.config import redis, settings
from src.core.database.models.models import BookModelOrm
from src.core.services import TextLoad


logger = logging.getLogger(__name__)

class BookCacheService:
    @staticmethod
    async def get_book_text(book_data: BookModelOrm) -> str:
        """Retrieve book text from cache or source, with compression handling."""
        cached_text = await redis.get(book_data.text_hook)
        logger.info(f'Cache {"hit" if cached_text else "miss"} for book {book_data.id}')

        if cached_text:
            try:
                return gzip.decompress(cached_text).decode()
            except gzip.BadGzipFile:
                return cached_text.decode()
        
        text_load = TextLoad(book_data)
        content = text_load.push_text()
        await BookCacheService._cache_book_text(book_data.text_hook, content)
        return content

    @staticmethod
    async def _cache_book_text(key: str, content: str) -> None:
        """Store book text in cache with compression."""
        compressed = gzip.compress(content.encode())
        await redis.set(key, compressed, ex=settings.cache.REDIS_CACHE_TTL_BOOKS)

    @staticmethod
    async def get_cache_stats() -> dict:
        """Return Redis memory and hit rate statistics."""
        memory_info = await redis.info("MEMORY")
        stats = await redis.info("STATS")
        
        hits = stats["keyspace_hits"]
        misses = stats["keyspace_misses"]
        hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
        
        return {
            "memory_used": memory_info["used_memory_human"],
            "hit_rate": f"{hit_rate:.2%}",
            "hits": hits,
            "misses": misses
        }