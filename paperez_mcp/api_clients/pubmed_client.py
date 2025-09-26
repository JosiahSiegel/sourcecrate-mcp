"""
PubMed API client for biomedical literature search.
"""

import asyncio
import logging
from typing import Any, Dict, List

from pymed import PubMed
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, config, api_status

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_pubmed(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search PubMed for biomedical literature"""
    cache_key = f"pubmed:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        def _search_pubmed():
            pubmed = PubMed(tool="scholarly-mcp", email=config.crossref_email)
            results = []

            for article in pubmed.query(query, max_results=limit):
                result = {
                    "title": article.title,
                    "authors": [str(author) for author in (article.authors or [])],
                    "abstract": article.abstract,
                    "journal": article.journal,
                    "year": article.publication_date.year if article.publication_date else None,
                    "pubmed_id": article.pubmed_id,
                    "doi": article.doi,
                    "source": "PubMed",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id}/" if article.pubmed_id else ""
                }
                results.append(result)
            return results

        results = await asyncio.to_thread(_search_pubmed)

        # Cache for 1 hour
        cache.set(cache_key, results, expire=3600)
        logger.info(f"✅ PubMed: Found {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.warning(f"❌ PubMed search failed: {e}")
        api_status["pubmed"] = False
        return []