from fastapi.templating import Jinja2Templates
from authx import AuthX, AuthXConfig
from datetime import timedelta

from src.core.config import (ACCESS_TYPE, REFRESH_TYPE, refresh_token_expire, access_token_expire, settings, frontend_root)

templates_users = Jinja2Templates(directory=frontend_root)
config = AuthXConfig(
    JWT_ALGORITHM = "HS256",
    JWT_SECRET_KEY=settings.jwt_key.key,
    JWT_ACCESS_COOKIE_NAME = ACCESS_TYPE,
    JWT_REFRESH_COOKIE_NAME = REFRESH_TYPE,
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(minutes=refresh_token_expire),
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=access_token_expire)
)


securityAuthx = AuthX(config=config)