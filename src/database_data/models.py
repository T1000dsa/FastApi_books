from src.database_data.database import Base, int_pk, created_at, updated_at, str_uniq, ist
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
import slugify

class BookModelOrm(Base):
    __tablename__ = 'books'

    id:Mapped[int_pk]
    title:Mapped[str_uniq]
    author:Mapped[str|None]
    slug:Mapped[str]
    created_at:Mapped[created_at]
    updated_at:Mapped[updated_at]
    text_hook:Mapped[str|None]

    tag_books:Mapped[list['TagsModelOrm']] = relationship(
        'TagsModelOrm',
        back_populates="book_tags", 
        secondary="tagsinbooks", 
        )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.slug = slugify.slugify(self.title)

    def __set_tags__(self, new):
        self.tag_books=new
    

class TagsModelOrm(Base): 
    __tablename__ = 'tags'

    id:Mapped[int_pk]
    slug:Mapped[str]
    tag:Mapped[str_uniq]

    book_tags:Mapped[list['BookModelOrm']] = relationship(
        'BookModelOrm',
        back_populates="tag_books", 
        secondary="tagsinbooks",
        )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.slug = slugify.slugify(self.tag) # Generate slug when title is set
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