# venv/Scripts/activate | deactivate; venv -> 1 | 0
# pip install -U aiogram; -U when venv: 1 | -U if venv == True
# git add <file> | git add .
# git commit -m "description" current vers. 006
# git push origin main
# python3 -m venv venv
# venv/Scripts/activate.bat
# . venv/bin/activate
# virtualenv .env
# git ls-files | xargs wc -l
# pip install -r requirements.txt
# python -m uvicorn src.core.main:app --reload
# TODO1 Autorize and autentification [0, 0, 1, 1, 1]
# TODO2 Pagination in database and in html
# TODO3 Main page
# Mupltiply languages supporting
# TODO4 Recomendation
# TODO5 Cache
# TODO6 Celery
# TODO7 Rabbidmq or Kafka
# TODO8 Deploy

from fastapi import FastAPI
from src.core.routers import router as main_router
from src.core.routers_core import router as core_router
from src.users.autentification import router as users_router


app = FastAPI()
app.include_router(main_router)
app.include_router(core_router)
app.include_router(users_router)