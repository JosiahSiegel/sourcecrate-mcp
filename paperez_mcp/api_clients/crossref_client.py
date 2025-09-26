"""
CrossRef API client for academic paper search.
"""

import logging
from typing import Any, Dict, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, config, api_status
from .http_client import create_http_client

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_crossref(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search CrossRef API (primary source - most reliable)"""
    cache_key = f"crossref:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
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
                    result = {
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
                        "source": "CrossRef",
                        "publisher": item.get("publisher", "")
                    }
                    results.append(result)

                # Cache for 1 hour
                cache.set(cache_key, results, expire=3600)
                logger.info(f"✅ CrossRef: Found {len(results)} results for '{query}'")
                return results
            else:
                logger.warning(f"❌ CrossRef HTTP {response.status_code}")
                return []

    except Exception as e:
        logger.warning(f"❌ CrossRef search failed: {e}")
        api_status["crossref"] = False
        return []