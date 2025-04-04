from fastapi import (APIRouter, HTTPException, Response, Depends ,Request, Form)
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional
import logging

from src.api.api_v1.auth.user_scheme import User
from src.api.api_v1.auth.user_orm import select_data_user, insert_data, update_data, delete_data
from src.database_data.db_helper import db_helper
from src.api.api_v1.auth.config import templates_users, securityAuthx
from src.api.api_v1.auth.utils import refresh_logic
from src.core.config import (ACCESS_TYPE, REFRESH_TYPE, TOKEN_TYPE, refresh_token_expire, access_token_expire)
from src.menu import menu


router = APIRouter(tags=['auth'])

logger = logging.getLogger(__name__)

@router.get('/register')
async def register(
    request:Request,
    ):
    return templates_users.TemplateResponse(
        "users/register.html",  # Template name
        {
            "request": request,
            'menu':menu,
            'form_data': {} 

            }  # Context data
    )

@router.post('/register')
async def register_check(
        request:Request,
        session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
        username=Form(), 
        password=Form(),
        password_again=Form(),
        mail=Form(default=''),
        bio=Form(default='')
        ):
    
    form_data = {
        'username': username,
        'password': password,
        'password_again': password_again,
        'mail': mail,
        'bio': bio
    }
    
    try:
        # Create a User instance to validate the form data
        user = User(**form_data)
    except ValidationError as e:
        error_data = e.errors()[0].get('ctx').get('error')

        return templates_users.TemplateResponse(
            "users/register.html",
            {
                "request": request,
                'menu': menu,
                'error':error_data.args[0],
                'form_data': form_data 
            }
        )
    select_bool = await select_data_user(session, user)
    if select_bool == None:
        await insert_data(session, user)
    else:
        return templates_users.TemplateResponse(
        "users/register.html",  # Template name
        {
            "request": request,
            'menu':menu,
            'error':'This login already exists',
            'form_data': form_data 
            }
    )

    responce = RedirectResponse(url='/register_success')

    return responce

@router.post('/register_success')
async def reg_success(request:Request):
    return templates_users.TemplateResponse(
        "users/register_success.html",  # Template name
        {
            "request": request,
            'menu': menu
        }
    )

@router.get('/login')
async def login(request:Request):
    return templates_users.TemplateResponse(
        "users/login.html",  # Template name
        {
            "request": request,
            'menu': menu,
            'form_data':{}
        }
    )

@router.post('/login/check')
async def login_check(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request:Request,
    username=Form(), 
    password=Form()
    ):
    form_data = {
        'username':username, 
        'password':password
        }

    data = await select_data_user(session, username)
    if data is not None:
        if data.username == username and data.check_password(password):
            user_data = {'uid':str(data.id)}
            token = securityAuthx.create_access_token(**user_data).decode()
            refresh_token = securityAuthx.create_refresh_token(**user_data).decode()

            response = RedirectResponse(url="/", status_code=303) 
            
            response.set_cookie(
            key=ACCESS_TYPE,
            value=token,
            httponly=True,  # Prevent client-side JavaScript from accessing the cookie
            secure=True,     # Ensure the cookie is only sent over HTTPS
            samesite="lax"   # Prevent CSRF attacks
            )

            response.set_cookie(
            key=REFRESH_TYPE,
            value=refresh_token,
            httponly=True,  # Prevent client-side JavaScript from accessing the cookie
            secure=True,     # Ensure the cookie is only sent over HTTPS
            samesite="lax"   # Prevent CSRF attacks
            )
            return response
        
    response = RedirectResponse(url="/login", status_code=200) 
        
    return templates_users.TemplateResponse(
        "users/login.html",  # Template name
        {
            "request": request,
            'menu': menu,
            'error':'Incorrect password or username',
            "form_data":form_data
        }
    )

@router.get('/logout')
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie(ACCESS_TYPE)
    response.delete_cookie(REFRESH_TYPE)
    return response


@router.post("/refresh")
async def refresh_endpoint(
    request: Request,
    session: AsyncSession = Depends(db_helper.session_getter)
):
    """Public endpoint with DI"""
    new_token = await refresh_logic(request, session)
    if not new_token:
        raise HTTPException(status_code=401)
    
    response = Response(status_code=204)
    print(response)
    response.set_cookie(...)
    return response


@router.get("/profile")
async def user_profile(
    session:Annotated[AsyncSession, Depends(db_helper.session_getter)],
    request: Request,
    token_payload: dict = Depends(securityAuthx.access_token_required)
    ):

    user = await select_data_user(session, int(token_payload.sub))

    return templates_users.TemplateResponse(
        "users/profile.html",  # Template name
        {
            "request": request,
            'menu': menu,
            'error':'Incorrect password or username',
            "user":user,
        }
    )