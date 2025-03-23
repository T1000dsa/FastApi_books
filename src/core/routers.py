from fastapi import APIRouter, Request, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse ,RedirectResponse
from src.database_data.db_orm import create_data, drop_object, insert_data, update_data, output_data, select_data_book
from src.core.schemes import BookModelPydantic, TagsModelPydantic
from fastapi.templating import Jinja2Templates
from src.core.services import TextLoad
from src.menu import menu
from src.users.autentification import securityAuthx
from src.core.utils import get_list, get_select

import logging

router = APIRouter()


logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="frontend/templates")
logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

@router.get("/", response_class=HTMLResponse, tags=['root'])
async def read_root(request: Request):
    response = Response()
    token = request.cookies.get('access_token')
    #data = (await refresh_token(token))

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

    content = TextLoad(data)
    return templates.TemplateResponse(
        "get_book.html",  # Template name
        {
        "request": request, 
        "title": data.title, 
        'description':'Good reading!',
        'content':content.push_text(), 
        'menu':menu
        }  # Context data
    )