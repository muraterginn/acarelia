# acarelia/common/models.py

from pydantic import BaseModel
from typing import List, Optional

class ScrapeRequest(BaseModel):
    job_id: str
    author: str

class JobResponse(BaseModel):
    job_id: str

class StatusResponse(BaseModel):
    job_id: str
    status: str

# class Paper(BaseModel):
#     title: str
#     year: Optional[int] = None
#     link: Optional[str] = None
#     citations: Optional[int] = None

# class ScrapeResult(BaseModel):
#     job_id: str
#     results: List[Paper]
