from fastapi import Request, Response
from fastapi import FastAPI
import jwt
import logging
from datetime import datetime, timedelta
import time

from src.users.autentification import refresh
from src.core.config import refresh_close


logger = logging.getLogger(__name__)

def init_token_refresh_middleware(app: FastAPI):
    @app.middleware("http")
    async def auto_refresh_token(request: Request, call_next):

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        if process_time > 1.0:  # Log slow requests
            logger.warning(f"Slow request: {request.url} took {process_time}s")
            return response
        
        if 200 <= response.status_code < 400:
            if access_token := request.cookies.get("access_token"):
                try:
                    payload = jwt.decode(
                        access_token,
                        options={"verify_signature": False, "verify_exp": False}
                    )
                    exp_time = datetime.fromtimestamp(payload['exp'])
                    
                    if (time_remaining := exp_time - datetime.now()) < timedelta(minutes=refresh_close):
                        try:
                            new_token = await refresh(request)
                            
                            # Create new response if you need to modify cookies/headers
                            if isinstance(new_token, str):
                                new_response = Response(
                                    content=response.body if hasattr(response, 'body') else b'',
                                    status_code=response.status_code,
                                    headers=dict(response.headers),
                                    media_type=response.media_type
                                )
                                new_response.set_cookie(...)
                                return new_response
                            return new_token
                            
                        except Exception as e:
                            logger.error(f"Refresh failed: {e}")
                except jwt.PyJWTError as e:
                    logger.error(f"Token error: {e}")
        
        return response