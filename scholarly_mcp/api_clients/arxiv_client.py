"""
arXiv API client for academic paper search.
"""

import asyncio
import logging
from typing import Any, Dict, List

import arxiv
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, api_status

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_arxiv(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search arXiv using official library"""
    cache_key = f"arxiv:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        def _search_arxiv():
            search = arxiv.Search(
                query=query,
                max_results=limit,
                sort_by=arxiv.SortCriterion.Relevance
            )

            results = []
            for paper in search.results():
                result = {
                    "title": paper.title,
                    "authors": [str(author) for author in paper.authors],
                    "abstract": paper.summary,
                    "year": paper.published.year if paper.published else None,
                    "arxiv_id": paper.entry_id.split('/')[-1],
                    "pdf_url": paper.pdf_url,
                    "source": "arXiv",
                    "categories": paper.categories,
                    "url": paper.entry_id
                }
                results.append(result)
            return results

        results = await asyncio.to_thread(_search_arxiv)

        # Cache for 6 hours (arXiv updates once daily)
        cache.set(cache_key, results, expire=21600)
        logger.info(f"✅ arXiv: Found {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.warning(f"❌ arXiv search failed: {e}")
        api_status["arxiv"] = False
        return []