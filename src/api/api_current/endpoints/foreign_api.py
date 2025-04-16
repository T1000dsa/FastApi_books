from fastapi import APIRouter, HTTPException
from typing import Optional, List
import logging

from src.utils.BookDownloader import BookLoader

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/download-books/")
async def download_books(
    title: Optional[str] = None,
    author: Optional[str] = None,
    limit: int = 10
):
    """
    Download books by title/author or random selection.
    Returns book data including download URLs and registers in DB.
    """
    new_session_book_load = BookLoader(title, author, limit)
    data = await new_session_book_load.provide_books()
    logger.debug(len(data))

    return data

    