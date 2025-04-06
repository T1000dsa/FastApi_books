from fastapi import Request, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import RedirectResponse
from authx import RequestToken
from datetime import datetime, timedelta
from typing import Optional, Annotated
import logging
import jwt

from src.core.config import ACCESS_TYPE, REFRESH_TYPE, access_token_expire, refresh_time
from src.api.api_v1.orm.user_orm import select_data_user
from src.api.api_v1.auth.config import securityAuthx
from src.core.database.db_helper import db_helper


logger = logging.getLogger(__name__)


async def refresh_logic(
        request: Request, 
        ) -> Optional[str]:
    """Core refresh logic using refresh token"""
    #logger.debug('in refresh_logic')
    try:
        refresh_token = request.cookies.get(REFRESH_TYPE)
        if not refresh_token:
            logger.info("No refresh token found")
            return None # Better to raise exception or redirect to login
                
            # Verify refresh token
        payload = securityAuthx.verify_token(
                RequestToken(
                    token=refresh_token,
                    location="cookies",
                    type=REFRESH_TYPE
                ),
            verify_csrf=False
        )
            
        if not payload:
            logger.info("Invalid refresh token")
            return None
                
            # Get user data
        async with db_helper.session_factory() as session:
            user_data = await select_data_user(session, int(payload.sub))
            if not user_data:
                logger.info("User not found")
                return None
        
        should = should_refresh_access_token(request)
        if should:
            # Create new access token
            logger.debug('Before create_access_token')
            
            return securityAuthx.create_access_token(
                    **{'uid': str(user_data.id)}
            ).decode()
        
        return None
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        return None

def should_refresh_access_token(request: Request) -> bool:
    """More conservative refresh check"""
    access_token = request.cookies.get(ACCESS_TYPE)
    #if not access_token: # access tokens now exists eternal but anyways expired so this row useless
        #return True
        
    try:
        #logger.debug('in should_refresh_access_token')
        payload = jwt.decode(access_token, options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(payload['exp']) # 18:30:30
        remaining = (exp_time - datetime.now()) # 18:30:30 - 18:28:00 = 2:30 

        #logger.debug('Successfuly return True')
        return timedelta(minutes=refresh_time).seconds > remaining.seconds # True ; 1:00 < 2:30 -> False ; 1:00 > 0:44
    
    except jwt.ExpiredSignatureError:
        logger.info('Access token expired')
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
