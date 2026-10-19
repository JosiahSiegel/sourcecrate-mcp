"""
Core search functionality for SourceCrateMCP.

This module contains protocol-agnostic search functions that can be called
from any interface (MCP, HTTP, CLI, etc.).

These adapters normalize the shared research service responses.
"""

import logging
from typing import Any, cast

logger = logging.getLogger(__name__)


async def browse_papers_core(
    query: str,
    limit: int = 10,
    force_category: str | None = None,
    debug: bool = False,
) -> dict[str, Any]:
    """
    Search academic papers and return metadata/abstracts.

    This is the core search function that can be called from any interface.

    Args:
        query: Search query (keywords, DOI, author, title)
        limit: Maximum number of results to return
        force_category: Force a specific search category
        debug: Include diagnostic information

    Returns:
        Dict containing:
        - results: List of paper metadata
        - total_found: Number of papers found
        - api_status: Status of academic databases
        - sources_used: List of sources that returned results
        - query: Original search query
    """
    from source_crate.core import research

    result_list = await research.browse_papers(query, limit, force_category, debug)

    if result_list and len(result_list) > 0:
        return cast(dict[str, Any], result_list[0])

    # Fallback for empty results
    return {
        "results": [],
        "total_found": 0,
        "api_status": {},
        "sources_used": [],
        "query": query,
    }


async def browse_papers_streaming_core(
    query: str,
    limit: int = 10,
    force_category: str | None = None,
    debug: bool = False,
) -> dict[str, Any]:
    """
    Search academic papers with real-time streaming as sources complete.

    This is the streaming version of browse_papers_core that delivers results
    as they become available from each source.

    Args:
        query: Search query (keywords, DOI, author, title)
        limit: Maximum number of results to return
        force_category: Force a specific search category
        debug: Include diagnostic information including streaming metrics

    Returns:
        Dict containing:
        - streaming_results: List of paper metadata
        - streaming_summary: Performance metrics and source completion status
        - early_results: Results delivered before all sources completed
        - final_results: Complete deduplicated results
        - streaming_stats: Timing and performance statistics
    """
    from source_crate.core import research

    result_list = await research.browse_papers_streaming(
        query, limit, force_category, debug
    )

    if result_list and len(result_list) > 0:
        return cast(dict[str, Any], result_list[0])

    # Fallback for empty results
    return {
        "streaming_results": [],
        "streaming_summary": {},
        "query": query,
    }
