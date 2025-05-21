from pydantic import BaseModel
from typing import List, Optional

class Article(BaseModel):
    title: str
    year: Optional[int]
    link: Optional[str]
    citations: Optional[int]
    doi: Optional[str]
    verified: bool
    open_access: bool
    text: Optional[str] = None


class Job(BaseModel):
    job_id: str
    author: str
    results: List[Article]
