from scholarly import scholarly
from .base import BaseScholarScraper

class ScholarlyScraper(BaseScholarScraper):
    async def fetch_publications(self, author_name: str):
        search_query = scholarly.search_author(author_name)
        author = next(search_query)
        filled_author = scholarly.fill(author, sections=["publications"])
        
        publications = []
        for pub in filled_author.get("publications", []):
            bib = pub.get("bib", {})
            publications.append({
                "title": bib.get("title", "Unknown"),
                "year": bib.get("pub_year"),
                "link": pub.get("eprint_url"),
                "citations": pub.get("num_citations")
            })
        return publications
