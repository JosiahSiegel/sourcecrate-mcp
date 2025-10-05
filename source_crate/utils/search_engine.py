"""
Comprehensive search engine that queries multiple academic databases.
"""

import logging
from typing import Any

# Note: Source functions are now handled by the registry system
from ..config import get_search_service
from .adaptive_concurrency import adaptive_concurrency_manager
from .pdf_processor import extract_pdf_text
from .query_cache import query_cache
from .source_health_monitor import health_monitor

logger = logging.getLogger(__name__)


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
            # Assume all sources in search_functions are enabled
            if True:  # Only include enabled sources
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
        # Assume all sources in search_functions are enabled
        if True:  # Default to True for unknown sources
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
    enable_parallel = True  # Default to parallel search
    max_concurrent_sources = 5  # Default max concurrent
    if enable_parallel and len(available_sources) > 1:
        # Parallel search implementation for improved performance
        max_concurrent = min(max_concurrent_sources, len(available_sources))
        logger.info(
            f"🚀 Using parallel search with max {max_concurrent} concurrent sources"
        )
    else:
        # Fall back to sequential search if parallel is disabled or only one source
        logger.info("🔄 Using sequential search (parallel disabled or single source)")
        max_concurrent = 1

    if max_concurrent > 1:
        # Enhanced parallel search using adaptive concurrency
        logger.info(
            f"🚀 Using adaptive parallel search with up to {max_concurrent} concurrent sources"
        )

        # Prepare search tasks for adaptive concurrency manager
        search_tasks = []
        for i, source_info in enumerate(available_sources[:max_concurrent]):
            source_name, search_func, preference_score = source_info

            # Calculate fair quota distribution for parallel execution
            if i < min_sources_to_try:
                # For top sources, ensure reasonable allocation
                base_quota = max(3, limit // min_sources_to_try)
                preference_bonus = max(0, int(base_quota * preference_score * 0.3))
                source_limit = min(limit, base_quota + preference_bonus)
            else:
                # For additional sources, use preference-based allocation
                source_limit = max(2, int(limit * preference_score * 0.4))

            if callable(search_func):
                # Create enhanced search function that integrates with health monitoring
                async def enhanced_search_func(
                    q: str,
                    lim: int,
                    src_name: str = source_name,
                    func: Any = search_func,
                ) -> Any:
                    return await health_monitor.monitor_request(src_name, func, q, lim)

                search_tasks.append(
                    (source_name, enhanced_search_func, (query, source_limit))
                )
            else:
                logger.warning(
                    f"⚠️ Skipping {source_name}: search function not available"
                )

        # Progress callback for real-time updates
        async def search_progress_callback(
            source_name: str, result_count: int, success: bool
        ) -> None:
            status = "✅" if success else "❌"
            logger.info(
                f"{status} {source_name}: {result_count} results (adaptive parallel)"
            )

        # Execute with adaptive concurrency management
        if search_tasks:
            parallel_results = (
                await adaptive_concurrency_manager.execute_parallel_search(
                    search_tasks, progress_callback=search_progress_callback
                )
            )

            # Process results
            successful_sources = 0
            for source_name, results, success in parallel_results:
                if success:
                    successful_sources += 1
                    if results:
                        all_results.extend(results)
                        sources_used.append(source_name)

            # Log performance summary
            perf_summary = adaptive_concurrency_manager.get_performance_summary()
            logger.info(
                f"🎯 Adaptive parallel search complete: {successful_sources} sources successful, "
                f"{len(all_results)} total results, current concurrency: {perf_summary['current_concurrency']}"
            )

            # Log circuit breaker status if any sources are blocked
            if perf_summary["circuit_breaker_sources"]:
                logger.warning(
                    f"🚨 Circuit breakers active for: {', '.join(perf_summary['circuit_breaker_sources'])}"
                )
        else:
            logger.warning("No valid search tasks prepared for parallel execution")

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

                # Execute search using registry-based function routing
                if callable(search_func):
                    results = await health_monitor.monitor_request(
                        source_name, search_func, query, source_limit
                    )
                else:
                    logger.warning(
                        f"⚠️ Skipping {source_name}: search function not available"
                    )
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
            if name not in sources_used  # Source not used yet
        ]

        for source_name, search_func, _ in fallback_sources:
            if remaining_limit <= 0:
                break

            try:
                logger.info(f"Fallback search: {source_name}")

                # Try with smaller limits for fallback
                fallback_limit = min(remaining_limit, 2)

                if callable(search_func):
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
        "sources_enabled": True,  # All sources in search_functions are enabled
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
