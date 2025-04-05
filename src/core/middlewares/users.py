from fastapi import FastAPI, Depends, Request
import logging

from src.api.api_v1.auth.utils import refresh_logic, clear_tokens_and_redirect, should_refresh_access_token
from src.core.config import (ACCESS_TYPE, REFRESH_TYPE, access_token_expire)
from src.core.database.db_helper import db_helper


logger = logging.getLogger(__name__)

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    async def auto_refresh_token(
        request: Request, 
        call_next):
        logger.debug(f"Incoming request to: {request.url}")
        # Skip auth for these paths

        public_paths = ['/login', '/register', '/static', '/docs', '/openapi.json']
        if any(request.url.path.startswith(path) for path in public_paths):
            logger.debug(f'Middleware skipped the: {request.url.path}')
            return await call_next(request)
        
        access_token = request.cookies.get(ACCESS_TYPE)
        refresh_token = request.cookies.get(REFRESH_TYPE)
        logger.debug('Middleware got the tokens')
        
        # Case 1: No tokens at all - allow through to login
        if not access_token and not refresh_token:
            if request.url.path != '/login':  # Prevent redirect loops
                return clear_tokens_and_redirect()
            return await call_next(request)
        
        try:
            # Case 2: Validate access token if exists
            try:
                new_token = await refresh_logic(request)
                if new_token:
                    logger.debug('before set cookies')
                    response = await call_next(request)
                    response.set_cookie(
                                key=ACCESS_TYPE,
                                value=new_token,
                                httponly=True,
                                secure=True,
                                samesite="lax",
                                path="/"
                            )
                    logger.debug('after set cookies')
                    return response
                else:
                    logger.debug('Continue')
                    return await call_next(request)

            except Exception as e:
                logger.error(f"Refresh failed: {e}")
            
            # Final fallback - clear tokens and redirect
            if request.url.path != '/login':
                return clear_tokens_and_redirect()
            return await call_next(request)
            
        except Exception as e:
            logger.error(f"Middleware error: {e}")
            if request.url.path != '/login':
                return clear_tokens_and_redirect()
            return await call_next(request)
