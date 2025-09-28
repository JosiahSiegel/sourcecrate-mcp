"""
Comprehensive search engine that queries multiple academic databases.
"""

import logging
from typing import Any

from ..api_clients.arxiv_client import search_arxiv
from ..api_clients.pubmed_client import search_pubmed, search_pubmed_central
from ..config import api_status, get_search_service
from .pdf_processor import extract_pdf_text
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

    Args:
        query: Search query for publications
        limit: Maximum number of results to return (default: 5)
        include_full_text: Whether to attempt full text extraction (default: False)

    Returns:
        Dictionary with search results and metadata from multiple sources
    """
    all_results = []
    remaining_limit = limit

    # Get search functions from unified config system
    search_service = get_search_service()
    search_functions = search_service.get_search_functions()

    # Use intelligent query analysis for source prioritization
    try:
        from .query_intent import analyze_query_intent

        query_analysis = analyze_query_intent(query)
        source_preferences = query_analysis.source_preferences
        logger.info(
            f"Query intent: {query_analysis.intent.value}, temporal: {query_analysis.temporal_preference.value}"
        )
    except Exception as e:
        logger.warning(f"Query analysis failed, using default preferences: {e}")
        source_preferences = {}

    # Get available sources and their priorities
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
            )  # Default preference
            available_sources.append(
                (actual_source_name, search_func, preference_score)
            )

    # Sort sources by preference score (highest first)
    available_sources.sort(key=lambda x: x[2], reverse=True)

    # Search through sources in priority order until limit is reached
    sources_used = []
    for source_name, search_func, preference_score in available_sources:
        if remaining_limit <= 0:
            break

        try:
            logger.info(
                f"Searching {source_name} (preference: {preference_score:.3f}, remaining: {remaining_limit})"
            )

            # Determine appropriate limit for this source
            source_limit = min(
                remaining_limit, max(1, int(remaining_limit * preference_score * 2))
            )

            # Handle special cases for legacy function signatures
            if source_name in ["pubmed", "pubmed_central"]:
                # These functions might need different handling
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
                # Generic search function call
                results = await health_monitor.monitor_request(
                    source_name, search_func, query, source_limit
                )
            else:
                logger.warning(f"Skipping {source_name}: not callable")
                continue

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

    # Sort by citation count if available, then by relevance
    all_results.sort(
        key=lambda x: (x.get("citation_count", 0), x.get("relevance_score", 0)),
        reverse=True,
    )

    # Prepare result summary with enhanced metadata
    result_summary = {
        "results": all_results[:limit],
        "total_found": len(all_results),
        "api_status": api_status.copy(),
        "sources_used": sources_used,  # Use the tracked sources_used list
        "query": query,
        "search_strategy": "intelligent_routing",
        "query_analysis": (
            {
                "intent": getattr(query_analysis, "intent", "unknown"),
                "temporal_preference": getattr(
                    query_analysis, "temporal_preference", "neutral"
                ),
                "confidence": getattr(query_analysis, "confidence", 0.0),
            }
            if "query_analysis" in locals()
            else None
        ),
    }

    logger.info(
        f"Search completed: {len(all_results)} total results from {len(sources_used)} sources"
    )
    return result_summary
