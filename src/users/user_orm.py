from src.database_data.database import async_session_maker, async_engine, Base
from sqlalchemy import select, update, delete, join
from src.users.user_models import UserModel
from src.users.user_scheme import User as User_pydantic

async def select_data_user(data:User_pydantic|str|int):
    async with async_session_maker() as session:
        if type(data) == User_pydantic:
                query = select(UserModel).where(UserModel.username==data.username)
                res = await session.execute(query)
                result = res.scalar_one_or_none()
                return result
            
        if type(data) == str:
                query = select(UserModel).where(UserModel.username==data)
                res = await session.execute(query)
                result = res.scalar_one_or_none()
                return result
        
        if type(data) == int:
                query = select(UserModel).where(UserModel.id==data)
                res = await session.execute(query)
                result = res.scalar_one_or_none()
                return result
    
async def insert_data(data:User_pydantic=None):
    async with async_session_maker() as session:
        if type(data) == User_pydantic:
            res = User_pydantic.model_validate(data, from_attributes=True)
            user_data = {i:k for i, k in res.model_dump().items() if i != 'password_again'}
            new_data = UserModel(**user_data)
            new_data.set_password(new_data.password)
            session.add(new_data)
            await session.commit()

async def update_data(data_id:int=None, data:User_pydantic=None):
    async with async_session_maker() as session:
        if type(data) == User_pydantic:
            res = User_pydantic.model_validate(data, from_attributes=True)
            stm = (
                update(UserModel)
                .where(UserModel.id==data_id)
                .values(**res)
            )
            await session.execute(stm)
            await session.commit()

async def delete_data(data_id:int=None):
    async with async_session_maker() as session:
        stm = (
                delete(UserModel)
                .where(UserModel.id==data_id)
            ) 
        await session.execute(stm)
        await session.commit()
        