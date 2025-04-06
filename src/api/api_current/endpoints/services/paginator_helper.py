from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from src.core.database.db_helper import db_helper
from src.api.api_current.orm.db_orm import paginator, output_data
from src.core.config import per_page

async def get_paginated_books(
    session: AsyncSession = Depends(db_helper.session_getter),
    page: int=1
):
    paginated_books = await paginator(session, page)
    all_books = await output_data(session)
    lenght_data = len(all_books) / per_page

    if str(lenght_data).split('.')[1] != '0':
        lenght_data = int(lenght_data+1)

    lenght_data = int(lenght_data)

    data = {
            'current_page':page,
            'total_pages':lenght_data
        }
    return (data, paginated_books)