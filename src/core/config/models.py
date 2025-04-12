from pydantic import BaseModel
from datetime import timedelta


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


class ElasticSearch(BaseModel):
    host:str='localhost'
    user:str='elasticuser'
    password:str|None=None