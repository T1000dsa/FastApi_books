# python -m uvicorn src.core.main:app --reload
from fastapi.responses import FileResponse
from fastapi import FastAPI
from ..database_data.db_orm import create_data, drop_object, insert_data, update_data, output_data
from ..init_data.models import BookModelPydantic, TagsModelPydantic
import asyncio
from fastapi import UploadFile, File, Form


app = FastAPI()
succeses = {'status_code':200}
#failule = {'status_code':400}

@app.get('/')
async def first_def():
    return FileResponse("frontend/templates/form_index.html")

@app.get('/action/get_list/{choice}', tags=['get'])
async def first_def(choice:int=0):
    result = await output_data(choice)
    succeses.update({'msg':'Data was gaved', 'data':result})
    return succeses

@app.post('/action/create', tags=['init'])
async def create_db_data():
    await drop_object()
    await create_data()
    succeses.update({'msg':'Tables were created'})
    return succeses

@app.post('/action/insert/book', tags=['books'])
async def insert_db_data_book(model:BookModelPydantic):
    await insert_data(model)
    succeses.update({'msg':'Data was inserted'})
    return succeses

@app.post('/action/insert/tag', tags=['tags'])
async def insert_db_data_tag(model:TagsModelPydantic):
    await insert_data(model)
    succeses.update({'msg':'Data was inserted'})
    return succeses
    

@app.delete('/action/delete/book', tags=['books'])
async def drop_db_data_book(id:int=None):
    await drop_object(BookModelPydantic, drop_id=id)
    succeses.update({'msg':'Book was deleted'})
    return succeses

@app.delete('/action/delete/tag', tags=['tags'])
async def drop_db_data_tag(id:int=None):
    await drop_object(TagsModelPydantic, drop_id=id)
    succeses.update({'msg':'Tag was deleted'})
    return succeses

@app.put('/action/update/book', tags=['books'])
async def update_db_data_book(model:BookModelPydantic, id:int=None):
    await asyncio.create_task(update_data(id, model))
    succeses.update({'msg':'Book was updated'})
    return succeses

'''
@app.put('/action/update/tag', tags=['tags'])
async def update_db_data_tag(model:TagsModelPydantic, id:int=None):
    task = asyncio.create_task(update_data(id, model))
    await task
    succeses.update({'msg':'Tag was updated'})
    return succeses
'''


@app.post("/postdata")
def postdata(
    title=Form(), 
    author=Form(),
    slug=Form(),
    text_hook=Form()
    ):
    return {
        "title": title, 
        "author": author,
        "slug":slug,
        "text_hook":text_hook

        }

