from src.database_data.database import async_session_maker, async_engine, Base
from sqlalchemy import select, update, delete, join
from src.init_data.models import BookModelPydantic, TagsModelPydantic
from src.users.user_models import User
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from src.users.user_scheme import User as User_pydantic

async def select_data_user(data:User_pydantic):
    async with async_engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    async with async_session_maker() as session:
        query = select(User).where(User.username==data.username)
        res = await session.execute(query)
        result = res.scalar_one_or_none()
        return result
    
async def insert_data(data:User_pydantic=None):
    async with async_session_maker() as session:
        if type(data) == User_pydantic:
            res = User_pydantic.model_validate(data, from_attributes=True)
            user_data = {i:k for i, k in res.model_dump().items() if i != 'password_again'}
            new_data = User(**user_data)
            new_data.set_password(new_data.password)
            session.add(new_data)
            await session.commit()

async def update_data(data_id:int=None, data:User_pydantic=None):
    async with async_session_maker() as session:
        if type(data) == User_pydantic:
            res = User_pydantic.model_validate(data, from_attributes=True)
            stm = (
                update(User)
                .where(User.id==data_id)
                .values(**res)
            )
            await session.execute(stm)
            await session.commit()

async def delete_data(data_id:int=None):
    async with async_session_maker() as session:
        stm = (
                delete(User)
                .where(User.id==data_id)
            ) 
        await session.execute(stm)
        await session.commit()
        