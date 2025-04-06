from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, File, Form
from typing import Annotated
import logging

from src.core.utils import get_list, book_process
from src.api.api_v1.orm.db_orm import ( drop_object, insert_data, update_data, select_data_tag, select_data_book)
from src.core.schemes import BookModelPydantic, TagsModelPydantic
from src.core.services import TextLoad
from src.core.database.db_helper import db_helper
from src.core.config import frontend_root
from src.api.api_v1.auth.config import securityAuthx
from src.core.config import menu
from src.core.urls import choice_from_menu


router = APIRouter(prefix='/action')
logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory=frontend_root)

@router.post('/create', tags=['init'])
async def create_db_data(session:Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    await drop_object(session)
    return {'msg':'Tables were created'}

@router.post('/insert/book', tags=['books'])
async def insert_db_data_book(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    model:BookModelPydantic):
    await insert_data(session, model)
    return {'msg':'Data was inserted'}

@router.post('/insert/tag', tags=['tags'])
async def insert_db_data_tag(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    model:TagsModelPydantic):
    await insert_data(session, model)
    return {'msg':'Data was inserted'}
    

@router.delete('/delete/book/{book_id}', tags=['books'])
async def drop_db_data_book(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    book_id:int):
    await drop_object(session, BookModelPydantic, drop_id=book_id)
    return {'msg':'Book was deleted'}


@router.delete('/delete/tag', tags=['tags'])
async def drop_db_data_tag(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    id:int=None):
    await drop_object(session, TagsModelPydantic, drop_id=id)
    return {'msg':'Tag was deleted'}

@router.put('/update/book/{book_id}', tags=['books'])
async def update_db_data_book(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    model:BookModelPydantic, book_id:int=None):
    await update_data(session, book_id, model)
    return {'msg':'Book was updated'}


@router.put('/update/tag', tags=['tags'])
async def update_db_data_tag(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    model:TagsModelPydantic, id:int=None
    ):
    task = update_data(session, id, model)
    await task
    return {'msg':'Tag was updated'}

    
@router.get("/add_book", tags=['render'], dependencies=[Depends(securityAuthx.access_token_required)])
async def render_form_book(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request: Request
    ):
    data = [i.tag for i in (await get_list(choice=1, session=session).get_obj())] # All tags select. Might cause some problems in future.

    return templates.TemplateResponse(
            "book_form_index.html",  # Template name
            {
            'title':'Add Book',
            "request": request, 
            'tags':data, 
            'menu':menu,
            "menu_data":choice_from_menu
            }  # Context data
        )

@router.post("/add_book")
async def postdata_book(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    title=Form(), 
    author=Form(),
    text_hook:UploadFile=File(),
    tags:list[str]=Form(default=[])
        ):

    local = await book_process(text_hook)
    result = [i.id for i in await select_data_tag(session, tags)]

    insert_input = {
        "title": title, 
        "author": author,
        "text_hook":local,
        "tags":result,
        "menu_data":choice_from_menu
        }
    try:
        await insert_data(session, BookModelPydantic(**insert_input))
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
        "menu_data":choice_from_menu
        }  # Context data
    )


@router.post("/add_tag", tags=['render'])
async def postdata_tag(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request:Request,
        tag=Form(), 
        ):
    insert = {
        'tag':tag, 
        'books':[]
    }

    try:
        await insert_data(session, TagsModelPydantic(**insert))
    except IntegrityError as err:
        logger.debug(err)
        return HTTPException(status_code=400, detail='There is already such tag in database.')
    
    return templates.TemplateResponse(
        "tag_form_index.html",  # Template name
        {
        "request": request, 
        'menu':menu,
        "menu_data":choice_from_menu
        }  # Context data
    )


@router.delete('/delete', tags=['init'])
async def delete_all(session:Annotated[AsyncSession, Depends(db_helper.session_getter)]):
    await drop_object(session)
    return {'msg':'Data was deleted'}

@router.post('/edit_book/{book_id}')
async def update_book_render(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request:Request,
    book_id:int):

    book_obj = await select_data_book(session, book_id)

    return templates.TemplateResponse(
        "book_edit.html",  # Template name
        {
        "request": request, 
        'menu':menu,
        'book':book_obj,
        "menu_data":choice_from_menu
        }  # Context data
    )


@router.post("/edit_book_complete/{book_id}")
async def update_book(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    book_id: int,
    title: str = Form(...),
    author: str = Form(...),
    text_hook: UploadFile = File(None),
    tags: list[str] = Form([])
):
    try:
            book = await select_data_book(session, book_id)
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
                "tags":tags,
                "menu_data":choice_from_menu
            }   
            
            result = await update_data(session, book_id, BookModelPydantic(**insert))
            logger.debug(result.title)
            return RedirectResponse(f"/book/{book_id}", status_code=303)
            
    except Exception as e:
        raise HTTPException(400, str(e))
    

@router.get('/delete_book/{book_id}')
async def delete_book_id(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request:Request, 
    book_id:int):

    book = await select_data_book(session, book_id)
    pull_len = TextLoad(book)
    text_data = pull_len.push_text()

    return templates.TemplateResponse(
        "delete_book.html",
        {
        "request": request, 
        'menu':menu,
        'book':book,
        'lost':len(text_data),
        "menu_data":choice_from_menu
        }
    )

    
@router.post('/delete_book_confirm/{book_id}')
async def delete_book_id(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    book_id:int):

    await drop_db_data_book(session, book_id)
    return RedirectResponse(f"/", status_code=303)