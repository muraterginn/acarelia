from pydantic import BaseModel
from typing import Dict, Any, Optional

class ScrapeRequest(BaseModel):
    job_id: str
    author: str

class JobResponse(BaseModel):
    job_id: str

class StatusResponse(BaseModel):
    job_id: str
    status: str

class AIAnalyzeStatusResponse(BaseModel):
    job_id: str
    ai_analyze_status: str

class PlagiarismCheckStatusResponse(BaseModel):
    job_id: str
    plagiarism_check_status: str

class JobDataResponse(BaseModel):
    job_id: str
    job_data: Dict[str, Any]
