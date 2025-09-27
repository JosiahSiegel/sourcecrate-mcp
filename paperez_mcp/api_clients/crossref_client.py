"""
CrossRef API client for academic paper search.
"""

from typing import Any, Dict, List

from ..config import config
from .base_client import BaseAPIClient
from .http_client import create_http_client


class CrossRefClient(BaseAPIClient):
    """CrossRef API client with standardized patterns."""

    def __init__(self):
        super().__init__("CrossRef", cache_expire=3600)

    async def _perform_search(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
        """Perform CrossRef API search."""
        # Use CrossRef REST API directly
        url = "https://api.crossref.org/works"

        # Format query for phrase search - wrap in quotes if it contains multiple words
        formatted_query = query
        if ' ' in query.strip() and not (query.strip().startswith('"') and query.strip().endswith('"')):
            formatted_query = f'"{query}"'

        params = {
            "query": formatted_query,
            "rows": limit,
            "sort": "relevance",
            "order": "desc",
            "mailto": config.crossref_email  # Use polite pool
        }

        async with create_http_client() as client:
            response = await client.get(url, params=params)

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("message", {}).get("items", []):
                    paper_data = {
                        "title": item.get("title", [""])[0] if item.get("title") else "",
                        "authors": [
                            f"{author.get('given', '')} {author.get('family', '')}"
                            for author in item.get("author", [])
                        ],
                        "doi": item.get("DOI", ""),
                        "year": item.get("published-print", {}).get("date-parts", [[None]])[0][0] if item.get("published-print") else None,
                        "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                        "abstract": item.get("abstract", ""),
                        "citation_count": item.get("is-referenced-by-count", 0),
                        "url": f"https://doi.org/{item.get('DOI', '')}" if item.get("DOI") else "",
                        "publisher": item.get("publisher", "")
                    }
                    results.append(self._standardize_paper(paper_data))

                return results
            else:
                self.logger.warning(f"❌ CrossRef HTTP {response.status_code}")
                return []


# Create client instance
_crossref_client = CrossRefClient()


# Maintain backwards compatibility with existing function-based API
async def search_crossref(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search CrossRef API (primary source - most reliable)"""
    return await _crossref_client.search(query, limit)