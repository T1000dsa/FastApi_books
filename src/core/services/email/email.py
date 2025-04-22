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
        if not settings.email.EMAIL_ENABLED:
            logger.warning("Email service disabled in configuration")
            return False

        try:
            msg = EmailMessage()
            msg['From'] = f"Book Service <{settings.email.EMAIL_FROM}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Always include plain text version
            msg.set_content(body)
            
            # Add HTML version if provided
            if html_body:
                msg.add_alternative(html_body, subtype='html')

            context = cls._create_secure_context()

            with smtplib.SMTP(
                settings.email.EMAIL_HOST,
                settings.email.EMAIL_PORT,
                timeout=settings.email.EMAIL_TIMEOUT
            ) as server:
                server.ehlo()
                
                if settings.email.EMAIL_USE_TLS:
                    server.starttls(context=context)
                    server.ehlo()  # Re-identify after STARTTLS
                
                server.login(
                    settings.email.EMAIL_USERNAME,
                    settings.email.EMAIL_PASSWORD
                )
                server.send_message(msg)
                logger.info(f"Email successfully sent to {to_email}")
                return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Failed. Details:")
            logger.error(f"Code: {e.smtp_code}, Message: {e.smtp_error.decode()}")
            logger.error("Verify:")
            logger.error(f"1. Username: {settings.email.EMAIL_USERNAME}")
            logger.error(f"2. Password length: {len(settings.email.EMAIL_PASSWORD or '')} chars")
            logger.error("3. App password generated for 'Mail'")
            logger.error("4. Less secure apps enabled (if no 2FA)")
            return False
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}", exc_info=True)
            return False