# python -m venv venv
# venv/Scripts/activate.bat
# .venv/bin/activate
# git add <file> | git add .
# git commit -m "vers. 009"
# git push origin main
# git ls-files | xargs wc -l
# pip install -r requirements.txt
# python -m uvicorn src.core.main:app --reload
# TODO1 Autorize and autentification [1, 1, 1, 1, 1] Auth On authx
# TODO2 Pagination in database and in html [1, 1, 1, 1, 1] custom paginator
# TODO3 Main page [0, 1, 1, 1, 1] html+jinja2
# TODO4 Cache [1, 1, 1, 1, 1] Redis
# TODOEXTRA Make automatic books download
# TODO5 Celery [0, 0, 0, 0, 0]
# TODO6 Rabbidmq or Kafka [0, 0, 0, 0, 0]
# TODO7 search engine [0, 0, 0, 0, 0]
# TODO8 Mupltiply languages supporting [0, 0, 0, 0, 0]
# TODO9 Recomendation [0, 0, 0, 0, 0]

# global_TODO Deploy [0, 0, 0, 0, 0]

from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging 

from src.api.api_v1.endpoints.routers import router as main_router
from  src.api.api_v1.endpoints.routers_core import router as core_router
from src.api.api_v1.auth.autentification import router as users_router
from src.core.middlewares.users import init_token_refresh_middleware
from src.api.api_v1.auth.config import securityAuthx
from src.core.database.db_helper import db_helper


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield
    
    try:
        await db_helper.dispose()
        logger.debug("✅ Connection pool closed cleanly")
    except Exception as e:
        logger.warning(f"⚠️ Error closing connection pool: {e}")

app = FastAPI(lifespan=lifespan)
logger = logging.getLogger(__name__)

init_token_refresh_middleware(app)
securityAuthx.handle_errors(app)

app.include_router(main_router)
app.include_router(core_router)
app.include_router(users_router)