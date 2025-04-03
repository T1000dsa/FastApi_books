from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import asyncio
from fastapi import UploadFile, File, Form
import os
from uuid import uuid4
import logging


from src.menu import menu
from src.users.autentification import securityAuthx
from src.core.utils import get_list, book_process
from src.database_data.db_orm import (create_data, drop_object, insert_data, update_data, select_data_tag, select_data_book)
from src.core.schemes import BookModelPydantic, TagsModelPydantic
from src.core.config import max_file_size, media_root


router = APIRouter(prefix='/action')
logger = logging.getLogger(__name__)
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
    

@router.delete('/delete/book/{book_id}', tags=['books'])
async def drop_db_data_book(book_id:int):
    await drop_object(BookModelPydantic, drop_id=book_id)
    return {'msg':'Book was deleted'}


@router.delete('/delete/tag', tags=['tags'])
async def drop_db_data_tag(id:int=None):
    await drop_object(TagsModelPydantic, drop_id=id)
    return {'msg':'Tag was deleted'}

@router.put('/update/book/{book_id}', tags=['books'])
async def update_db_data_book(model:BookModelPydantic, book_id:int=None):
    await asyncio.create_task(update_data(book_id, model))
    return {'msg':'Book was updated'}


@router.put('/update/tag', tags=['tags'])
async def update_db_data_tag(model:TagsModelPydantic, id:int=None):
    task = asyncio.create_task(update_data(id, model))
    await task
    return {'msg':'Tag was updated'}

    
@router.get("/add_book", tags=['render'], dependencies=[Depends(securityAuthx.access_token_required)])
async def render_form_book(request: Request):
    data = [i.tag for i in (await get_list(choice=1).get_obj())] # All tags select. Might cause some problems in future.

    return templates.TemplateResponse(
            "book_form_index.html",  # Template name
            {
            'title':'Add Book',
            "request": request, 
            'tags':data, 
            'menu':menu
            }  # Context data
        )

@router.post("/add_book")
async def postdata_book(
        title=Form(), 
        author=Form(),
        text_hook:UploadFile=File(),
        tags:list[str]=Form(default=[])
        ):

    local = await book_process(text_hook)
    result = [i.id for i in await select_data_tag(tags)]

    insert_input = {
        "title": title, 
        "author": author,
        "text_hook":local,
        "tags":result
        }
    try:
        await insert_data(BookModelPydantic(**insert_input))
    except IntegrityError as err:
        return HTTPException(status_code=400, detail='Book with such title already exists')


    return JSONResponse({
            "status": "success",
            "message": "Book added successfully",
            "data": {
                "title": title,
                "tags": tags
            }
        }, status_code=status.HTTP_201_CREATED)

@router.get("/add_tag", tags=['render'], dependencies=[Depends(securityAuthx.access_token_required)])
async def render_form_tag(request: Request):

    return templates.TemplateResponse(
        "tag_form_index.html",  # Template name
        {
        "request": request, 
        'menu':menu,
        }  # Context data
    )


@router.post("/add_tag", tags=['render'])
async def postdata_tag(request:Request,
        tag=Form(), 
        ):
    insert = {
        'tag':tag, 
        'books':[]
    }

    try:
        await insert_data(TagsModelPydantic(**insert))
    except IntegrityError as err:
        logger.debug(err)
        return HTTPException(status_code=400, detail='There is already such tag in database.')
    
    return templates.TemplateResponse(
        "tag_form_index.html",  # Template name
        {
        "request": request, 
        'menu':menu,
        }  # Context data
    )


@router.delete('/delete', tags=['init'])
async def delete_all():
    task = asyncio.create_task(drop_object())
    await task
    return {'msg':'Data was deleted'}

@router.post('/edit_book/{book_id}')
async def update_book_render(
    request:Request,
    book_id:int):

    book_obj = await select_data_book(book_id)

    return templates.TemplateResponse(
        "book_edit.html",  # Template name
        {
        "request": request, 
        'menu':menu,
        'book':book_obj
        }  # Context data
    )


@router.post("/edit_book_complete/{book_id}")
async def update_book(
    request: Request,
    book_id: int,
    title: str = Form(...),
    author: str = Form(...),
    text_hook: UploadFile = File(None),
    tags: list[str] = Form([])
):
    try:
            book = await select_data_book(book_id)
            if not book:
                raise HTTPException(404, "Book not found")
            
            if text_hook.filename:
                text_path = await book_process(text_hook)
            else:
                text_path = book.text_hook
            
            insert = {
                "title":title,
                "author":author,
                "text_hook":text_path,
                "tags":tags

            }   
            
            result = await update_data(book_id, BookModelPydantic(**insert))
            logger.debug(result.title)
            return RedirectResponse(f"/book/{book_id}", status_code=303)
            
    except Exception as e:
        raise HTTPException(400, str(e))
    


@router.get('/delete_book/{book_id}')
async def delete_book_id(request:Request, book_id:int):
    book = await select_data_book(book_id)
    
    return templates.TemplateResponse(
        "delete_book.html",
        {
        "request": request, 
        'menu':menu,
        'book':book
        }
    )

    
@router.post('/delete_book_confirm/{book_id}')
async def delete_book_id(book_id:int):

    result = await drop_db_data_book(book_id)

    return RedirectResponse(f"/", status_code=303)
