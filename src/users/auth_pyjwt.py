from fastapi import (
    APIRouter, 
    HTTPException,
    status,
    Response, 
    Depends,
    Request, 
    Form)
from src.users.user_scheme import User, TokenInfo
from src.users.utils import encode_jwt, decode_jwt, create_refresh_token, create_access_token, create_refresh_token
from src.users.user_orm import select_data_user
from src.users.user_models import UserModel as db_user
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from src.core.config import authJWT

from datetime import datetime, timedelta
from src.core.config import logger

router = APIRouter(tags=['auth'])
http_bearer = HTTPBearer()
TOKEN_TYPE = "type"
ACCESS_TYPE = 'access token'
REFRESH_TYPE = 'refresh token'

unauth_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Incorrect password or login'
    )
token_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Token invalid'
    )

def validate_token(payload:dict, token_type:str):
    if payload.get(TOKEN_TYPE) == token_type:
        return True
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Invalid token. Expected {token_type}'
            )
        
async def validate_user(
        username:str = Form(),
        password:str = Form()
):
    
    user_obj:db_user = await select_data_user(username)

    if user_obj == None:
        raise unauth_exc
    if user_obj.check_password(password):
        return user_obj
    raise unauth_exc

async def get_current_user_payload(
        creds:HTTPAuthorizationCredentials=Depends(http_bearer)
) -> User:
    creds_data = creds.credentials

    try:    
        payload = decode_jwt(token=creds_data)
        return payload
    except(InvalidTokenError) as err:
        logger.exception(err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Invalid token error'
        )

async def get_current_user(
        payload:dict = Depends(get_current_user_payload)
) -> db_user:
    token_type:str = payload.get(TOKEN_TYPE)

    validate_token(payload=payload, token_type=token_type)
    username:str|None = payload.get('username')
    user_id:int|None = payload.get('id')
    user_obj:db_user = await select_data_user(user_id if user_id else username)

    if user_obj == None:
        raise token_exc
    return user_obj  

async def get_current_active_user(
        user:db_user=Depends(get_current_user)
        
):
    if user.is_active:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail='Incorrect password or login'
    )


@router.post('/login')
async def login(user:db_user=Depends(validate_user)):

    access_token = await create_access_token(user)
    refresh_token = await create_refresh_token(user)
    return TokenInfo(
        access_token=access_token,
        refresh_token=refresh_token
        )

@router.post('/refresh', 
             response_model=TokenInfo,
             response_model_exclude_none=True)
async def set_new_access_token(
    payload:dict = Depends(get_current_user_payload), 
    user:db_user=Depends(get_current_active_user)
    ):
    token_type:str = REFRESH_TYPE
    if validate_token(payload=payload, token_type=token_type):
        access_token = await create_access_token(user)

    return TokenInfo(
        access_token=access_token,
        )

@router.get('/user')
async def auth_user_check(
    payload:dict = Depends(get_current_user_payload),
    user:db_user=Depends(get_current_active_user)
):

    iat = payload.get('iat')
    current_user = await select_data_user(user.id)
    return {
        'join_data':current_user.join_data,
        'last_time_login':current_user.last_time_login,
        'iat':datetime.fromtimestamp(iat).strftime('%Y-%m-%d %H:%M:%S')
    }
