from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import hashlib
import bcrypt

hash_protocol = bcrypt

class Settings(BaseSettings):
    JWT_SECRET_KEY:str
    JWT_ACCESS_COOKIE_NAME:str
    MODE:str
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".", ".env")
    )
load_env = Settings()