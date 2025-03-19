from fastapi.responses import FileResponse
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from src.database_data.db_orm import create_data, drop_object, insert_data, update_data, output_data, select_data_book
from src.init_data.models import BookModelPydantic, TagsModelPydantic
from fastapi.templating import Jinja2Templates
from src.database_data.models import BookModelOrm, TagsModelOrm
from src.core.services import TextLoad

import asyncio
from fastapi import UploadFile, File, Form
import logging
import os
from uuid import uuid4
from datetime import datetime

router = APIRouter()

menu = [
    {'title':'Docs', 'url':'/docs'},
    {'title':'Home', 'url':'/'},
    {'title':'Add Book', 'url':'/add_book'},
    {'title':'Add Tag', 'url':'/add_tag'},
    {'title':'Get Books', 'url':'/books'},
]

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="frontend/templates")
logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html",  # Template name
        {
            "request": request, 
            "title": "Home",
            "content": "Greetings! Choice the book and make you comfortable here!", 
            'menu':menu
            }  # Context data
    )

@router.get('/action/get_list/{choice}', tags=['get'])
async def get_list(choice:int):
    if isinstance(choice, int):
        result = await output_data(choice)
        return {'msg':'Data was gaved', 'data':result}
    return {'msg':'invalid choice'}


@router.post('/action/create', tags=['init'])
async def create_db_data():
    await drop_object()
    await create_data()
    return {'msg':'Tables were created'}

@router.post('/action/insert/book', tags=['books'])
async def insert_db_data_book(model:BookModelPydantic):
    await insert_data(model)
    return {'msg':'Data was inserted'}

@router.get('/action/select/book', tags=['books'])
async def select_db_data_book(data_id):
    result = await select_data_book(data=data_id)
    return {'msg':'Data was inserted', 'data':result}

@router.post('/action/insert/tag', tags=['tags'])
async def insert_db_data_tag(model:TagsModelPydantic):
    await insert_data(model)
    return {'msg':'Data was inserted'}
    

@router.delete('/action/delete/book', tags=['books'])
async def drop_db_data_book(id:int=None):
    await drop_object(BookModelPydantic, drop_id=id)
    return {'msg':'Book was deleted'}


@router.delete('/action/delete/tag', tags=['tags'])
async def drop_db_data_tag(id:int=None):
    await drop_object(TagsModelPydantic, drop_id=id)
    return {'msg':'Tag was deleted'}

@router.put('/action/update/book', tags=['books'])
async def update_db_data_book(model:BookModelPydantic, id:int=None):
    await asyncio.create_task(update_data(id, model))
    return {'msg':'Book was updated'}


@router.put('/action/update/tag', tags=['tags'])
async def update_db_data_tag(model:TagsModelPydantic, id:int=None):
    task = asyncio.create_task(update_data(id, model))
    await task
    return {'msg':'Tag was updated'}


@router.post("/action/insert/book/form")
async def postdata_book(request:Request,
        title=Form(), 
        author=Form(),
        text_hook:UploadFile=File(),
        tags_book=Form(default='')
        ):
    
    media_root = os.path.join(os.getcwd(), "src", "media_root", datetime.now().date().strftime('%Y/%m/%d'))
    os.makedirs(media_root, exist_ok=True)
    noise = uuid4().int

    if ".." in text_hook.filename or "/" in text_hook.filename:
        raise HTTPException(status_code=400, detail="Invalid file name")

# Limit file size (e.g., 10 MB)
    max_file_size = 10 * 1024 * 1024  # 10 MB
    if text_hook.size > max_file_size:
        raise HTTPException(status_code=400, detail="File size exceeds the limit")

        # Save the file
    local = os.path.join(media_root, f'{noise}'+text_hook.filename)
    print(local)
    with open(local, 'wb') as filex:
        filex.write(await text_hook.read())

    insert_input = {
        "title": title, 
        "author": author,
        "text_hook":local,
        "tags":tags_book.split(',') if tags_book else []
        }
    await insert_data(BookModelPydantic(**insert_input))
    return templates.TemplateResponse(
        "book_form_index.html",  # Template name
        {
        "request": request, 
        "title": "Add Book",
        'menu':menu
        }  # Context data
    )

@router.post("/action/insert/tag/form")
async def postdata_tag(request:Request,
        tag=Form(), 
        book_tags=Form(default='')
        ):
    
    insert_input = {
        "tag": tag, 
        "books":book_tags.split(',') if book_tags else []
        }
    print(insert_input)
    await insert_data(TagsModelPydantic(**insert_input))
    
    return templates.TemplateResponse(
        "tag_form_index.html",  # Template name
        {
        "request": request, 
        "title": "Add Book",
        'menu':menu
        }  # Context data
    )
    
@router.get("/add_book", tags=['get'])
async def render_form_book(request: Request):
    data = [i.tag for i in (await get_list(choice=1))['data']] # All tags select. Might cause some problems in future.

    return templates.TemplateResponse(
        "book_form_index.html",  # Template name
        {
        "request": request, 
        "title": "Add Book", 
        'tags':data, 
        'menu':menu
        }  # Context data
    )

@router.get("/add_tag", tags=['get'])
async def render_form_tag(request: Request):
    data = [i.title for i in (await get_list(choice=0))['data']] # All books select. Might cause some problems in future.

    return templates.TemplateResponse(
        "tag_form_index.html",  # Template name
        {
        "request": request, 
        "title": "Add Tag", 
        'books':data, 
        'menu':menu
        }  # Context data
    )

@router.get("/books", tags=['get'])
async def get_books(request: Request):
    data = (await get_list(choice=0))['data'] # All books select. Might cause some problems in future.
    return templates.TemplateResponse(
        "get_books.html",  # Template name
        {
        "request": request, 
        "title": "Get books", 
        'description':'Choice the book!',
        'books':data, 
        'menu':menu
        }  # Context data
    )

@router.get("/book/{book_id}", tags=['get'])
async def get_book(request: Request, book_id: int):
    data = (await select_db_data_book(book_id))['data']
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

@router.delete('/action/update/')
async def delete_all():
    task = asyncio.create_task(drop_object())
    await task
    return {'msg':'Data was deleted'}
