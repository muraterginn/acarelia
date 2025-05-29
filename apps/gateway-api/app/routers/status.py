from fastapi import APIRouter
from common.models import StatusResponse
from common.job_store import JobStore
from app.config import settings

router = APIRouter()
job_store = JobStore(settings.REDIS_URL)

@router.get("/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str):
    val = await job_store.get_field(job_id, "state")
    return StatusResponse(job_id=job_id, status=val or "pending")