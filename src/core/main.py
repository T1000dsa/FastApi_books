# python3 -m uvicorn src.core.main:app --reload
from fastapi import FastAPI
from ..database_data.db_orm import create_data, drop_object, insert_data, update_data, output_data
from ..init_data.models import BookModelPydantic, TagsModelPydantic
import asyncio

app = FastAPI()


@app.get('/')
async def first_def():
    return {'msg':'hi there!'}

@app.get('/get_list', tags=['get'])
async def first_def(choice:int=0):
    task = asyncio.create_task(output_data(choice))
    result = await task
    return {'msg':'Data was gaved', 'data':result}

@app.post('/action/create', tags=['init'])
async def create_db_data():
    task = asyncio.create_task(create_data())
    await task
    return {'code':200, 'msg':'Tables were created'}

@app.post('/action/insert/book', tags=['books'])
async def insert_db_data_book(model:BookModelPydantic):
    task_post = asyncio.create_task(insert_data(model))
    await task_post
    return {'code':200, 'msg':'Data was inserted'}

@app.post('/action/insert/tag', tags=['tags'])
async def insert_db_data_tag(model:TagsModelPydantic):
    task_post = asyncio.create_task(insert_data(model))
    await task_post
    return {'code':200, 'msg':'Data was inserted'}
    

@app.delete('/action/delete/book', tags=['books'])
async def drop_db_data_book(id:int=None):
    task = asyncio.create_task(drop_object(BookModelPydantic, drop_id=id))
    await task
    return {'code':200, 'msg':'Tables/objects were deleted'}

@app.delete('/action/delete/tag', tags=['tags'])
async def drop_db_data_tag(id:int=None):
    task = asyncio.create_task(drop_object(TagsModelPydantic, drop_id=id))
    await task
    return {'code':200, 'msg':'Tables/objects were deleted'}


@app.delete('/action/delete/all', tags=['delete'])
async def drop_db_data_all():
    task = asyncio.create_task(drop_object())
    await task
    return {'code':200, 'msg':'Tables/objects were deleted'}


