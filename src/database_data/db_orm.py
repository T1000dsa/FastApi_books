from src.database_data.models import BookModelOrm, TagsModelOrm
from src.database_data.database import async_session_maker, async_engine, Base
from sqlalchemy import select, update, delete
from src.init_data.models import BookModelPydantic, TagsModelPydantic

async def create_data():
    async with async_engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

async def insert_data(data=None):
    async with async_session_maker() as session:

        if isinstance(data, BookModelPydantic):
            res = BookModelPydantic.model_validate(data, from_attributes=True)
            session.add(BookModelOrm(
                title=res.title, 
                author=res.author,
                slug=res.slug,
                text_hook=res.text_hook
                ))
            await session.commit()

        elif isinstance(data, TagsModelPydantic):
            res = TagsModelPydantic.model_validate(data, from_attributes=True)
            session.add(TagsModelOrm(
                slug=res.slug, 
                tag=res.tag
                ))
            await session.commit()

async def update_data(id_data:int=None, data:BookModelPydantic|TagsModelPydantic=None):
    async with async_session_maker() as session:
        if isinstance(data, BookModelPydantic):
            res = BookModelPydantic.model_validate(data, from_attributes=True)
            statement = (
                    update(BookModelOrm)
                    .where(BookModelOrm.id == id_data if id_data else res.id)
                    .values(
                title=res.title, 
                author=res.author,
                slug=res.slug,
                text_hook=res.text_hook
                )
                )
            await session.execute(statement)
            await session.commit()

        elif isinstance(data, TagsModelPydantic):
            res = TagsModelPydantic.model_validate(data, from_attributes=True)
            statement = (
                    update(TagsModelOrm)
                    .where(TagsModelOrm.id == id_data if id_data else res.id)
                    .values(slug=res.slug, 
                            tag=res.tag,
                            )
                )
            await session.execute(statement)
            await session.commit()


async def drop_object(data:TagsModelPydantic|BookModelPydantic=None, drop_id:int=None):
    if drop_id is not None and data is not None:
        async with async_session_maker() as session:
            if data == BookModelPydantic:
                statement = (
                        delete(BookModelOrm)
                        .where(BookModelOrm.id == drop_id)
                    )
                await session.execute(statement)
                await session.commit()
                
            elif data == TagsModelPydantic:
                statement = (
                        delete(TagsModelOrm)
                        .where(TagsModelOrm.id == drop_id)
                    )
                await session.execute(statement)
                await session.commit()

    if drop_id is None and data is not None:
        async with async_session_maker() as session:
            if data == BookModelPydantic:
                statement = (
                        delete(BookModelOrm)
                    )
                await session.execute(statement)
                await session.commit()
                
            elif data == TagsModelPydantic:
                statement = (
                        delete(TagsModelOrm)
                    )
                await session.execute(statement)
                await session.commit()

    if drop_id is None and data is None:
        async with async_engine.connect() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.commit()


async def output_data(data:int=0):
    async with async_engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()
    async with async_session_maker() as session:
        if data == 0:
            query = select(BookModelOrm)
            res = await session.execute(query)
            result = res.scalars().all()
            return result
        if data == 1:
            query = select(TagsModelOrm)
            res = await session.execute(query)
            result = res.scalars().all()
            return result

