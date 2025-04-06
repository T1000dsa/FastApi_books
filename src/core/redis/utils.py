import logging
import gzip

from src.core.config import menu, redis, settings
from src.core.database.models.models import BookModelOrm
from src.core.services import TextLoad


logger = logging.getLogger(__name__)

async def cached(book_data:BookModelOrm) -> str:
    '''Takes BookModelOrm obj and returns text'''
    cached_text = await redis.get(book_data.text_hook)
    logger.info(f'In cache: {bool(cached_text)}')

    memory_info = await redis.info("MEMORY")
    logger.info(f"Memory used: {memory_info['used_memory_human']}")

    stats = await redis.info("STATS")
    hits = stats["keyspace_hits"]
    misses = stats["keyspace_misses"]
    logger.info(f'{hits=} {misses=}')
    hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
    logger.info(f"Cache hit rate: {hit_rate:.2%}")

    if cached_text:
        try:
            # Try decompressing first (for new cached items)
            content = gzip.decompress(cached_text).decode()
        except gzip.BadGzipFile:
            # Fall back to raw text (for old cached items)
            content = cached_text.decode()
    else:
        text_load = TextLoad(book_data)
        content = text_load.push_text()
        # Compress before storing in Redis
        compressed = gzip.compress(content.encode())
        await redis.set(book_data.text_hook, compressed, ex=settings.cache.REDIS_CACHE_TTL_BOOKS)
    return content