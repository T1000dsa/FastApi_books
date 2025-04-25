from celery import shared_task
from src.core.services.email.email import EmailService
import logging
from typing import Optional
import smtplib

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, autoretry_for=(Exception,), retry_backoff=True)
async def send_email_task(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Enhanced email task with better error handling
    """
    # Input validation
    if not to_email or not isinstance(to_email, str):
        logger.error(f"Invalid email address provided: {to_email}")
        return False
    
    try:
        success = await EmailService.send_email(
            to_email=to_email.strip(),
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        if not success:
            if self.request.retries < self.max_retries:
                logger.warning(f"Retry {self.request.retries + 1} for {to_email}")
                raise self.retry(exc=Exception("Temporary email failure"))
            return False
            
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Permanent authentication failure - aborting")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient refused: {e.recipients}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return False