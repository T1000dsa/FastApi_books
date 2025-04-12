from elasticsearch import AsyncElasticsearch

from src.core.config.config import settings


search_engine = AsyncElasticsearch(
    hosts=[settings.elastic.host],
    http_auth=(
        settings.elastic.user, 
        settings.elastic.password
    )
)