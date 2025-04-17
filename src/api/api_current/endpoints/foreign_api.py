from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from fastapi import UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from aiohttp import ClientSession
from datetime import datetime
import io
import logging

from src.utils.BookDownloader import BookLoader
from src.api.api_current.endpoints.routers_core import postdata_book
from src.utils.db_utils import text_process_direct
from src.core.services.database.db_helper import db_helper

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/download-books/")
async def download_books(
    title: Optional[str] = None,
    limit: int = 10,
    db_session: AsyncSession = Depends(db_helper.session_getter)
):
    try:
        new_session_book_load = BookLoader(title, limit)
        data = await new_session_book_load.provide_books()
        
        async with ClientSession() as http_session:
            for book in data:
                if not book.get('formats') or not book['formats'][0]:
                    continue
                    
                try:
                    async with http_session.get(url=book['formats'][0]) as response:
                        if response.status != 200:
                            continue
                            
                        text_content = await response.text()
                        processed_text = await text_process_direct(text_content)
                        
                        # Create an in-memory file-like object
                        file_obj = io.BytesIO(processed_text.encode('utf-8'))
                        
                        # Create a proper UploadFile instance
                        upload_file = UploadFile(
                            filename=f"{book['title']}.txt",
                            file=file_obj,
                            size=len(processed_text)
                        )
                        
                        # Reset file pointer to start (important!)
                        await upload_file.seek(0)
                        
                        await postdata_book(
                            title=book['title'], 
                            author=book['author'],
                            text_hook=upload_file,
                            year=datetime(1900, 1, 1),
                            tags=[],
                            session=db_session
                        )
                except Exception as e:
                    logger.error(f"Error processing book {book.get('title')}: {str(e)}")
                    continue

        return data
    except Exception as e:
        logger.error(f"Error in download-books: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during book download"
        )