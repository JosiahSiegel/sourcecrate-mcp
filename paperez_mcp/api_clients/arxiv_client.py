"""
arXiv API client for academic paper search.
"""

import asyncio
import logging
from typing import Any

import arxiv
from tenacity import retry, stop_after_attempt, wait_exponential

# api_status is now managed by the configuration system
from .base_client import BaseAPIClient

logger = logging.getLogger(__name__)


class ArXivClient(BaseAPIClient):
    """ArXiv API client with enhanced PDF validation and metadata normalization"""

    def __init__(self) -> None:
        super().__init__("arXiv", cache_expire=21600)  # 6 hours cache

    async def _perform_search(
        self, query: str, limit: int, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Perform arXiv search with strategy fallback and PDF enhancement"""
        return await _search_with_strategy(query, limit, use_phrase=True)


async def _search_with_strategy(
    query: str, limit: int, use_phrase: bool = True
) -> list[dict[str, Any]]:
    """Internal search function with configurable phrase/keyword strategy"""

    def _search_arxiv() -> list[dict[str, Any]]:
        # Format query based on strategy
        formatted_query = query
        if " " in query.strip() and not (
            query.strip().startswith('"') and query.strip().endswith('"')
        ):
            if use_phrase:
                # For multi-word queries, use title and abstract search with phrase matching
                formatted_query = f'ti:"{query}" OR abs:"{query}"'
            else:
                # For keyword search, split words and search in title/abstract
                words = query.strip().split()
                title_terms = " AND ".join([f"ti:{word}" for word in words])
                abs_terms = " AND ".join([f"abs:{word}" for word in words])
                formatted_query = f"({title_terms}) OR ({abs_terms})"

        search = arxiv.Search(
            query=formatted_query,
            max_results=limit,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        results = []
        for paper in search.results():
            result = {
                "title": paper.title,
                "authors": [str(author) for author in paper.authors],
                "abstract": paper.summary,
                "year": paper.published.year if paper.published else None,
                "arxiv_id": paper.entry_id.split("/")[-1],
                "pdf_url": paper.pdf_url,
                "source": "arXiv",
                "categories": paper.categories,
                "url": paper.entry_id,
            }
            results.append(result)
        return results

    return await asyncio.to_thread(_search_arxiv)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_arxiv(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search arXiv with enhanced PDF validation and metadata normalization"""
    client = ArXivClient()

    try:
        # Try phrase search first
        results = await _search_with_strategy(query, limit, use_phrase=True)

        # If no results and multi-word query, try keyword search
        if len(results) == 0 and " " in query:
            logger.info(
                f"No results with phrase search for '{query}', trying keyword search"
            )
            results = await _search_with_strategy(query, limit, use_phrase=False)

        # Enhance results with PDF validation and metadata normalization
        enhanced_results = []
        for result in results:
            # Apply base client standardization (includes metadata normalization)
            standardized = client._standardize_paper(result)

            # Enhance with PDF validation (async operation)
            enhanced = await client._enhance_pdf_availability(standardized)
            enhanced_results.append(enhanced)

        logger.info(f"✅ arXiv: Found {len(enhanced_results)} results for '{query}'")
        return enhanced_results

    except Exception as e:
        logger.warning(f"❌ arXiv search failed: {e}")
        # api_status is now managed by config system
        return []
