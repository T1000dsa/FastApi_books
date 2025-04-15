from src.core.services.database.models.base import Base, int_pk, created_at, updated_at, str_uniq
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import date

class BookModelOrm(Base):
    __tablename__ = 'books'

    id:Mapped[int_pk]
    title:Mapped[str_uniq] = mapped_column(index=True)
    author:Mapped[str|None]
    year:Mapped[date|None]
    created_at:Mapped[created_at]
    updated_at:Mapped[updated_at]
    text_hook:Mapped[str|None]

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
    tag:Mapped[str_uniq]

    book_tags:Mapped[list['BookModelOrm']] = relationship(
        'BookModelOrm',
        back_populates="tag_books", 
        secondary="tagsinbooks",
        )
    
    def __str__(self):
        return self.tag
    
    

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