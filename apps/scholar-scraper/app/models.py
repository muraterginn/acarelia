from pydantic import BaseModel
from typing import List, Optional

class Paper(BaseModel):
    title: str
    year: Optional[int] = None
    link: Optional[str] = None
    citations: Optional[int] = None

class ScholarResponse(BaseModel):
    author: str
    results: List[Paper]
