from fastapi import FastAPI, Request
from authx import RequestToken
import logging
from authx.exceptions import JWTDecodeError
import jwt

from src.api.api_current.auth.utils import refresh_logic, clear_tokens_and_redirect

from src.core.config.config import (ACCESS_TYPE, REFRESH_TYPE)
from src.api.api_current.auth.config import securityAuthx


logger = logging.getLogger(__name__)

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    async def auto_refresh_token(
        request: Request, 
        call_next
    ):
        logger.info(f"Incoming request to: {request.url}")
        
        # Skip auth for these paths
        public_paths = ['/login', '/register', '/static', '/docs', '/openapi.json']
        if any(request.url.path.startswith(path) for path in public_paths):
            logger.info(f'Middleware skipped the: {request.url.path}')
            return await call_next(request)
        
        access_token = request.cookies.get(ACCESS_TYPE)
        refresh_token = request.cookies.get(REFRESH_TYPE)
        
        # Case 1: No tokens at all - redirect to login
        if not access_token and not refresh_token:
            if request.url.path != '/login':
                return clear_tokens_and_redirect()
            return await call_next(request)
        
        # Case 2: We have an access token - check if it's valid
        if access_token:
            try:
                # Verify the access token
                securityAuthx.verify_token(
                    RequestToken(
                        token=access_token,
                        location="cookies",
                        type=ACCESS_TYPE
                    ),
                    verify_csrf=False
                )
                # If valid, just proceed
                return await call_next(request)
            except (jwt.ExpiredSignatureError, JWTDecodeError):
                # Token is expired, will try to refresh
                pass
            except Exception as e:
                logger.error(f"Access token verification failed: {e}")
                if request.url.path != '/login':
                    return clear_tokens_and_redirect()
                return await call_next(request)
        
        # Case 3: Try to refresh the access token
        if refresh_token:
            try:
                new_access_token = await refresh_logic(request)
                if new_access_token:
                    logger.debug('Got new access token from refresh')
                    
                    # Clone the request with the new token in cookies
                    request.scope['headers'] = [
                        (k, v) for k, v in request.scope['headers'] 
                        if k.lower() != b'cookie'
                    ]
                    new_cookies = request.cookies.copy()
                    new_cookies[ACCESS_TYPE] = new_access_token
                    cookie_header = "; ".join(
                        [f"{k}={v}" for k, v in new_cookies.items()]
                    )
                    request.scope['headers'].append(
                        (b'cookie', cookie_header.encode('latin-1'))
                    )
                    
                    # Process the request with the new token
                    response = await call_next(request)
                    
                    # Set the cookie in the response too
                    response.set_cookie(
                        key=ACCESS_TYPE,
                        value=new_access_token,
                        httponly=True,
                        secure=True,
                        samesite="lax",
                        path="/"
                    )
                    logger.debug('Successfully set new access token')
                    return response
                
                logger.debug('Refresh failed - no new token received')
            except Exception as e:
                logger.error(f"Refresh failed: {e}")
        
        # If we get here, either:
        # - No refresh token available
        # - Refresh failed
        # - Both tokens are invalid
        if request.url.path != '/login':
            return clear_tokens_and_redirect()
        return await call_next(request)