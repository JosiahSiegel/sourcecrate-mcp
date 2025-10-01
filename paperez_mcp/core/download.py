"""
Core download functionality for PaperezMCP.

This module contains protocol-agnostic download functions that can be called
from any interface (MCP, HTTP, CLI, etc.).

Note: Currently these are wrappers that delegate to the implementations in server.py.
Future refactoring will move the full implementation here.
"""

import logging
from typing import Any, cast

logger = logging.getLogger(__name__)


async def download_papers_core(
    query: str,
    limit: int = 5,
    output_dir: str = ".paperez",
    force_category: str | None = None,
    convert_to_markdown: bool = True,
    debug: bool = False,
) -> dict[str, Any]:
    """
    Download academic papers and convert to markdown/PDF.

    This is the core download function that can be called from any interface.

    Args:
        query: Search query (keywords, DOI, author, title)
        limit: Maximum number of papers to download
        output_dir: Directory to save downloaded papers
        force_category: Force a specific search category
        convert_to_markdown: Convert PDFs to markdown (True) or keep as PDF (False)
        debug: Include diagnostic information

    Returns:
        Dict containing:
        - results: List of paper objects with local file paths
        - total_found: Number of papers found
        - downloaded_count: Number successfully downloaded
        - output_directory: Where files were saved
    """
    # Import here to avoid circular dependencies
    from paperez_mcp import server

    # Call the existing download_papers implementation
    result_list = await server.download_papers(  # type: ignore[operator]  # FastMCP decorated function is callable
        query, limit, output_dir, force_category, convert_to_markdown, debug
    )

    if result_list and len(result_list) > 0:
        return cast(dict[str, Any], result_list[0])

    # Fallback for empty results
    return {
        "results": [],
        "total_found": 0,
        "downloaded_count": 0,
        "output_directory": output_dir,
    }
