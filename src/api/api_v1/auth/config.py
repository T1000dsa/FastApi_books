from fastapi.templating import Jinja2Templates
from authx import AuthX, AuthXConfig, RequestToken
from datetime import timedelta

from src.core.config import frontend_root
from src.api.api_v1.auth.user_config import load_env
from src.core.config import (ACCESS_TYPE, REFRESH_TYPE, TOKEN_TYPE, refresh_token_expire, access_token_expire)

templates_users = Jinja2Templates(directory=frontend_root)
config = AuthXConfig(
    JWT_SECRET_KEY=load_env.JWT_SECRET_KEY,
    JWT_ACCESS_COOKIE_NAME = load_env.JWT_ACCESS_COOKIE_NAME,
    JWT_REFRESH_COOKIE_NAME = load_env.JWT_REFRESH_COOKIE_NAME,
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(minutes=refresh_token_expire),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=access_token_expire)
    
)

securityAuthx = AuthX(config=config)