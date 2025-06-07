from fastapi import APIRouter
import json

from common.models import (
    StatusResponse,
    AIAnalyzeStatusResponse,
    PlagiarismCheckStatusResponse,
    JobDataResponse,
)
from common.job_store import JobStore
from app.config import settings

router = APIRouter()
job_store = JobStore(settings.REDIS_URL)


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_state(job_id: str):
    val = await job_store.get_field(job_id, "state")
    return StatusResponse(job_id=job_id, status=val or "pending")


@router.get("/ai_analyze_status/{job_id}", response_model=AIAnalyzeStatusResponse)
async def get_ai_analyze_status(job_id: str):
    val = await job_store.get_field(job_id, "ai_analyze_status")
    return AIAnalyzeStatusResponse(job_id=job_id, ai_analyze_status=val or "pending")


@router.get("/plagiarism_check_status/{job_id}", response_model=PlagiarismCheckStatusResponse)
async def get_plagiarism_check_status(job_id: str):
    val = await job_store.get_field(job_id, "plagiarism_check_status")
    return PlagiarismCheckStatusResponse(
        job_id=job_id,
        plagiarism_check_status=val or "pending"
    )


@router.get("/job_data/{job_id}", response_model=JobDataResponse)
async def get_job_data(job_id: str):
    data_str = await job_store.get_field(job_id, "job_data")
    try:
        data = json.loads(data_str) if data_str else {}
    except json.JSONDecodeError:
        # fall back to returning raw string if it wasn't valid JSON
        data = {"raw": data_str}
    return JobDataResponse(job_id=job_id, job_data=data)
