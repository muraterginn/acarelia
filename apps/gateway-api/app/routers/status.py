from fastapi import APIRouter
from common.models import StatusResponse
from common.state_store import StateStore
from app.config import settings

router = APIRouter()
store = StateStore(settings.REDIS_URL)

@router.get("/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str):
    s = await store.get_status(job_id)
    return StatusResponse(job_id=job_id, status=s)