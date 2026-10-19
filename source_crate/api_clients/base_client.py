"""
Base API client class providing common functionality for all academic database clients.
Standardizes retry logic, caching, error handling, and status tracking.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from source_crate.utils.json_cache import cache

from ..utils.metadata_normalizer import metadata_normalizer
from ..utils.pdf_validator import pdf_validator

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """
    Abstract base class for academic database API clients.

    Provides common functionality:
    - Standardized caching with configurable expiration
    - Consistent retry logic with exponential backoff
    - Error handling and status tracking
    - Logging patterns
    """

    def __init__(self, source_name: str, cache_expire: int = 3600):
        """
        Initialize base client.

        Args:
            source_name: Name of the source (e.g., "CrossRef", "PubMed")
            cache_expire: Cache expiration time in seconds (default: 1 hour)
        """
        self.source_name = source_name
        self.cache_expire = cache_expire
        self.logger = logging.getLogger(f"{__name__}.{source_name}")

    def _get_cache_key(self, query: str, limit: int, **kwargs: Any) -> str:
        """Generate standardized cache key."""
        extra_params = "_".join(
            f"{k}:{v}" for k, v in sorted(kwargs.items()) if v is not None
        )
        base_key = f"{self.source_name.lower()}:{query}:{limit}"
        return f"{base_key}_{extra_params}" if extra_params else base_key

    def _get_cached_result(self, cache_key: str) -> list[dict[str, Any]] | None:
        """Retrieve cached result if available."""
        cached = cache.get(cache_key)
        if cached:
            self.logger.debug(f"Cache hit for {cache_key}")
            return cached  # type: ignore[no-any-return]
        return None

    def _cache_result(self, cache_key: str, result: list[dict[str, Any]]) -> None:
        """Cache the search result."""
        cache.set(cache_key, result, expire=self.cache_expire)
        self.logger.debug(f"Cached {len(result)} results for {cache_key}")

    def _log_success(self, query: str, result_count: int, **kwargs: Any) -> None:
        """Log successful search with consistent format."""
        extra_info = " ".join(f"{k}={v}" for k, v in kwargs.items() if v is not None)
        extra_str = f" ({extra_info})" if extra_info else ""
        self.logger.info(
            f"✅ {self.source_name}: Found {result_count} results for '{query}'{extra_str}"
        )

    def _log_failure(self, query: str, error: Exception) -> None:
        """Log search failure and update API status."""
        self.logger.warning(
            f"❌ {self.source_name} search failed for '{query}': {error}"
        )
        # API status is now managed by config system
        # api_status[self.source_name.lower().replace(" ", "_")] = False

    def _log_no_results(self, query: str) -> None:
        """Log when no results are found."""
        self.logger.info(f"🔍 {self.source_name}: No results found for '{query}'")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def search(
        self, query: str, limit: int = 5, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """
        Main search method with caching and error handling.

        Args:
            query: Search query string
            limit: Maximum number of results to return
            **kwargs: Additional search parameters specific to each client

        Returns:
            List of standardized paper dictionaries
        """
        # Check cache first
        cache_key = self._get_cache_key(query, limit, **kwargs)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result  # type: ignore[no-any-return]

        try:
            # Perform the actual search (implemented by subclasses)
            results = await self._perform_search(query, limit, **kwargs)

            # Cache and log results
            if results:
                self._cache_result(cache_key, results)
                self._log_success(query, len(results), **kwargs)
            else:
                self._log_no_results(query)

            return results

        except Exception as e:
            self._log_failure(query, e)
            return []

    @abstractmethod
    async def _perform_search(
        self, query: str, limit: int, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """
        Perform the actual search implementation.

        Must be implemented by each API client subclass.
        Should return a list of standardized paper dictionaries.
        """
        pass

    def _standardize_paper(self, paper_data: dict[str, Any]) -> dict[str, Any]:
        """
        Standardize paper data format across all sources with metadata normalization.

        Args:
            paper_data: Raw paper data from the API

        Returns:
            Standardized and normalized paper dictionary with consistent fields
        """
        # Basic standardization
        standardized = {
            "title": paper_data.get("title", ""),
            "authors": paper_data.get("authors", []),
            "abstract": paper_data.get("abstract", ""),
            "journal": paper_data.get("journal", ""),
            "year": paper_data.get("year"),
            "doi": paper_data.get("doi"),
            "url": paper_data.get("url", ""),
            "pdf_url": paper_data.get("pdf_url"),
            "open_access_pdf": paper_data.get("open_access_pdf"),
            "citation_count": paper_data.get("citation_count", 0),
            "source": self.source_name,
            # Include any source-specific fields
            **{
                k: v
                for k, v in paper_data.items()
                if k
                not in [
                    "title",
                    "authors",
                    "abstract",
                    "journal",
                    "year",
                    "doi",
                    "url",
                    "pdf_url",
                    "open_access_pdf",
                    "citation_count",
                    "source",
                ]
            },
        }

        # Apply metadata normalization
        normalized = metadata_normalizer.normalize_paper_metadata(standardized)

        # Note: PDF validation is async and expensive, so it's not done here
        # Instead, it should be done when specifically needed or in batch processing

        return normalized

    async def _enhance_pdf_availability(
        self, paper_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Enhance paper data with validated PDF URLs (async operation)

        Args:
            paper_data: Paper metadata dictionary

        Returns:
            Enhanced paper data with validated PDF information
        """
        return await pdf_validator.enhance_pdf_availability(paper_data)
