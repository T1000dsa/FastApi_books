from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict
import logging
import asyncio
import os

from src.core.config.config import frontend_root
from src.utils.BookDownloader import BookDownloader  # Import your BookDownloader class

router = APIRouter(prefix='/foreign')
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory=frontend_root)

@router.post('/mass_download')
async def mass_download_books(
    list_titles: List[Dict] = [
        {"title": "1984"},
        {"title": "Fulgrim"},
        {"title": "Black tower"},
        {"title": "The Brotherhood of the Ring"},
        {"title": "the flight of the eisenstein"},
        {"title": "Fahrenheit 451"},
        {"title": "Xenos", "author": "Dan Abnett"}
    ],
    language: str = Query('eng', description="Filter by language")
):
    """
    Mass download endpoint using BookDownloader's session management
    """
    async with BookDownloader(
        username='marselkhasanov1234567890@gmail.com',  # Get credentials from environment
        password='fsdfdsfu90dasy0fu9earyfa8w9rya8w977r9war90w37r9w79r'
    ) as downloader:
        downloader.default_language = language.lower()

        # Normalize search queries
        queries = []
        for item in list_titles:
            normalized_item = {
                "title": item["title"].title() if isinstance(item.get("title"), str) else None,
                "author": item["author"].title() if isinstance(item.get("author"), str) else None,
                "language": language
            }
            queries.append({k: v for k, v in normalized_item.items() if v is not None})
        logger.info(f"{queries=}")

        # Process queries with rate limiting
        results = []
        for i, query in enumerate(queries):
            if i > 0:
                await asyncio.sleep(1)  # Rate limiting
            try:
                # Call fetch_books with just the query (no session parameter)
                result = await downloader.fetch_books(query)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {query}: {str(e)}")
                results.append({"error": str(e), "item": query})

        # Compile results
        response = {
            "request_config": {
                "language": language,
                "authenticated": downloader.auth is not None,
                "normalized_queries": queries
            },
            "results": results,
            "summary": {
                "total_requests": len(list_titles),
                "successful": sum(1 for r in results if r.get('status') == 'success'),
                "failed": sum(1 for r in results if r.get('status') != 'success'),
                "books_found": sum(len(r.get('books', [])) for r in results),
                "auth_required": sum(
                    1 for r in results 
                    for b in r.get('books', []) 
                    if 'encrypted' in b.get('format', '').lower()
                )
            }
        }

        return {"response":response}
    
