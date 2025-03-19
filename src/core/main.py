# venv/Scripts/activate | deactivate; venv -> 1 | 0
# pip install -U aiogram; -U when venv: 1 | -U if venv == True
# git add <file> | git add .
# git commit -m "description" current vers. 003
# git push origin main
# python3 -m venv venv
# venv/Scripts/activate.bat
# . venv/bin/activate
# virtualenv .env
# git ls-files | xargs wc -l
# pip install -r requirements.txt
# python -m uvicorn src.core.main:app --reload
from fastapi import FastAPI
from src.core.routers import router as main_router


app = FastAPI()
app.include_router(main_router)

