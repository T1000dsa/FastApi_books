from fastapi import APIRouter, Request, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
import logging

from src.core.services import TextLoad
from src.core.utils import get_list, get_select
from src.api.api_v1.orm.db_orm import select_data_tag, paginator, output_data
from src.core.config import per_page, frontend_root
from src.core.database.db_helper import db_helper
from src.api.api_v1.auth.config import securityAuthx
from src.core.config import menu
from src.core.urls import choice_from_menu


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

@router.get("/books/{page}", dependencies=[Depends(securityAuthx.access_token_required)])
async def get_books(
    request:Request,
    page: int=1,
    session: AsyncSession = Depends(db_helper.session_getter)

):
    try:
        # Proper pagination query
        paginated_books = await paginator(session, page)
        all_books = await output_data(session)
        lenght_data = (len(all_books) / per_page)

        if str(lenght_data).split('.')[1] != '0':
            lenght_data = int(lenght_data+1)


        data = {
            'current_page':page,
            'total_pages':lenght_data
        }
        
        return templates.TemplateResponse(
        "get_books.html",  # Template name
        {
        "request": request, 
        'description':'Good reading!',
        'menu':menu,
        "books":paginated_books,
        "data":data,
        "menu_data":choice_from_menu
        }  # Context data
    )
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        raise HTTPException(status_code=500, detail="Error fetching books")

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
        'book':data,
        "menu_data":choice_from_menu
        }  # Context data
    )
