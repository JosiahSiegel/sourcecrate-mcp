"""
Semantic Scholar API client for academic paper search.
"""

import logging
from typing import Any, Dict, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, config, api_status
from .http_client import create_http_client

logger = logging.getLogger(__name__)


async def _search_semantic_scholar_internal(query: str, limit: int) -> List[Dict[str, Any]]:
    """Internal search function for Semantic Scholar"""
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query,
        "limit": limit,
        "fields": "paperId,title,authors,year,abstract,venue,citationCount,url,openAccessPdf"
    }

    headers = {}
    if config.semantic_scholar_api_key:
        headers["x-api-key"] = config.semantic_scholar_api_key

    async with create_http_client() as client:
        response = await client.get(url, params=params, headers=headers)

        if response.status_code == 429:
            logger.warning("⚠️ Semantic Scholar rate limited")
            raise httpx.HTTPStatusError(f"Rate limited", request=response.request, response=response)

        if response.status_code == 200:
            data = response.json()
            results = []

            for paper in data.get("data", []):
                result = {
                    "title": paper.get("title", ""),
                    "authors": [author.get("name", "") for author in paper.get("authors", [])],
                    "year": paper.get("year"),
                    "abstract": paper.get("abstract", ""),
                    "venue": paper.get("venue", ""),
                    "citation_count": paper.get("citationCount", 0),
                    "url": paper.get("url", ""),
                    "source": "Semantic Scholar",
                    "paper_id": paper.get("paperId"),
                    "open_access_pdf": paper.get("openAccessPdf", {}).get("url") if paper.get("openAccessPdf") else None
                }
                results.append(result)

            return results
        else:
            logger.warning(f"❌ Semantic Scholar HTTP {response.status_code}")
            return []


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
async def search_semantic_scholar(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search Semantic Scholar with fallback from phrase to keyword search"""
    cache_key = f"semantic:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # Try phrase search first
        formatted_query = query
        if ' ' in query.strip() and not (query.strip().startswith('"') and query.strip().endswith('"')):
            formatted_query = f'"{query}"'

        results = await _search_semantic_scholar_internal(formatted_query, limit)

        # If no results with phrase search, try without quotes
        if len(results) == 0 and ' ' in query:
            logger.info(f"No results with phrase search for '{query}', trying keyword search")
            results = await _search_semantic_scholar_internal(query, limit)

        # Cache for 1 hour
        cache.set(cache_key, results, expire=3600)
        logger.info(f"✅ Semantic Scholar: Found {len(results)} results for '{query}'")
        return results

    except httpx.HTTPStatusError:
        raise  # Let retry handle this
    except Exception as e:
        logger.warning(f"❌ Semantic Scholar search failed: {e}")
        api_status["semantic_scholar"] = False
        return []