from fastapi import APIRouter, Request, HTTPException
from uuid import uuid4
from datetime import datetime
from common.models import ScrapeRequest, JobResponse
from app.logger import logger

router = APIRouter()

@router.post("/scan", response_model=JobResponse)
async def scan(request: Request, author: str):
    job_id = uuid4().hex
    now_str = datetime.now().strftime("%d-%m-%Y - %H:%M:%S")
    await request.app.state.job_store.set_field(job_id, "job_start_time", now_str)
    payload = ScrapeRequest(job_id=job_id, author=author).dict()
    try:
        # app.state.rabbitPublisher üzerinden publish işlemi
        await request.app.state.rabbitPublisher.publish("scrape_requests", payload)
        logger.info(f"Published scrape job {job_id} for author '{author}'")
        return JobResponse(job_id=job_id)
    except Exception as e:
        logger.error(f"Failed to publish message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")