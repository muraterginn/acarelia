from fastapi import APIRouter
from common.models import StatusResponse
from app.services.state_store import get_status

router = APIRouter()

@router.get("/status/{job_id}", response_model=StatusResponse)
async def status(job_id: str):
    status = await get_status(job_id)
    return StatusResponse(job_id=job_id, status=status)