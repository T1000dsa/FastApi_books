from src.database_data.database import Base, int_pk, created_at, updated_at, str_uniq
from datetime import datetime 
from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from sqlalchemy import ForeignKey
from typing import List

class BookModelOrm(Base):
    __tablename__ = 'books'

    id:Mapped[int_pk]
    title:Mapped[str]
    author:Mapped[str|None]
    slug:Mapped[str_uniq]
    created_at:Mapped[created_at]
    updated_at:Mapped[updated_at]

    #tags:Mapped[list['TagsModelOrm']|None] = relationship()
    text_hook:Mapped[str|None] # Path to the file like in Django

    #goods_id:Mapped[list["GoodsModelOrm"]] = relationship()
    #count:Mapped[int]
    #price:Mapped[int|None]



class TagsModelOrm(Base): 
    __tablename__ = 'tags'

    id:Mapped[int_pk]
    slug:Mapped[str_uniq]
    tag:Mapped[str]
