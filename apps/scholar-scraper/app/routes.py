from fastapi import APIRouter, Query
from app.models import ScholarResponse, Paper
from app.scraper.fetch_router import fetch_publications

router = APIRouter()

@router.get("/scrape", response_model=ScholarResponse)
async def scrape_scholar(author: str = Query(..., description="Author name")):
    publications = await fetch_publications(author)
    return ScholarResponse(author=author, results=publications)
