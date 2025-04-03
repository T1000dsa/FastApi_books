# venv/Scripts/activate | deactivate; venv -> 1 | 0
# pip install -U aiogram; -U when venv: 1 | -U if venv == True
# git add <file> | git add .
# git commit -m "vers. 009"
# git push origin main
# python3 -m venv venv
# venv/Scripts/activate.bat
# . venv/bin/activate
# virtualenv .env
# git ls-files | xargs wc -l
# pip install -r requirements.txt
# python -m uvicorn src.core.main:app --reload
# TODO1 Autorize and autentification [1, 1, 1, 1, 1] On jwt
# TODO2 Pagination in database and in html
# TODO3 Main page
# Mupltiply languages supporting
# TODO4 Recomendation
# TODO5 Cache
# TODO6 Celery
# TODO7 Rabbidmq or Kafka
# TODO8 search engine
# TODO9 Deploy

from fastapi import FastAPI
import logging 

from src.core.routers import router as main_router
from src.core.routers_core import router as core_router
from src.users.autentification import router as users_router
from src.core.middlewares.users import init_token_refresh_middleware


logger = logging.getLogger(__name__)
app = FastAPI()


init_token_refresh_middleware(app)
app.include_router(main_router)
app.include_router(core_router)
app.include_router(users_router)