"""
CORE API client for open access papers.
https://core.ac.uk/services/api
"""

import logging
from typing import Any, Dict, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, config, api_status
from .http_client import create_http_client

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
async def search_core(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search CORE for open access papers"""
    cache_key = f"core:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        url = "https://api.core.ac.uk/v3/search/works"
        params = {
            "q": query,
            "limit": limit,
            "fullText": True  # Only papers with full text
        }

        headers = {}
        if config.core_api_key:
            headers["Authorization"] = f"Bearer {config.core_api_key}"
        else:
            logger.warning("⚠️ CORE API key not configured, using free tier with limitations")

        async with create_http_client() as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                logger.warning("⚠️ CORE API rate limited")
                raise httpx.HTTPStatusError(f"Rate limited", request=response.request, response=response)

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("results", []):
                    # Only include if has downloadable PDF
                    download_url = item.get("downloadUrl")
                    if download_url:
                        result = {
                            "title": item.get("title", ""),
                            "authors": [author.get("name", "") for author in item.get("authors", [])],
                            "abstract": item.get("abstract", ""),
                            "year": item.get("yearPublished"),
                            "doi": item.get("doi"),
                            "pdf_url": download_url,
                            "source": "CORE",
                            "open_access": True,
                            "journal": item.get("journals", [{}])[0].get("title", "") if item.get("journals") else "",
                            "citation_count": item.get("citationCount", 0),
                            "url": item.get("magId")  # Microsoft Academic Graph ID
                        }
                        results.append(result)

                # Cache for 2 hours
                cache.set(cache_key, results, expire=7200)
                logger.info(f"✅ CORE: Found {len(results)} open access papers for '{query}'")
                return results
            else:
                logger.warning(f"❌ CORE API HTTP {response.status_code}: {response.text}")
                return []

    except httpx.HTTPStatusError:
        raise  # Let retry handle this
    except Exception as e:
        logger.warning(f"❌ CORE search failed: {e}")
        api_status["core"] = False
        return []