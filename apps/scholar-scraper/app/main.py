from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Scholar Scraper API")
app.include_router(router)

# uvicorn app.main:app --reload --port 8001
