from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import RedirectResponse
from authx import RequestToken
from datetime import datetime, timedelta
from typing import Optional
import logging
import jwt


from src.core.config import ACCESS_TYPE, REFRESH_TYPE, access_token_expire
from src.api.api_v1.auth.user_orm import select_data_user
from src.api.api_v1.auth.config import securityAuthx
from src.database_data.db_helper import db_helper


logger = logging.getLogger(__name__)

async def refresh_logic(request: Request, session: AsyncSession) -> Optional[str]:
    """Core refresh logic using refresh token"""
    try:
        refresh_token = request.cookies.get(REFRESH_TYPE)
        if not refresh_token:
            return None
            
        # Create properly validated request token
        request_token = RequestToken(
            token=refresh_token,
            location="cookies",
            type=REFRESH_TYPE
        )
        
        # Verify refresh token (this should ignore access token expiration)
        payload = securityAuthx.verify_token(
            request_token,
            verify_csrf=False,
            verify_type=REFRESH_TYPE
        )
        
        if not payload:
            return None
            
        # Get user data
        user_data = await select_data_user(session, int(payload.sub))
        if not user_data:
            return None

        # Create new access token
        return securityAuthx.create_access_token(
            **{'uid': str(user_data.id)}
        ).decode()
        
    except jwt.ExpiredSignatureError:
        logger.debug("Refresh token expired")
        return None
    except Exception as e:
        logger.error(f"Refresh failed: {e}", exc_info=True)
        return None
    

async def handle_token_refresh(request: Request, existing_response: Response = None) -> Response:
    """Handle token refresh when access is expired"""
    refresh_token = request.cookies.get(REFRESH_TYPE)
    if not refresh_token:
        #return clear_tokens_and_redirect()
        pass
    
    try:
        async with db_helper.session_factory() as session:
            new_access_token = await refresh_logic(request, session)
            if not new_access_token:
                #return clear_tokens_and_redirect()
                pass
            
            response = existing_response or Response(status_code=204)
            response.set_cookie(
                key=ACCESS_TYPE,
                value=new_access_token,
                httponly=True,
                secure=True,
                max_age=access_token_expire
            )
            return response
            
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        #return clear_tokens_and_redirect()

def should_refresh_access_token(request: Request) -> bool:
    """Check if we should refresh access token proactively"""
    access_token = request.cookies.get(ACCESS_TYPE)
    if not access_token:
        return True
        
    try:
        payload = jwt.decode(access_token, options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(payload['exp'])
        return (exp_time - datetime.now()) < timedelta(minutes=5)
    except:
        return True

#def clear_tokens_and_redirect() -> Response:
    """Clear invalid tokens and redirect to login"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(ACCESS_TYPE)
    response.delete_cookie(REFRESH_TYPE)
    return response