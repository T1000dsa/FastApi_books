from src.database_data.database import Base, int_pk, created_at, updated_at, str_uniq, ist
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

    text_hook:Mapped[str|None] # Path to the file like in Django

    tag_books:Mapped[list['TagsModelOrm']] = relationship(
        'TagsModelOrm',
        back_populates="book_tags", 
        secondary="tagsinbooks", 
        )
    def __set_tags__(self, new):
        self.tag_books=new

    

class TagsModelOrm(Base): 
    __tablename__ = 'tags'

    id:Mapped[int_pk]
    slug:Mapped[str_uniq]
    tag:Mapped[str]

    book_tags:Mapped[list['BookModelOrm']] = relationship(
        'BookModelOrm',
        back_populates="tag_books", 
        secondary="tagsinbooks",
        )
    

class TagsOnBookOrm(Base):
    __tablename__ = 'tagsinbooks'

    book_id:Mapped[int] = mapped_column(
        ForeignKey('books.id', ondelete='CASCADE'),
        primary_key=True,
    )
    tag_id:Mapped[int] = mapped_column(
        ForeignKey('tags.id', ondelete='CASCADE'),
        primary_key=True
    )