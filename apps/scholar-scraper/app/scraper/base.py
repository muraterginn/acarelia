from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScholarScraper(ABC):
    @abstractmethod
    async def fetch_publications(self, author_name: str) -> List[Dict]:
        pass
