from fastapi import APIRouter, HTTPException, Query
from fastapi.templating import Jinja2Templates
from aiohttp import ClientSession
from collections import defaultdict
from typing import List, Dict, Optional
import logging
import asyncio

from src.core.config.config import frontend_root
from src.utils.BookDownloader import downloader


router = APIRouter(prefix='/foreign')
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory=frontend_root)

@router.post('/mass_download')
async def mass_download_books(
    list_titles: List[Dict] = [{'title':'Fulgrim'}],
    preferred_formats: List[str] = Query(['txt', 'pdf', 'epub', 'Text PDF', 'JSON', 'chOCR', 'XML'], description="Order of format preference"),
    language: str = Query('eng', description="Filter by language")
):
    """
    Mass download endpoint with configurable formats.
    
    Example request body:
    [
        {"title": "Fulgrim", "author": "Graham McNeill"},
        {"title": "Dune", "author": "Frank Herbert"}
    ]
    """
    # Update preferences per request
    downloader.format_priority = preferred_formats
    downloader.default_language = language.lower()

    async with ClientSession() as session:
        # Add language to all queries
        queries = [{**item, "language": language} for item in list_titles]
        tasks = [downloader.fetch_books(session, item) for item in queries]
        results = await asyncio.gather(*tasks)
        
        # Compile results
        response = {
            "request_config": {
                "preferred_formats": preferred_formats,
                "language": language
            },
            "results": [],
            "summary": {
                "total_requests": len(list_titles),
                "successful": 0,
                "failed": 0,
                "books_found": 0
            }
        }

        for result in results:
            if result.get('status') == 'success':
                response['summary']['successful'] += 1
                response['summary']['books_found'] += len(result['books'])
            else:
                response['summary']['failed'] += 1
            response['results'].append(result)

        return response