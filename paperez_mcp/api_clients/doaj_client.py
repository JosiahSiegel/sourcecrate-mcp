"""
Directory of Open Access Journals API client.
https://doaj.org/api/v3/docs
"""

import logging
from typing import Any, Dict, List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, api_status
from .http_client import create_http_client

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
async def search_doaj(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search DOAJ for open access journal articles"""
    cache_key = f"doaj:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        url = "https://doaj.org/api/v3/search/articles"
        params = {
            "query": query,
            "pageSize": limit
        }

        async with create_http_client() as client:
            response = await client.get(url, params=params)

            if response.status_code == 429:
                logger.warning("⚠️ DOAJ API rate limited")
                raise httpx.HTTPStatusError(f"Rate limited", request=response.request, response=response)

            if response.status_code == 200:
                data = response.json()
                results = []

                for item in data.get("results", []):
                    bibjson = item.get("bibjson", {})

                    # Extract PDF URL from links
                    pdf_url = None
                    for link in bibjson.get("link", []):
                        if link.get("type") == "fulltext":
                            pdf_url = link.get("url")
                            break

                    # Only include articles with PDF links
                    if pdf_url:
                        result = {
                            "title": bibjson.get("title", ""),
                            "authors": [author.get("name", "") for author in bibjson.get("author", [])],
                            "abstract": bibjson.get("abstract", ""),
                            "year": bibjson.get("year"),
                            "doi": next((id["id"] for id in bibjson.get("identifier", [])
                                        if id.get("type") == "doi"), None),
                            "pdf_url": pdf_url,
                            "source": "DOAJ",
                            "open_access": True,
                            "journal": bibjson.get("journal", {}).get("title", ""),
                            "volume": bibjson.get("journal", {}).get("volume", ""),
                            "issue": bibjson.get("journal", {}).get("number", ""),
                            "pages": bibjson.get("start_page", ""),
                            "url": pdf_url  # Use PDF URL as the main URL
                        }
                        results.append(result)

                # Cache for 4 hours
                cache.set(cache_key, results, expire=14400)
                logger.info(f"✅ DOAJ: Found {len(results)} open access articles for '{query}'")
                return results
            else:
                logger.warning(f"❌ DOAJ API HTTP {response.status_code}: {response.text}")
                return []

    except httpx.HTTPStatusError:
        raise  # Let retry handle this
    except Exception as e:
        logger.warning(f"❌ DOAJ search failed: {e}")
        api_status["doaj"] = False
        return []