"""
Comprehensive search engine that queries multiple academic databases.
"""

import asyncio
import logging
from typing import Any

from ..api_clients.arxiv_client import search_arxiv
from ..api_clients.pubmed_client import search_pubmed, search_pubmed_central
from ..config import api_status, get_search_service
from ..config.settings import config
from .pdf_processor import extract_pdf_text
from .query_cache import query_cache
from .source_health_monitor import health_monitor

logger = logging.getLogger(__name__)


# Placeholder functions for missing search clients
async def search_semantic_scholar(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Placeholder for semantic scholar search - to be implemented"""
    logger.warning("Semantic Scholar search not implemented yet")
    return []


async def search_clinicaltrials(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Placeholder for clinical trials search - to be implemented"""
    logger.warning("Clinical trials search not implemented yet")
    return []


async def comprehensive_search_internal(
    query: str, limit: int = 5, include_full_text: bool = False
) -> dict[str, Any]:
    """
    Comprehensive search across multiple academic databases with intelligent routing and fallback support.
    Now includes intelligent caching for improved performance.

    Args:
        query: Search query for publications
        limit: Maximum number of results to return (default: 5)
        include_full_text: Whether to attempt full text extraction (default: False)

    Returns:
        Dictionary with search results and metadata from multiple sources
    """

    # Check cache first for quick results
    cache_params = {"include_full_text": include_full_text}
    cached_result = query_cache.get_cached_result(query, limit, cache_params)

    if cached_result:
        logger.info(f"🎯 Returning cached result for query: '{query}'")
        return cached_result

    # Cache miss - perform actual search
    logger.info(f"🔍 Performing fresh search for query: '{query}' (limit: {limit})")

    all_results = []
    remaining_limit = limit

    # Get search functions from unified config system
    search_service = get_search_service()
    search_functions = search_service.get_search_functions()

    # Use BM25 ranking for intelligent source prioritization
    try:
        from .bm25_ranker import BM25SourceRanker

        bm25_ranker = BM25SourceRanker()
        # Get list of available source names (without search_ prefix)
        available_source_names = []
        for source_name in search_functions.keys():
            if api_status.get(source_name, True):  # Only include enabled sources
                actual_source_name = (
                    source_name.replace("search_", "")
                    if source_name.startswith("search_")
                    else source_name
                )
                available_source_names.append(actual_source_name)

        # Get BM25 rankings for the query
        source_rankings = bm25_ranker.rank_sources(query, available_source_names)
        logger.info(
            f"🏆 BM25 source rankings: {[(name, f'{score:.3f}') for name, score in source_rankings[:5]]}"
        )

        # Convert rankings to source preferences dict
        source_preferences = {name: score for name, score in source_rankings}
    except Exception as e:
        logger.warning(f"BM25 ranking failed, using default preferences: {e}")
        source_preferences = {}

    # Get available sources and their BM25-based priorities
    available_sources = []
    for source_name, search_func in search_functions.items():
        if api_status.get(source_name, True):  # Default to True for unknown sources
            # Extract actual source name from function name (remove "search_" prefix if present)
            actual_source_name = (
                source_name.replace("search_", "")
                if source_name.startswith("search_")
                else source_name
            )
            preference_score = source_preferences.get(
                actual_source_name, 0.3
            )  # Default preference if BM25 failed
            available_sources.append(
                (actual_source_name, search_func, preference_score)
            )

    # Sort sources by preference score (highest first)
    available_sources.sort(key=lambda x: x[2], reverse=True)

    # Search implementation with optional parallel execution
    sources_used = []
    min_sources_to_try = min(
        3, len(available_sources)
    )  # Always try at least top 3 sources

    # Check if parallel search is enabled, otherwise fall back to sequential
    if config.enable_parallel_search and len(available_sources) > 1:
        # Parallel search implementation for improved performance
        max_concurrent = min(config.max_concurrent_sources, len(available_sources))
        logger.info(
            f"🚀 Using parallel search with max {max_concurrent} concurrent sources"
        )
    else:
        # Fall back to sequential search if parallel is disabled or only one source
        logger.info("🔄 Using sequential search (parallel disabled or single source)")
        max_concurrent = 1

    if max_concurrent > 1:
        # Parallel search implementation
        async def search_source_with_isolation(
            source_info: tuple, source_index: int
        ) -> tuple[str, list, bool]:
            """Search a single source with proper error isolation"""
            source_name, search_func, preference_score = source_info

            try:
                logger.info(
                    f"🔍 Searching {source_name} (preference: {preference_score:.3f}, parallel)"
                )

                # Calculate fair quota distribution for parallel execution
                if source_index < min_sources_to_try:
                    # For top sources, ensure reasonable allocation
                    base_quota = max(3, limit // min_sources_to_try)
                    preference_bonus = max(0, int(base_quota * preference_score * 0.3))
                    source_limit = min(limit, base_quota + preference_bonus)
                else:
                    # For additional sources, use preference-based allocation
                    source_limit = max(2, int(limit * preference_score * 0.4))

                # Execute search with proper function routing
                if source_name in ["pubmed", "pubmed_central"]:
                    if source_name == "pubmed":
                        results = await health_monitor.monitor_request(
                            source_name, search_pubmed, query, source_limit
                        )
                    elif source_name == "pubmed_central":
                        results = await health_monitor.monitor_request(
                            source_name, search_pubmed_central, query, source_limit
                        )
                    else:
                        results = await health_monitor.monitor_request(
                            source_name, search_func, query, source_limit
                        )
                elif source_name == "arxiv":
                    results = await health_monitor.monitor_request(
                        source_name, search_arxiv, query, source_limit
                    )
                elif callable(search_func):
                    results = await health_monitor.monitor_request(
                        source_name, search_func, query, source_limit
                    )
                else:
                    logger.warning(f"⚠️ Skipping {source_name}: not callable")
                    return source_name, [], False

                # Return results with source metadata
                if results:
                    logger.info(f"✅ {source_name}: {len(results)} results (parallel)")
                    return source_name, results, True
                else:
                    logger.info(f"⚪ {source_name}: No results (parallel)")
                    return source_name, [], True

            except Exception as e:
                logger.warning(f"❌ {source_name} failed: {e}")
                return source_name, [], False

        # Execute searches in parallel with concurrency control
        search_tasks = []
        for i, source_info in enumerate(available_sources[:max_concurrent]):
            task = search_source_with_isolation(source_info, i)
            search_tasks.append(task)

        logger.info(f"🚀 Starting parallel search across {len(search_tasks)} sources")

        # Gather all results concurrently
        parallel_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Process results and maintain source priority order
        successful_sources = 0
        for result in parallel_results:
            if isinstance(result, Exception):
                logger.warning(f"🔥 Parallel search exception: {result}")
                continue

            if isinstance(result, tuple) and len(result) == 3:
                source_name, results, success = result
            else:
                logger.warning(f"Invalid result format: {result}")
                continue
            if success:
                successful_sources += 1
                if results:
                    all_results.extend(results)
                    sources_used.append(source_name)

        logger.info(
            f"🎯 Parallel search complete: {successful_sources} sources, {len(all_results)} total results"
        )

    else:
        # Sequential search fallback implementation
        sources_attempted = 0
        remaining_limit = limit

        for source_name, search_func, preference_score in available_sources:
            # Stop if we've tried minimum sources and have enough results
            if sources_attempted >= min_sources_to_try and remaining_limit <= 0:
                break

            try:
                logger.info(
                    f"🔍 Searching {source_name} (preference: {preference_score:.3f}, sequential)"
                )

                # Calculate quota for sequential execution
                if sources_attempted < min_sources_to_try:
                    sources_remaining = min_sources_to_try - sources_attempted
                    base_quota = max(2, remaining_limit // sources_remaining)
                    preference_bonus = max(0, int(base_quota * preference_score * 0.5))
                    source_limit = min(remaining_limit, base_quota + preference_bonus)
                else:
                    source_limit = min(
                        remaining_limit,
                        max(1, int(remaining_limit * preference_score * 2)),
                    )

                # Execute search with proper function routing
                if source_name in ["pubmed", "pubmed_central"]:
                    if source_name == "pubmed":
                        results = await health_monitor.monitor_request(
                            source_name, search_pubmed, query, source_limit
                        )
                    elif source_name == "pubmed_central":
                        results = await health_monitor.monitor_request(
                            source_name, search_pubmed_central, query, source_limit
                        )
                    else:
                        results = await health_monitor.monitor_request(
                            source_name, search_func, query, source_limit
                        )
                elif source_name == "arxiv":
                    results = await health_monitor.monitor_request(
                        source_name, search_arxiv, query, source_limit
                    )
                elif callable(search_func):
                    results = await health_monitor.monitor_request(
                        source_name, search_func, query, source_limit
                    )
                else:
                    logger.warning(f"⚠️ Skipping {source_name}: not callable")
                    continue

                sources_attempted += 1

                if results:
                    all_results.extend(results)
                    sources_used.append(source_name)
                    remaining_limit = max(0, limit - len(all_results))
                    logger.info(
                        f"✅ {source_name}: {len(results)} results (total: {len(all_results)})"
                    )
                else:
                    logger.info(f"⚪ {source_name}: No results")

            except Exception as e:
                logger.warning(f"❌ {source_name} failed: {e}")
                continue

    # Fallback: If we still haven't reached the limit, try additional sources with default category
    if remaining_limit > 0:
        logger.info(f"Using fallback search for remaining {remaining_limit} results")
        fallback_sources = [
            (name, func, 0.3)
            for name, func, _ in available_sources
            if name not in sources_used and api_status.get(name, True)
        ]

        for source_name, search_func, _ in fallback_sources:
            if remaining_limit <= 0:
                break

            try:
                logger.info(f"Fallback search: {source_name}")

                # Try with smaller limits for fallback
                fallback_limit = min(remaining_limit, 2)

                if source_name == "pubmed":
                    results = await health_monitor.monitor_request(
                        source_name, search_pubmed, query, fallback_limit
                    )
                elif source_name == "arxiv":
                    results = await health_monitor.monitor_request(
                        source_name, search_arxiv, query, fallback_limit
                    )
                elif callable(search_func):
                    results = await health_monitor.monitor_request(
                        source_name, search_func, query, fallback_limit
                    )
                else:
                    continue

                if results:
                    all_results.extend(results)
                    sources_used.append(source_name)
                    remaining_limit = max(0, limit - len(all_results))
                    logger.info(f"✅ Fallback {source_name}: {len(results)} results")

            except Exception as e:
                logger.warning(f"❌ Fallback {source_name} failed: {e}")
                continue

    # Add full text if requested
    if include_full_text and all_results:
        logger.info(f"Extracting full text for top {min(3, len(all_results))} results")
        for result in all_results[:3]:  # Only top 3 to avoid overload
            pdf_url = result.get("pdf_url") or result.get("open_access_pdf")
            if pdf_url:
                try:
                    text_result = await extract_pdf_text(pdf_url)
                    if text_result.get("success"):
                        result["full_text"] = text_result["text"]
                        result["extraction_method"] = text_result["extraction_method"]
                except Exception as e:
                    logger.warning(f"PDF extraction failed for {pdf_url}: {e}")

    # Sort by citation count if available, then by relevance (handle mixed data types)
    def safe_numeric_key(x: dict[str, Any]) -> tuple[float, float]:
        """Safely extract numeric values for sorting, handling string/None values."""
        citation_count = x.get("citation_count", 0)
        relevance_score = x.get("relevance_score", 0)

        # Convert citation_count to float safely
        try:
            citation_float = (
                float(citation_count) if citation_count is not None else 0.0
            )
        except (ValueError, TypeError):
            citation_float = 0.0

        # Convert relevance_score to float safely
        try:
            relevance_float = (
                float(relevance_score) if relevance_score is not None else 0.0
            )
        except (ValueError, TypeError):
            relevance_float = 0.0

        return (citation_float, relevance_float)

    all_results.sort(key=safe_numeric_key, reverse=True)

    # Prepare result summary with enhanced metadata
    result_summary = {
        "results": all_results[:limit],
        "total_found": len(all_results),
        "api_status": api_status.copy(),
        "sources_used": sources_used,  # Use the tracked sources_used list
        "query": query,
        "search_strategy": "intelligent_routing",
        "bm25_rankings": (
            {
                "top_sources": (
                    source_rankings[:5] if "source_rankings" in locals() else []
                ),
                "ranking_method": "BM25",
                "total_sources_ranked": (
                    len(source_rankings) if "source_rankings" in locals() else 0
                ),
            }
            if "source_rankings" in locals()
            else None
        ),
    }

    logger.info(
        f"Search completed: {len(all_results)} total results from {len(sources_used)} sources"
    )

    # Cache the result for future requests (smart TTL based on query complexity)
    cache_ttl = 3600  # 1 hour default

    # Adjust TTL based on result quality and complexity
    if len(sources_used) >= 3 and len(all_results) >= limit:
        # High-quality multi-source results get longer cache time
        cache_ttl = 7200  # 2 hours
    elif len(all_results) == 0:
        # Empty results get shorter cache time (might be temporary API issues)
        cache_ttl = 600  # 10 minutes

    # Store in cache for future requests
    cache_success = query_cache.cache_result(
        query, limit, result_summary, cache_params, cache_ttl
    )
    if cache_success:
        logger.info(f"💾 Cached search result (TTL: {cache_ttl}s)")

    return result_summary
