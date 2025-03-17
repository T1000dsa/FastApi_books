# venv/Scripts/activate | deactivate; venv -> 1 | 0
# pip install -U aiogram; -U when venv: 1 | -U if venv == True
# git add <file> | git add .
# git commit -m "description"
# git push origin main
# python3 -m venv venv
# venv/Scripts/activate.bat
# . venv/bin/activate
# virtualenv .env
# git ls-files | xargs wc -l
# pip install -r requirements.txt
# python -m uvicorn src.core.main:app --reload
from fastapi.responses import FileResponse
from fastapi import FastAPI
from ..database_data.db_orm import create_data, drop_object, insert_data, update_data, output_data
from ..init_data.models import BookModelPydantic, TagsModelPydantic
import asyncio
from fastapi import UploadFile, File, Form
import logging
app = FastAPI()


logger = logging.getLogger(__name__)

logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

@app.get('/')
async def first_def():
    return FileResponse("frontend/templates/form_index.html")

@app.get('/action/get_list/{choice}', tags=['get'])
async def get_list(choice:int):
    if isinstance(choice, int):
        result = await output_data(choice)
        return {'msg':'Data was gaved', 'data':result}

    return {'msg':'invalid choice'}


@app.post('/action/create', tags=['init'])
async def create_db_data():
    await drop_object()
    await create_data()
    return {'msg':'Tables were created'}

@app.post('/action/insert/book', tags=['books'])
async def insert_db_data_book(model:BookModelPydantic):
    await insert_data(model)
    return {'msg':'Data was inserted'}

@app.post('/action/insert/tag', tags=['tags'])
async def insert_db_data_tag(model:TagsModelPydantic):
    await insert_data(model)
    return {'msg':'Data was inserted'}
    

@app.delete('/action/delete/book', tags=['books'])
async def drop_db_data_book(id:int=None):
    await drop_object(BookModelPydantic, drop_id=id)
    return {'msg':'Book was deleted'}


@app.delete('/action/delete/tag', tags=['tags'])
async def drop_db_data_tag(id:int=None):
    await drop_object(TagsModelPydantic, drop_id=id)
    return {'msg':'Tag was deleted'}

@app.put('/action/update/book', tags=['books'])
async def update_db_data_book(model:BookModelPydantic, id:int=None):
    await asyncio.create_task(update_data(id, model))
    return {'msg':'Book was updated'}

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

