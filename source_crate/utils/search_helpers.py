"""
Shared utilities for search operations.
Eliminates code duplication between optimize_search_performance() and smart_downloadable_search().
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def filter_available_sources(
    sources: dict[str, Any] | list[tuple[str, Any]],
    api_status: dict[str, bool],
) -> list[tuple[str, Any]]:
    """
    Filter sources to only include those that are available (enabled in API status).

    Args:
        sources: Either dict of {name: func} or list of [(name, func/desc), ...]
        api_status: Dict mapping source names to availability status

    Returns:
        List of (source_name, source_data) tuples for available sources only

    Example:
        >>> funcs = {"crossref": func1, "pubmed": func2}
        >>> status = {"crossref": True, "pubmed": False}
        >>> available = filter_available_sources(funcs, status)
        >>> # Returns [("crossref", func1)] - pubmed filtered out
    """
    # Convert dict to list of tuples if needed
    if isinstance(sources, dict):
        source_list = list(sources.items())
    else:
        source_list = list(sources)

    # Filter to only available sources
    available = []
    unavailable_count = 0

    for source_name, source_data in source_list:
        if api_status.get(source_name, True):  # Default to True if not in status
            available.append((source_name, source_data))
        else:
            unavailable_count += 1

    if unavailable_count > 0:
        logger.debug(
            f"⏭️  Skipped {unavailable_count} unavailable sources "
            f"({len(available)} sources available)"
        )

    return available


def apply_source_fallback(
    sources_to_search: list[tuple[str, Any]],
    all_available_sources: list[tuple[str, Any]],
    fallback_count: int = 3,
    reason: str = "all sources filtered out",
) -> list[tuple[str, Any]]:
    """
    Apply fallback mechanism when all sources have been filtered out.

    If sources_to_search is empty but all_available_sources is not, this returns
    the top N sources from all_available_sources as a fallback to prevent 0 results
    when overly aggressive filtering occurs.

    Args:
        sources_to_search: List of sources that passed filtering
        all_available_sources: List of all available sources (before filtering)
        fallback_count: Number of top sources to use as fallback (default: 3)
        reason: Reason for fallback (for logging)

    Returns:
        sources_to_search if non-empty, or top N all_available_sources as fallback

    Example:
        >>> sources_after_bm25 = []  # All filtered out
        >>> all_sources = [("crossref", ...), ("openalex", ...), ("pubmed", ...)]
        >>> fallback = apply_source_fallback(sources_after_bm25, all_sources, 3)
        >>> # Returns first 3 from all_sources as fallback
    """
    if len(sources_to_search) == 0 and len(all_available_sources) > 0:
        # All sources were filtered out - use fallback
        min_sources = min(fallback_count, len(all_available_sources))
        fallback_sources = all_available_sources[:min_sources]

        logger.warning(
            f"🚨 All sources filtered out ({reason})! "
            f"Using fallback: searching top {min_sources} sources: "
            f"{[s[0] for s in fallback_sources]}"
        )

        return fallback_sources
    else:
        # Normal case - return filtered sources
        return sources_to_search


def check_empty_search_functions(
    search_functions: dict[str, Any],
    operation_name: str = "search",
) -> bool:
    """
    Check if search_functions is empty and log error if so.

    Args:
        search_functions: Dictionary of search functions
        operation_name: Name of operation for logging (default: "search")

    Returns:
        True if empty (error condition), False if has functions

    Example:
        >>> if check_empty_search_functions(search_funcs, "browse"):
        ...     return empty_result  # Handle error case
    """
    if not search_functions:
        logger.error(
            f"❌ No search functions available for {operation_name}. "
            f"Configuration may have failed to load. Check initialization errors."
        )
        return True
    return False


def validate_api_status(
    api_status: dict[str, bool],
    search_functions: dict[str, Any],
) -> dict[str, bool]:
    """
    Validate and normalize API status dictionary.

    If api_status is empty or missing entries, attempts to load from config
    or falls back to enabling all available search functions.

    Args:
        api_status: Current API status dict (may be empty/incomplete)
        search_functions: Available search functions

    Returns:
        Validated/normalized API status dictionary

    Example:
        >>> api_status = {}  # Empty
        >>> validated = validate_api_status(api_status, search_funcs)
        >>> # Returns {source: True for source in search_funcs}
    """
    if not api_status:
        logger.warning("🚨 Empty api_status detected, attempting to load from config")
        try:
            from source_crate.config import get_current_config

            config = get_current_config()
            if config and config.sources:
                api_status = {
                    source: cfg.enabled for source, cfg in config.sources.items()
                }
                logger.info(f"✅ Loaded {len(api_status)} sources from config")
            else:
                # Fall back to enabling all available search functions
                api_status = {name: True for name in search_functions.keys()}
                logger.info(f"✅ Using {len(api_status)} available search functions")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            # Last resort - enable all available search functions
            api_status = {name: True for name in search_functions.keys()}
            logger.warning(
                f"⚠️  Enabling all {len(api_status)} available search functions as fallback"
            )

    return api_status
