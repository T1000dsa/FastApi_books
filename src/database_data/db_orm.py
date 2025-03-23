from src.database_data.models import BookModelOrm, TagsModelOrm, TagsOnBookOrm
from src.database_data.database import async_session_maker, async_engine, Base
from sqlalchemy import select, update, delete, join
from src.core.schemes import BookModelPydantic, TagsModelPydantic
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')



async def create_data():
    async with async_engine.begin() as conn:
        # Use run_sync to execute the synchronous create_all method
        await conn.run_sync(Base.metadata.create_all)

async def insert_data(data:TagsModelPydantic|BookModelPydantic=None):
    async with async_session_maker() as session:

        if type(data) == BookModelPydantic:
            res = BookModelPydantic.model_validate(data, from_attributes=True)
            stm = select(TagsModelOrm).where(TagsModelOrm.id.in_(res.tags))
            tag_objs = await session.execute(stm)
            session.add(BookModelOrm(
                    title=res.title, 
                    author=res.author,
                    text_hook=res.text_hook,
                    tag_books=tag_objs.scalars().all()
                    ))
            await session.commit()

        elif type(data) == TagsModelPydantic:
            res = TagsModelPydantic.model_validate(data, from_attributes=True)
            stm = select(BookModelOrm).where(BookModelOrm.id.in_(res.books))
            tag_objs = await session.execute(stm)
            session.add(TagsModelOrm(
                tag=res.tag,
                book_tags=tag_objs.scalars().all()
                ))
            await session.commit()


async def update_data(id_data: int, data: BookModelPydantic|TagsModelPydantic):
    async with async_session_maker() as session:
        try:
            # Validate the input data
            if type(data) == BookModelPydantic:
                res = BookModelPydantic.model_validate(data, from_attributes=True)
                
                # Fetch the tags from the database based on the tag IDs in the input data
                tag_objs = (await session.execute(select(TagsModelOrm).where(TagsModelOrm.id.in_(res.tags)))).scalars().all()
                
                # Fetch the book to be updated, eagerly loading the tag_books relationship
                book = (await session.execute(select(BookModelOrm).where(BookModelOrm.id == id_data)
                        .options(selectinload(BookModelOrm.tag_books))) # Eagerly load the relationship
                ).scalar_one()
                
                # Clear existing tags and apply new tags
                book.tag_books.clear()  # Remove existing tags
                book.tag_books.extend(tag_objs)  # Add new tags
                
                # Add the book to the session (if not already tracked)
                session.add(book)
                
                # Commit the changes to the database
                await session.commit()
                
                # Refresh the book instance to reflect the changes
                await session.refresh(book)
                
                return book
            
            elif type(data) == TagsModelPydantic:
                res = TagsModelPydantic.model_validate(data, from_attributes=True)
                book_objs = (await session.execute(select(BookModelOrm).where(BookModelOrm.id.in_(res.books)))).scalars().all()
                tag = (await session.execute(select(TagsModelOrm).where(TagsModelOrm.id == id_data)
                        .options(selectinload(TagsModelOrm.book_tags)))
                ).scalar_one()
                

                tag.book_tags.clear()  # Remove existing books
                tag.book_tags.extend(book_objs)  # Add new books
                
                session.add(tag)
                await session.commit()
                await session.refresh(tag)
                
                return tag

        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Error updating book: {e}")
            raise e


async def drop_object(data:TagsModelPydantic|BookModelPydantic=None, drop_id:int=None):
    if drop_id is not None and data is not None:
        async with async_session_maker() as session:
            if data == BookModelPydantic:
                statement = (
                        delete(BookModelOrm)
                        .where(BookModelOrm.id == drop_id)
                    )
                await session.execute(statement)
                
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
                
            elif data == TagsModelPydantic:
                statement = (
                        delete(TagsModelOrm)
                    )
                await session.execute(statement)

            await session.commit()

    if drop_id is None and data is None:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


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

async def select_data_book(data:int):
    async with async_engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    async with async_session_maker() as session:
        query = select(BookModelOrm).where(BookModelOrm.id==int(data))
        res = await session.execute(query)
        result = res.scalar_one_or_none()
        return result