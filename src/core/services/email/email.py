import smtplib
import ssl
from email.message import EmailMessage
from src.core.config.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def _create_secure_context() -> ssl.SSLContext:
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        return context

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        # Add input validation
        if not to_email or not isinstance(to_email, str):
            logger.error("Invalid recipient email address")
            return False
        
        if not settings.email.EMAIL_ENABLED:
            logger.warning("Email service disabled in configuration")
            return False

        try:
            msg = EmailMessage()
            msg['From'] = f"Book Service <{settings.email.EMAIL_FROM}>"
            msg['To'] = to_email.strip()  # Clean whitespace
            msg['Subject'] = subject
            
            # Set content with explicit charset
            msg.set_content(body, charset='utf-8')
            
            if html_body:
                msg.add_alternative(html_body, subtype='html', charset='utf-8')

            # Verify message before sending
            logger.debug(f"Prepared email message:\nFrom: {msg['From']}\nTo: {msg['To']}\nSubject: {msg['Subject']}")

            context = cls._create_secure_context()

            with smtplib.SMTP(
                settings.email.EMAIL_HOST,
                settings.email.EMAIL_PORT,
                timeout=settings.email.EMAIL_TIMEOUT
            ) as server:
                server.ehlo()
                
                if settings.email.EMAIL_USE_TLS:
                    server.starttls(context=context)
                    server.ehlo()
                
                # Debug login
                logger.debug(f"Attempting login with user: {settings.email.EMAIL_USERNAME}")
                server.login(
                    settings.email.EMAIL_USERNAME,
                    settings.email.EMAIL_PASSWORD
                )
                
                # Debug before sending
                logger.debug(f"Sending email to {to_email}")
                server.send_message(msg)
                logger.info(f"Email successfully sent to {to_email}")
                return True

        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return False