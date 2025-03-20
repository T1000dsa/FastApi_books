from fastapi import APIRouter, HTTPException, Response, Depends ,Request
from authx import AuthX, AuthXConfig
from src.users.user_scheme import User
from src.users.user_config import load_env
from src.users.user_orm import select_data_user, insert_data, update_data, delete_data
from fastapi.templating import Jinja2Templates
from src.menu import menu
from fastapi import UploadFile, File, Form

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse

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
        print(error_data)
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

            }  # Context data
    )


    return templates_users.TemplateResponse(
        "users/register_success.html",  # Template name
        {
            "request": request,
            "content": "Greetings! Choose a book and make yourself comfortable here!",
            'menu': menu  # Ensure 'menu' is defined in your context
        }  # Context data
    )

@router.post('/login')
async def login(creds:User, response:Response):
    data = await select_data_user(creds)
    if creds.username == select_data_user and creds.password == 'test':
        token = security.create_access_token(uid='1232343243243244322')
        # Set the access token in a cookie
        response.set_cookie(load_env.JWT_ACCESS_COOKIE_NAME, token)
        return {"access_token": token}
    return HTTPException(status_code=401, detail='Incorrect username or password')

#@router.get('/protected', dependencies=[Depends(security.access_token_required)])
#async def protected(request:Request):
    #return {'data':'only autorised users can see it'}