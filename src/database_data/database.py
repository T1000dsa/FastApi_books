from datetime import datetime
from typing import Annotated

from sqlalchemy import func, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, mapped_column, sessionmaker
from src.database_data.settings import get_db_url_async

import hashlib

db_url = get_db_url_async()

async_engine = create_async_engine(
    url=db_url,
    echo=False
    )

sync_engine = create_engine(
    url=db_url
)

sync_session_maker = sessionmaker(
    sync_engine,
)


async_session_maker = async_sessionmaker(
    async_engine, 
    class_=AsyncSession,
    expire_on_commit=False
    )


# настройка аннотаций
int_pk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_true = Annotated[str, mapped_column(nullable=True)]
ist = Annotated[hashlib, mapped_column(nullable=False)]

class Base(DeclarativeBase):
    pass