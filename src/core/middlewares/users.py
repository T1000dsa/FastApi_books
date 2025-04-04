from fastapi import Request, Response
from fastapi import FastAPI, Depends, HTTPException
import jwt
import logging
from datetime import datetime, timedelta
import time

from src.api.api_v1.auth.utils import refresh_logic, handle_token_refresh, should_refresh_access_token
from src.core.config import refresh_time
from src.database_data.db_helper import db_helper
from src.core.config import (ACCESS_TYPE, REFRESH_TYPE, TOKEN_TYPE, refresh_token_expire, access_token_expire)


logger = logging.getLogger(__name__)

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    async def auto_refresh_token(request: Request, call_next):
        refresh_token = request.cookies.get(REFRESH_TYPE)
        
        # First try processing the request normally
        try:
            response = await call_next(request)
        except HTTPException as e:
            if e.status_code == 401:  # Only catch unauthorized errors
                if refresh_token:
                    return await handle_token_refresh(request)
            raise
        
        # If we got here, the request succeeded
        if 200 <= response.status_code < 400 and refresh_token:
            # Check if we should refresh proactively
            if should_refresh_access_token(request):
                response = await handle_token_refresh(request, response)
        
        return response