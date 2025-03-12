from pydantic import BaseModel, Field
from datetime import datetime

class BookModelPydantic(BaseModel):
    title:str
    author:str
    slug:str
    #count:Mapped[int]
    #price:Mapped[int|None]
    created_at:datetime
    updated_at:datetime
    text_hook:str|None

class TagsModelPydantic(BaseModel):
    slug:str
    tag:str

