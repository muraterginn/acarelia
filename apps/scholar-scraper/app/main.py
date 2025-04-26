from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Scholar Scraper API")
app.include_router(router)

# uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
