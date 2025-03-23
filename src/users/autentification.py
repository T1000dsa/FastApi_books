from fastapi import APIRouter, HTTPException, Response, Depends ,Request
from authx import AuthX, AuthXConfig
from src.users.user_scheme import User
from src.users.user_config import load_env
from src.users.user_orm import select_data_user, insert_data, update_data, delete_data
from fastapi.templating import Jinja2Templates
from src.menu import menu
from fastapi import Form
from authx.exceptions import JWTDecodeError
from fastapi.security import OAuth2PasswordBearer 
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from authx import RequestToken
#from fastapi_jwt_auth import AuthJWT
import jwt

router = APIRouter()
templates_users = Jinja2Templates(directory="frontend/templates")
config = AuthXConfig(
    JWT_SECRET_KEY=load_env.JWT_SECRET_KEY,
    JWT_ACCESS_COOKIE_NAME = load_env.JWT_ACCESS_COOKIE_NAME,
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_REFRESH_TOKEN_EXPIRES=7,  # Refresh token expires in 7 days (604800 seconds)
    
)

securityAuthx = AuthX(config=config)



@router.get('/register', tags=['auth'])
async def register(request:Request):
    return templates_users.TemplateResponse(
        "users/register.html",  # Template name
        {
            "request": request,
            'menu':menu,
            'form_data': {} 

            }  # Context data
    )

@router.post('/register', tags=['auth'])
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
        user = User(
            username=username,
            password=password,
            password_again=password_again,
            mail=mail,
            bio=bio
        )
    except ValidationError as e:
        error_data = e.errors()[0].get('ctx').get('error')


        return templates_users.TemplateResponse(
            "users/register.html",
            {
                "request": request,
                'menu': menu,
                'error':error_data.args,
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

@router.post('/register_success', tags=['auth'])
async def reg_success(request:Request):
    return templates_users.TemplateResponse(
        "users/register_success.html",  # Template name
        {
            "request": request,
            'menu': menu
        }
    )

@router.get('/login', tags=['auth'])
async def login(request:Request):
    return templates_users.TemplateResponse(
        "users/login.html",  # Template name
        {
            "request": request,
            'menu': menu
        }
    )

@router.post('/login/check', tags=['auth'])
async def login_check(
    username=Form(), 
    password=Form()):

    data = await select_data_user(username)
    if data is not None:
        if data.username == username and data.check_password(password):
            user_data = {'uid':str(data.id), 'data':{'username':username}}
            token = securityAuthx.create_access_token(**user_data)
            refresh_token = securityAuthx.create_refresh_token(**user_data)
            # Set the access token in a cookie
            response = RedirectResponse(url="/", status_code=303)  # 303 See Other
            
            response.set_cookie(
            key="access_token",  # Replace with your cookie name
            value=token,
            httponly=True,  # Prevent client-side JavaScript from accessing the cookie
            secure=True,     # Ensure the cookie is only sent over HTTPS
            samesite="lax"   # Prevent CSRF attacks
            )

        # Include the refresh token in the response body
            response.set_cookie(
            key="refresh_token",  # Replace with your cookie name
            value=refresh_token,
            httponly=True,  # Prevent client-side JavaScript from accessing the cookie
            secure=True,     # Ensure the cookie is only sent over HTTPS
            samesite="lax"   # Prevent CSRF attacks
            )
            return response
    return HTTPException(status_code=401, detail='Incorrect username or password')

@router.get('/logout', tags=['auth'])
async def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


"""@router.post("/refresh")
async def refresh(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_refresh_token_required()
        current_user = Authorize.get_jwt_subject()
        new_access_token = Authorize.create_access_token(subject=current_user)
        response = Response()

        response.set_cookie(
            key="access_token",  # Replace with your cookie name
            value=new_access_token,
            httponly=True,  # Prevent client-side JavaScript from accessing the cookie
            secure=True,     # Ensure the cookie is only sent over HTTPS
            samesite="lax"   # Prevent CSRF attacks
            )
        return response
    except Exception as e:
        print("Error:", e)  # Debugging: Print the error
        raise HTTPException(status_code=401, detail=f"Invalid or expired refresh token. {e}")"""
#@router.get('/protected', dependencies=[Depends(security.access_token_required)])
#async def protected(request:Request):
    #return {'data':'only autorised users can se it'}