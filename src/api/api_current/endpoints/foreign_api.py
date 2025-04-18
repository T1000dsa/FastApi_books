from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from fastapi import UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from aiohttp import ClientSession
from datetime import datetime
import io
import asyncio 
import logging

from src.utils.BookDownloader import BookLoader
from src.api.api_current.endpoints.routers_core import postdata_book
from src.utils.db_utils import text_process_direct
from src.core.services.database.db_helper import db_helper
from src.api.api_current.orm.db_orm import (select_data_book)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/download-books/")
async def download_books(
    title: Optional[str] = None,
    limit: int = 10,
    db_session: AsyncSession = Depends(db_helper.session_getter),
    overwrite: bool = False
):
    try:
        book_loader = BookLoader(title, limit)
        data = await book_loader.provide_books()
        
        # Track processing state
        processed_books = set()  # Track titles we've already handled
        results = {
            "successful": [],
            "skipped_existing": [],
            "failed": []
        }

        async with ClientSession() as http_session:
            for book in data:
                # Skip if we've already processed this title
                if book['title'] in processed_books:
                    continue
                    
                processed_books.add(book['title'])
                
                await asyncio.sleep(1)  # Rate limiting

                if not book.get('formats') or not book['formats'][0]:
                    results["failed"].append(book['title'])
                    continue
                    
                try:
                    # Check if book exists (unless overwrite is True)
                    if not overwrite:
                        existing = await select_data_book(db_session, book['title'])
                        if existing:
                            results["skipped_existing"].append(book['title'])
                            continue

                    # Download and process book
                    async with http_session.get(book['formats'][0]) as response:
                        if response.status != 200:
                            results["failed"].append(book['title'])
                            continue
                            
                        text_content = await response.text()
                        processed_text = await text_process_direct(text_content)
                        
                        file_obj = io.BytesIO(processed_text.encode('utf-8'))
                        upload_file = UploadFile(
                            filename=f"{book['title']}",
                            file=file_obj,
                            size=len(processed_text))
                        await upload_file.seek(0)
                        
                        try:
                            await postdata_book(
                                title=book['title'], 
                                author=book['author'],
                                text_hook=upload_file,
                                year=datetime(1900, 1, 1),
                                tags=[],
                                session=db_session
                            )
                            results["successful"].append(book['title'])
                        except HTTPException as e:
                            if e.status_code == 400 and "already exists" in str(e.detail):
                                results["skipped_existing"].append(book['title'])
                            else:
                                results["failed"].append(book['title'])
                        finally:
                            await upload_file.close()
                            
                except Exception as e:
                    logger.error(f"Error processing book {book.get('title')}: {str(e)}")
                    results["failed"].append(book['title'])

        return {
            "status": "completed",
            "stats": {
                "requested": len(data),
                "successful": len(results["successful"]),
                "skipped_existing": len(results["skipped_existing"]),
                "failed": len(results["failed"])
            },
            "details": results,
            "unique_books_processed": len(processed_books)
        }
        
    except Exception as e:
        logger.error(f"Error in download-books: {str(e)}")
        raise HTTPException(500, "Internal server error during book download")