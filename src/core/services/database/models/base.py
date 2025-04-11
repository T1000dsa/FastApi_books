from sqlalchemy.orm import (
    DeclarativeBase, 
    mapped_column,
    )
from sqlalchemy import func
from typing import Annotated
from datetime import datetime

class Base(DeclarativeBase):

    #@declared_attr.directive
    #def __tablename__(cls):
    #    return cls.__name__.lower()
    pass


int_pk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_true = Annotated[str, mapped_column(nullable=True)]