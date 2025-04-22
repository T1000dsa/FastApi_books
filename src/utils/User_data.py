from fastapi import Request
import logging
from authx import RequestToken

from src.core.config.config import ACCESS_TYPE
from src.api.api_current.auth.config import securityAuthx


logger = logging.getLogger(__name__)

async def gather_user_data_from_cookies(request:Request):
    try:
        access_token = request.cookies.get(ACCESS_TYPE)
        payload = securityAuthx.verify_token(
                    RequestToken(
                        token=access_token,
                        location="cookies",
                        type=ACCESS_TYPE
                    ),
                    verify_csrf=False
                )
    except Exception as err:
        logger.error(f"Error raised: {err}")
        raise err
    
    return payload