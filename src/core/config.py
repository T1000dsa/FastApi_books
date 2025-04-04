from datetime import datetime
from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import logging
import os


logger = logging.getLogger(__name__)

logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

max_file_size = 10 * 1024 * 1024
base_dir = Path(__file__).parent.parent
media_root = base_dir / "media_root" / datetime.now().date().strftime('%Y/%m/%d')
frontend_root = base_dir / 'frontend' / 'templates'
_core_env_file = base_dir / "core" / ".env"

TOKEN_TYPE = "type"
ACCESS_TYPE = 'access'
REFRESH_TYPE = 'refresh'

access_token_expire:int = 15
refresh_token_expire:int = 60*24*7
refresh_time:int = 5
pagination_pages:int = 2

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


class DatabaseConfig(BaseModel): 
    url: PostgresDsn
    echo: bool = True
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        env_prefix='FAST__',
        env_file=_core_env_file,
        env_file_encoding='utf-8'
    )
    run: RunConfig = RunConfig()
    data: Current_ApiPrefix = Current_ApiPrefix()
    mode: Mode = Mode()  # Default provided
    db: DatabaseConfig

settings = Settings()