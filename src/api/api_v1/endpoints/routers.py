from fastapi import APIRouter, Request, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse ,RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import logging
import os

from src.core.services import TextLoad
from src.menu import menu
from src.core.utils import get_list, get_select
from src.database_data.db_orm import select_data_tag
from src.core.config import pagination_pages, frontend_root
from src.database_data.db_helper import db_helper



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
            }
    )
    
    return response

@router.get('/books', tags=['books'])
async def get_books(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request:Request):
    get_list_data = get_list(choice=0, session=session)
    books_data = list(await get_list_data.get_obj())
    pag_data = int(len(books_data) / pagination_pages)
    current = 1

    return templates.TemplateResponse(
        "get_books.html",  # Template name
        {
        "request": request, 
        'description':'Choice the book!',
        'books':books_data,
        'menu':menu,
        'per_page':pag_data,
        'page':current,
        }
    )

@router.get('/tags', tags=['tags'])
async def get_tags(session:Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    get_list_data = get_list(choice=1, session=session)
    tags_data = (await get_list_data.get_obj())
    return {'msg':'Data was gaved', 'data':tags_data}


@router.get("/book/{book_id}", tags=['books'])
async def get_book(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request: Request, 
    book_id: int
    ):

    get_select_data = get_select(select_id=book_id, session=session)
    book_data = (await get_select_data.get_obj())
    data = book_data
    res = await select_data_tag(session, data)
    
    content = TextLoad(data)
    return templates.TemplateResponse(
        "get_book.html",  # Template name
        {
        "request": request, 
        'description':'Good reading!',
        'content':content.push_text(), 
        'menu':menu,
        'tags':[i.tag for i in res],
        'book':data
        }  # Context data
    )

users = [1, 2, 3, 4, 5, 6, 7, 8 , 9 ]
@router.get('/test')
async def test() -> Page[int]:
    return paginate(users)
