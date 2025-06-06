from sqlalchemy import select, update, delete, join
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import selectinload, joinedload
from fastapi import  HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.config import logger
from src.core.services.database.models.models import BookModelOrm, TagsModelOrm, TagsOnBookOrm, Base
from src.core.pydantic_schemas.schemas import BookModelPydantic, TagsModelPydantic
from src.core.config.config import per_page
from src.core.services.database.db_helper import db_helper


async def insert_data(
        session:AsyncSession,
        data:TagsModelPydantic|BookModelPydantic=None
        ):
    logger.debug(data)
    try:
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
            book_objs = (await session.execute(stm)).scalars().all()
            session.add(TagsModelOrm(
                    tag=res.tag,
                    book_tags=book_objs
                    ))
            await session.commit()
    except IntegrityError as err:
        raise err


async def update_data(
        session:AsyncSession,
        id_data: int, 
        data: BookModelPydantic | TagsModelPydantic
        ):
    try:
        if isinstance(data, BookModelPydantic):
                # 1. First get the book with relationships
            book = await session.execute(
                    select(BookModelOrm)
                    .where(BookModelOrm.id == id_data)
                    .options(selectinload(BookModelOrm.tag_books))
                )
            book = book.scalar_one()

                # 2. Update scalar fields
            for field, value in data.model_dump(exclude={'tags'}).items():
                setattr(book, field, value)

                # 3. Handle tags - verify existence first
            if data.tags:
                tag_objs = await session.execute(
                        select(TagsModelOrm)
                        .where(TagsModelOrm.id.in_(data.tags))
                    )
                found_tags = tag_objs.scalars().all()
                    
                    # Validate all tags exist
                if len(found_tags) != len(data.tags):
                    found_ids = {t.id for t in found_tags}
                    missing = set(data.tags) - found_ids
                    raise ValueError(f"Tags not found: {missing}")

                book.tag_books.clear()
                book.tag_books.extend(found_tags)

            await session.commit()
            return book

        elif isinstance(data, TagsModelPydantic):
                # Similar pattern for tags
            tag = await session.execute(
                    select(TagsModelOrm)
                    .where(TagsModelOrm.id == id_data)
                    .options(selectinload(TagsModelOrm.book_tags))
            ).scalar_one()

            if data.books:
                book_objs = await session.execute(
                        select(BookModelOrm)
                        .where(BookModelOrm.id.in_(data.books))
                )
                found_books = book_objs.scalars().all()
                    
                if len(found_books) != len(data.books):
                    found_ids = {b.id for b in found_books}
                    missing = set(data.books) - found_ids
                    raise ValueError(f"Books not found: {missing}")

                tag.book_tags.clear()
                tag.book_tags.extend(found_books)

            await session.commit()
            return tag
            
    except ValueError as e:
        await session.rollback()
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")


async def drop_object(
        session:AsyncSession,
        data:TagsModelPydantic|BookModelPydantic=None, 
        drop_id:int=None
        ):
    if drop_id is not None and data is not None:
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

    if drop_id is None and data is not None:
        statement = (
                        delete(BookModelOrm)

        )
        await session.execute(statement)

    await session.commit()

    #if drop_id is None and data is None:
    #    async with async_engine.begin() as conn:
    #        await conn.run_sync(Base.metadata.drop_all)


async def output_data(
        session:AsyncSession,
        data:int=0
        ):

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

async def select_data_book(
        session:AsyncSession,
        data:str|int
        ):
    
    if isinstance(data, str):
        query = select(BookModelOrm).where(BookModelOrm.title==data)
        
    if isinstance(data, int):
        query = select(BookModelOrm).where(BookModelOrm.id==int(data))

    res = await session.execute(query)
    result = res.scalar_one_or_none()
    return result
    
async def select_data_tag(
        session:AsyncSession,
        data: list | BookModelOrm
        ):
    if isinstance(data, list):
        # Handle list of tag names
        tag_list = []
        for tag_name in data:
            result = await session.execute(
                    select(TagsModelOrm)
                    .where(TagsModelOrm.tag == tag_name)
            )
            tag = result.scalar_one_or_none()
            if tag:
                tag_list.append(tag)
        return tag_list
            
    elif isinstance(data, BookModelOrm):
        # Handle BookModelOrm with eager loading
        result = await session.execute(
                select(BookModelOrm)
                .where(BookModelOrm.id == data.id)
                .options(
                    selectinload(BookModelOrm.tag_books)  # Better than joinedload for collections
            )
        )
        book = result.scalars().first()
        return book.tag_books if book else []
    return []

async def paginator(session:AsyncSession, page:int):
    stmt = select(BookModelOrm).limit(per_page).offset((page-1)*per_page)
    result = await session.execute(stmt)
    books = result.scalars().all()
    return books