from fastapi import HTTPException
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
import os

from src.api.api_v1.orm.db_orm import (output_data, select_data_book)
from src.core.config import max_file_size, media_root


class Choice:
    def __init__(self, choice:int, session:AsyncSession):
        self.choice = choice
        self.session = session

    def get_obj(self):
        return output_data(self.session, self.choice)
    
class Select:
    def __init__(self, select_id:int, session:AsyncSession):
        self.select_id = select_id
        self.session = session
    def get_obj(self):
        return select_data_book(self.session, self.select_id)
    
async def book_process(text_hook:UploadFile) -> str:
    noise = uuid4().int

    if ".." in text_hook.filename or "/" in text_hook.filename:
        raise HTTPException(status_code=400, detail="Invalid file name")

    if text_hook.size > max_file_size:
        raise HTTPException(status_code=400, detail="File size exceeds the limit")

    os.makedirs(media_root, exist_ok=True)
    local = os.path.join(media_root, f'{noise}')

    with open(local, 'wb') as filex:
        filex.write(await text_hook.read())

    return local
    
get_list = Choice
get_select = Select