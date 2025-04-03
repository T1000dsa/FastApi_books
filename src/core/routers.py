from fastapi import APIRouter, Request, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse ,RedirectResponse
from fastapi.templating import Jinja2Templates
import logging

from src.core.services import TextLoad
from src.menu import menu
from src.core.utils import get_list, get_select
from src.database_data.db_orm import select_data_tag


router = APIRouter()


templates = Jinja2Templates(directory="frontend/templates")
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse, tags=['root'])
async def read_root(request: Request):
    response = Response()

    response = templates.TemplateResponse(
        "index.html",  # Template name
        {
            "request": request, 
            "content": "Greetings! Choice the book and make you comfortable here!", 
            'menu':menu,
            }  # Context data
    )
    
    return response

@router.get('/books', tags=['books'])
async def get_books(request:Request):
    get_list_data = get_list(choice=0)
    books_data = (await get_list_data.get_obj())
    return templates.TemplateResponse(
        "get_books.html",  # Template name
        {
        "request": request, 
        'description':'Choice the book!',
        'books':books_data,
        'menu':menu
        }  # Context data
    )

@router.get('/tags', tags=['tags'])
async def get_tags():
    get_list_data = get_list(choice=1)
    tags_data = (await get_list_data.get_obj())
    return {'msg':'Data was gaved', 'data':tags_data}


@router.get("/book/{book_id}", tags=['books'])
async def get_book(request: Request, book_id: int):
    get_select_data = get_select(select_id=book_id)
    book_data = (await get_select_data.get_obj())
    data = book_data
    res = await select_data_tag(data)
    
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