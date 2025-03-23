from pydantic import BaseModel, Field
from datetime import datetime

class BookModelPydantic(BaseModel):
    title:str
    author:str
    #count:Mapped[int]
    #price:Mapped[int|None]
    text_hook:str|None

    tags:list[int]|None

class TagsModelPydantic(BaseModel):
    tag:str

    books:list[int]


