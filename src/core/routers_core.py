from fastapi import APIRouter, Depends
from src.database_data.db_orm import create_data, drop_object, insert_data, update_data, output_data, select_data_book
from src.core.schemes import BookModelPydantic, TagsModelPydantic
from fastapi import APIRouter, Request, HTTPException
from src.database_data.db_orm import create_data, drop_object, insert_data, update_data, output_data, select_data_book
from src.core.schemes import BookModelPydantic, TagsModelPydantic
from fastapi.templating import Jinja2Templates
from src.menu import menu
from src.users.autentification import securityAuthx
from src.core.utils import get_list


import asyncio
from fastapi import UploadFile, File, Form
import os
from uuid import uuid4
from src.core.config import max_file_size, media_root


router = APIRouter(prefix='/action')

templates = Jinja2Templates(directory="frontend/templates")

@router.post('/create', tags=['init'])
async def create_db_data():
    await drop_object()
    await create_data()
    return {'msg':'Tables were created'}

@router.post('/insert/book', tags=['books'])
async def insert_db_data_book(model:BookModelPydantic):
    await insert_data(model)
    return {'msg':'Data was inserted'}

@router.post('/insert/tag', tags=['tags'])
async def insert_db_data_tag(model:TagsModelPydantic):
    await insert_data(model)
    return {'msg':'Data was inserted'}
    

@router.delete('/delete/book', tags=['books'])
async def drop_db_data_book(id:int=None):
    await drop_object(BookModelPydantic, drop_id=id)
    return {'msg':'Book was deleted'}


@router.delete('/delete/tag', tags=['tags'])
async def drop_db_data_tag(id:int=None):
    await drop_object(TagsModelPydantic, drop_id=id)
    return {'msg':'Tag was deleted'}

@router.put('/update/book', tags=['books'])
async def update_db_data_book(model:BookModelPydantic, id:int=None):
    await asyncio.create_task(update_data(id, model))
    return {'msg':'Book was updated'}


@router.put('/update/tag', tags=['tags'])
async def update_db_data_tag(model:TagsModelPydantic, id:int=None):
    task = asyncio.create_task(update_data(id, model))
    await task
    return {'msg':'Tag was updated'}

@router.post("/insert/book/form", tags=['render'])
async def postdata_book(request:Request,
        title=Form(), 
        author=Form(),
        text_hook:UploadFile=File(),
        tags_book=Form(default='')
        ):

    noise = uuid4().int

    if ".." in text_hook.filename or "/" in text_hook.filename:
        raise HTTPException(status_code=400, detail="Invalid file name")

    if text_hook.size > max_file_size:
        raise HTTPException(status_code=400, detail="File size exceeds the limit")

        # Save the file
    local = os.path.join(media_root, f'{noise}'+text_hook.filename)
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

@router.post("/insert/tag/form", tags=['render'])
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
        'menu':menu
        }  # Context data
    )
    
@router.get("/add_book", tags=['render']) #, dependencies=[Depends(securityAuthx.access_token_required)]
async def render_form_book(request: Request):
    data = [i.tag for i in (await get_list(choice=1).get_obj())] # All tags select. Might cause some problems in future.

    return templates.TemplateResponse(
            "book_form_index.html",  # Template name
            {
            "request": request, 
            'tags':data, 
            'menu':menu
            }  # Context data
        )

@router.get("/add_tag", tags=['render']) #, dependencies=[Depends(securityAuthx.access_token_required)]
async def render_form_tag(request: Request):
    get_list_data = get_list(choice=0)
    books_data = (await get_list_data.get_obj())
    data = [i.title for i in books_data] # All books select. Might cause some problems in future.

    return templates.TemplateResponse(
        "tag_form_index.html",  # Template name
        {
        "request": request, 
        'books':data, 
        'menu':menu
        }  # Context data
    )


@router.delete('/delete', tags=['init'])
async def delete_all():
    task = asyncio.create_task(drop_object())
    await task
    return {'msg':'Data was deleted'}

