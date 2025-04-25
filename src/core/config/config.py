from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime
from pathlib import Path
import logging
import os
    
from src.core.menu.urls import menu_items
from src.core.config.models import (
    RunConfig, 
    Current_ApiPrefix,
    Mode, 
    DatabaseConfig, 
    Jwt, 
    RedisSettings, 
    RedisCache, 
    ElasticSearch, 
    Email_Settings
    )


logger = logging.getLogger(__name__)

logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

max_file_size_mb = 10
max_file_size = (1024**2)*max_file_size_mb
base_dir = Path(__file__).parent.parent.parent
media_root = base_dir / "media_root" / datetime.now().date().strftime('%Y/%m/%d')
frontend_root = base_dir / 'frontend' / 'templates'
_core_env_file = Path(__file__).parent.parent.parent.parent / '.env'

TOKEN_TYPE = "type"
ACCESS_TYPE = 'access'
REFRESH_TYPE = 'refresh'

access_token_expire:int = 20 # minutes 
refresh_token_expire:int = 60*24*7 # minutes 
per_page:int = 10

menu = menu_items

if os.path.exists(media_root) == False:
    os.makedirs(media_root, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_prefix='FAST__',
        env_file=_core_env_file,
        env_file_encoding='utf-8',
        extra='ignore'
    )
    run: RunConfig = RunConfig()  # Keep defaults as fallback
    data: Current_ApiPrefix = Current_ApiPrefix()
    mode: Mode = Mode()
    db: DatabaseConfig
    jwt_key: Jwt = Jwt()
    redis_settings: RedisSettings = RedisSettings()
    redis_cache: RedisCache = RedisCache()
    elastic:ElasticSearch = ElasticSearch()
    email:Email_Settings = Email_Settings()

settings = Settings()
settings.db.give_url()
assert settings.mode.mode == 'DEV'