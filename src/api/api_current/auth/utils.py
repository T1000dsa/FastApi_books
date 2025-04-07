from fastapi import Request, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import RedirectResponse
from authx import RequestToken
from datetime import datetime, timedelta
from typing import Optional, Annotated
import logging
from authx.exceptions import JWTDecodeError
import jwt

from src.core.config import ACCESS_TYPE, REFRESH_TYPE
from src.api.api_current.orm.user_orm import select_data_user
from src.api.api_current.auth.config import securityAuthx
from src.core.database.db_helper import db_helper


logger = logging.getLogger(__name__)


async def refresh_logic(request: Request) -> Optional[str]:
    """Core refresh logic using refresh token"""
    logger.debug('in refresh_logic')
    try:
        refresh_token = request.cookies.get(REFRESH_TYPE)

        if not refresh_token:
            logger.info("No refresh token found")
            return None
        
        #if should_refresh_access_token(request):
            # Verify refresh token (skip access token verification)

        logger.debug('before token verification')

        payload = securityAuthx.verify_token(
                    RequestToken(
                        token=refresh_token,
                        location="cookies",
                        type=REFRESH_TYPE
                    ),
                    verify_csrf=False
                )
        logger.debug('after token verification')
                
        if not payload:
            logger.info("Invalid refresh token")
            return None
                    
            # Get user data
        async with db_helper.session_factory() as session:
            user_data = await select_data_user(session, int(payload.sub))
            if not user_data:
                logger.info("User not found")
                return None
        logger.debug('create_access_token')
        return securityAuthx.create_access_token(
                    **{'uid': str(user_data.id)}
            )
        

    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        return None

def should_refresh_access_token(request: Request) -> bool: # Legacy-function

    access_token = request.cookies.get(ACCESS_TYPE)

    try:
        logger.debug('in should_refresh_access_token')
        payload = securityAuthx.verify_token(
                    RequestToken(
                        token=access_token,
                        location="cookies",
                        type=ACCESS_TYPE
                    ),
                    verify_csrf=False
                )
        exp_time = datetime.fromtimestamp(payload.exp.timestamp()) # 18:30:30

        remaining = (exp_time - datetime.now()).seconds # 18:30:30 - 18:28:00 = 2:30 
        logger.debug(f'{timedelta(minutes=0).seconds} {remaining}')

        return timedelta(seconds=0).seconds > remaining
    
    except (jwt.ExpiredSignatureError, JWTDecodeError) as err:
        logger.error(f"Access token expired: {err}")
        return True
    
    except Exception as err:
        logger.error(f'Something went wrong {err}')
        raise err



def clear_tokens_and_redirect() -> Response:
    """Clear invalid tokens and redirect to login"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(ACCESS_TYPE)
    response.delete_cookie(REFRESH_TYPE)
    return response
