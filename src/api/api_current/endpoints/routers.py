from fastapi import APIRouter, Request, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import logging

from src.utils.db_utils import get_list, get_select
from src.api.api_current.orm.db_orm import select_data_tag
from src.core.config.config import frontend_root
from src.core.services.database.db_helper import db_helper
from src.core.config.config import menu
from src.core.urls import choice_from_menu
from src.core.services.cache.books_cache import BookCacheService
from src.api.api_current.endpoints.services.paginator_helper import get_paginated_books
from src.api.api_current.auth.config import securityAuthx
from src.utils.Pagination_text import split_text_into_pages
from src.core.services.task_queue.emal_queue import send_email_task
from src.utils.User_data import gather_user_data_from_cookies


router = APIRouter()

templates = Jinja2Templates(directory=frontend_root)
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse, tags=['root'])
async def read_root(request: Request):
    response = Response()

    response = templates.TemplateResponse(
        'index.html',  # Template name
        {
            "request": request, 
            "content": "Greetings! Choice the book and make you comfortable here!", 
            'menu':menu,
            "menu_data":choice_from_menu
            }
    )
    return response

@router.get("/books", dependencies=[Depends(securityAuthx.access_token_required)])
@router.get("/books/{page}", dependencies=[Depends(securityAuthx.access_token_required)])
async def get_books(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_getter),
    page: int = 1
):
    
    try:
        # Proper pagination query
        data, paginated_books = await get_paginated_books(session, page)
        
        return templates.TemplateResponse(
        "get_books.html",
        {
        "request": request, 
        'description':'Choice the book!',
        'menu':menu,
        "books":paginated_books,
        "data":data,
        "menu_data":choice_from_menu,
        }
    )
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        raise HTTPException(status_code=500, detail="Error fetching books")

@router.get('/tags', tags=['tags'])
async def get_tags(session:Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    get_list_data = get_list(choice=1, session=session)
    tags_data = (await get_list_data.get_obj())
    return {'msg':'Data was gaved', 'data':tags_data}

@router.get("/books/{page}/book/{book_title}", tags=['books'], dependencies=[Depends(securityAuthx.access_token_required)])
@router.get("/books/{page}/book/{book_title}/{book_page}", tags=['books'], dependencies=[Depends(securityAuthx.access_token_required)])
async def get_book(
    session: Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request: Request, 
    book_title: str,
    page:int,
    book_page:int=1
):
    # Get book data
    get_select_data = get_select(select_id=book_title, session=session)
    book_data = await get_select_data.get_obj()

    content = await BookCacheService.get_book_text(book_data)
    pages_pet_text, count = split_text_into_pages(content)

    # Get Page data
    data, _ = await get_paginated_books(session)
    data['current_page'] = page
    
    data_book = {
        'book_page':book_page,
        'book_page_all':count
    }

    
    # Log cache stats
    await BookCacheService.get_cache_stats()

    # Get tags
    res = await select_data_tag(session, book_data)

    user_data = await gather_user_data_from_cookies(request=request)

    try:

        await send_email_task(
            to_email='',
            subject=user_data.sub,  # Assuming you have user auth
            body=book_title
        )
    except(Exception) as err:
        logger.debug(err)
    
    return templates.TemplateResponse(
        "get_book.html",
        {
            "request": request,
            "description": "Good reading!",
            "content": pages_pet_text[book_page-1],#content,
            "menu": menu,
            "tags": [i.tag for i in res],
            "book": book_data,
            "menu_data": choice_from_menu,
            "data":data,
            "data_book":data_book
        }
    )