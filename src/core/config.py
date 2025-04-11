from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, PostgresDsn, Field
from redis.asyncio import Redis
from datetime import datetime, timedelta
from pathlib import Path
import logging
import os

from src.core.urls import menu_items


logger = logging.getLogger(__name__)

logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

max_file_size_mb = 10
max_file_size = (1024**2)*max_file_size_mb
base_dir = Path(__file__).parent.parent
media_root = base_dir / "media_root" / datetime.now().date().strftime('%Y/%m/%d')
frontend_root = base_dir / 'frontend' / 'templates'
_core_env_file = base_dir / '.env'

TOKEN_TYPE = "type"
ACCESS_TYPE = 'access'
REFRESH_TYPE = 'refresh'

access_token_expire:int = 20 # minutes 
refresh_token_expire:int = 60*24*7 # minutes 
#refresh_time:int = 19 # refresh each 15 minutes 20 - 5 = 15
per_page:int = 10

menu = menu_items

if os.path.exists(media_root) == False:
    os.makedirs(media_root, exist_ok=True)


class RunConfig(BaseModel):
    host: str = "127.0.0.1"
    port:int=8000

# demonstation
class ApiPrefix_V2(BaseModel):
    prefix:str='/v2'
    users:str='/users'


class ApiPrefix_V1(BaseModel):
    prefix:str='/v1'
    users:str='/users'


class Current_ApiPrefix(BaseModel):
    data:ApiPrefix_V1 = ApiPrefix_V1()


class Mode(BaseModel):
    mode:str='DEV'

class Jwt(BaseModel):
    key:str='some-key-jwt-default'
    algorithm:str='HS256'


class DatabaseConfig(BaseModel): 
    url: None|str = None
    echo: bool = True
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    name: str
    user: str
    password: str
    host: str = 'db'
    port: int = 5432

    def give_url(self):
        if self.url is None:
            self.url = f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
            return self.url
        else:
            return self.url


class RedisSettings(BaseModel):
    host:str='localhost'
    port:int=6379
    db:int=0


class RedisCache(BaseModel):
    REDIS_CACHE_TTL_BOOKS: timedelta = timedelta(hours=1) #86400  # Default: 24h (in seconds)
    REDIS_CACHE_TTL_SESSIONS: timedelta = timedelta(hours=1)  # Sessions expire in 1h


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

settings = Settings()
redis = Redis(
    host=settings.redis_settings.host, 
    port=settings.redis_settings.port,
    db=settings.redis_settings.db
)

settings.db.give_url()