import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.services.task_queue.celery_fastapi import celery_app
from src.core.config.config import settings
from src.core.services.database.models.user_models import UserModel
from src.core.services.database.models.models import BookModelOrm
from src.core.services.database.db_helper import db_helper
from src.core.services.cache.redis_fastapi import redis

# Helper function to run async DB operations in sync context
def async_to_sync_db_operation(async_func):
    """Run async DB operations in Celery's sync context"""
    from asgiref.sync import sync_to_async
    import asyncio
    
    async def wrapper(*args, **kwargs):
        async with db_helper.session_getter() as session:
            return await async_func(session, *args, **kwargs)
    
    return asyncio.run(wrapper())

@celery_app.task(bind=True)
def send_email_notification(self, user_id: int, subject: str, message: str):
    """Send email notification to a specific user"""
    try:
        # Get user email (async operation in sync context)
        user_email = async_to_sync_db_operation(get_user_email)(user_id)
        
        if not user_email:
            raise ValueError(f"User {user_id} has no email address")
        
        # Email sending (synchronous)
        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = settings.email_settings.sender
        msg['To'] = user_email
        
        with smtplib.SMTP(
            host=settings.email_settings.host,
            port=settings.email_settings.port
        ) as server:
            if settings.email_settings.use_tls:
                server.starttls()
            if settings.email_settings.username:
                server.login(
                    settings.email_settings.username,
                    settings.email_settings.password
                )
            server.send_message(msg)
            
        return {"status": "success", "user_id": user_id}
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)

async def get_user_email(session: AsyncSession, user_id: int) -> str | None:
    """Async helper to get user email"""
    result = await session.execute(
        select(UserModel.mail).where(UserModel.id == user_id)
    )
    return result.scalar_one_or_none()

@celery_app.task
def process_book_upload(book_id: int):
    """Process uploaded book (generate thumbnails, extract metadata, etc.)"""
    try:
        result = async_to_sync_db_operation(process_book_async)(book_id)
        redis.set(f"book:{book_id}:status", "processed", ex=3600)
        return result
    except Exception as e:
        raise

async def process_book_async(session: AsyncSession, book_id: int):
    """Async book processing logic"""
    book = await session.execute(
        select(BookModelOrm).where(BookModelOrm.id == book_id)
    ).scalar_one_or_none()
    
    if not book:
        raise ValueError(f"Book {book_id} not found")
    
    book.processed = True
    await session.commit()
    return {"book_id": book_id, "status": "processed"}

@celery_app.task
def deactivate_inactive_users():
    """Periodic task to deactivate inactive users"""
    try:
        result = async_to_sync_db_operation(deactivate_users_async)
        return result
    except Exception as e:
        raise

async def deactivate_users_async(session: AsyncSession):
    """Async user deactivation logic"""
    inactive_period = datetime.utcnow() - timedelta(days=365)
    result = await session.execute(
        update(UserModel)
        .where(UserModel.last_time_login < inactive_period)
        .values(is_active=False)
        .returning(UserModel.id)
    )
    await session.commit()
    return {"deactivated_users": len(result.scalars().all())}