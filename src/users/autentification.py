from fastapi import APIRouter, HTTPException, Response, Depends ,Request
from authx import AuthX, AuthXConfig
from src.users.user_scheme import User
from src.users.user_config import load_env
from src.users.user_orm import select_data_user, insert_data, update_data, delete_data
from fastapi.templating import Jinja2Templates
from src.menu import menu
from fastapi import Form
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from authx import RequestToken
from src.core.config import ACCESS_TYPE, REFRESH_TYPE, TOKEN_TYPE, refresh_token_expire
from src.core.config import logger
#from fastapi_jwt_auth import AuthJWT

router = APIRouter(tags=['auth'])
templates_users = Jinja2Templates(directory="frontend/templates")
config = AuthXConfig(
    JWT_SECRET_KEY=load_env.JWT_SECRET_KEY,
    JWT_ACCESS_COOKIE_NAME = load_env.JWT_ACCESS_COOKIE_NAME,
    JWT_REFRESH_COOKIE_NAME = load_env.JWT_REFRESH_COOKIE_NAME,
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_REFRESH_TOKEN_EXPIRES=refresh_token_expire,
    
)

securityAuthx = AuthX(config=config)


@router.get('/register')
async def register(request:Request):
    return templates_users.TemplateResponse(
        "users/register.html",  # Template name
        {
            "request": request,
            'menu':menu,
            'form_data': {} 

            }  # Context data
    )

@router.post('/register')
async def register_check(request:Request,
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
    select_bool = await select_data_user(user)
    if select_bool == None:
        await insert_data(user)
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
    request:Request,
    username=Form(), 
    password=Form()
    ):
    form_data = {
        'username':username, 
        'password':password
        }

    data = await select_data_user(username)
    if data is not None:
        if data.username == username and data.check_password(password):
            user_data = {'uid':str(data.id), 'data':{'username':username}}
            token = securityAuthx.create_access_token(**user_data).decode()
            refresh_token = securityAuthx.create_refresh_token(**user_data).decode()

            response = RedirectResponse(url="/", status_code=303) 
            
            response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,  # Prevent client-side JavaScript from accessing the cookie
            secure=True,     # Ensure the cookie is only sent over HTTPS
            samesite="lax"   # Prevent CSRF attacks
            )

            response.set_cookie(
            key="refresh_token",
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
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.post("/refresh")
async def refresh(request: Request):
    try:
        refresh_token = request.cookies.get(REFRESH_TYPE)
        if not refresh_token:
            raise HTTPException(status_code=401, detail="Refresh token not found")
        
        request_token = RequestToken(token=refresh_token, location="cookies" , type='refresh')

        payload = securityAuthx.verify_token(request_token, verify_csrf=False)

        new_access_token = securityAuthx.create_access_token(uid=payload.sub).decode()



        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="lax"
        )

        return response
    except Exception as e:
        print("Error:", e) 
        logger.exception(e)
        raise HTTPException(status_code=401, detail=f"Invalid or expired refresh token. {e}")