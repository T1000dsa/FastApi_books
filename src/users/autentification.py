from fastapi import APIRouter, HTTPException, Response, Depends ,Request
from authx import AuthX, AuthXConfig
from src.users.user_scheme import User
from src.users.user_config import load_env
from src.users.user_orm import select_data_user, insert_data, update_data, delete_data
from fastapi.templating import Jinja2Templates
from src.menu import menu
from fastapi import UploadFile, File, Form
from authx.exceptions import JWTDecodeError

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
import jwt

from pydantic import ValidationError

router = APIRouter()
templates_users = Jinja2Templates(directory="frontend/templates")
config = AuthXConfig(
    JWT_SECRET_KEY=load_env.JWT_SECRET_KEY,
    JWT_ACCESS_COOKIE_NAME = load_env.JWT_ACCESS_COOKIE_NAME,
    JWT_TOKEN_LOCATION=["cookies"]
    
)

security = AuthX(config=config)



@router.get('/register')
async def register(request:Request):
    return templates_users.TemplateResponse(
        "users/register.html",  # Template name
        {
            "request": request,
            'menu':menu,

            }  # Context data
    )

@router.post('/register/check')
async def register_check(request:Request,
        username=Form(), 
        password=Form(),
        password_again=Form(),
        mail=Form(default=''),
        bio=Form(default='')
        ):
    
    try:
        # Create a User instance to validate the form data
        user = User(
            username=username,
            password=password,
            password_again=password_again,
            mail=mail,
            bio=bio
        )
    except ValidationError as e:
        error_data  = e.errors()[0]['ctx']['error'].args
        return templates_users.TemplateResponse(
        "users/register.html",  # Template name
        {
            "request": request,
            'menu':menu,
            'error':{i:k for i, k in enumerate(error_data)}

            }  # Context data
    )
    
    select_bool = await select_data_user(user)
    if select_bool == None:
        await insert_data(user)
    else:
        return templates_users.TemplateResponse(
        "users/register.html",  # Template name
        {
            "request": request,
            'menu':menu,
            'error':'This login already exists'

            }
    )


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
            'menu': menu
        }
    )

@router.post('/login/check')
async def login_check(
    request: Request,
    username=Form(), 
    password=Form()):

    data = await select_data_user(username)
    if data is not None:
        if data.username == username and data.check_password(password):
            token = security.create_access_token(uid=str(data.id), data={'username':username})
            # Set the access token in a cookie
            response = RedirectResponse(url="/", status_code=303)  # 303 See Other
            
            response.set_cookie(
                key=load_env.JWT_ACCESS_COOKIE_NAME,
                value=token,
                httponly=True,  # Prevent client-side JavaScript from accessing the cookie
                secure=True,     # Ensure the cookie is only sent over HTTPS
                samesite="lax"   # Prevent CSRF attacks
            )
            return response
    return HTTPException(status_code=401, detail='Incorrect username or password')

@router.get('/logout')
async def login_check(request: Request):
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    return response

@router.post("/refresh-token")
async def refresh_token(token: str = Depends(security.refresh_token_required)):
    try:
        # Decode the refresh token
        print('Old token:', token)
        payload_decode = jwt.decode(token, options={"verify_signature": False})
        payload = security.create_refresh_token(uid=payload_decode['sub'], data={'username':payload_decode['username']})
        print('New token:', payload)

        return payload
    except JWTDecodeError as e:
        if "Signature has expired" in str(e):
            raise HTTPException(status_code=401, detail="Refresh token has expired. Please log in again.")
        else:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

#@router.get('/protected', dependencies=[Depends(security.access_token_required)])
#async def protected(request:Request):
    #return {'data':'only autorised users can see it'}