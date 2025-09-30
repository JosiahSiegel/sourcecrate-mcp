"""
Shared category filtering utilities for search operations.
Eliminates code duplication between optimize_search_performance() and smart_downloadable_search().
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def resolve_category_sources(force_category: str | None) -> list[str] | None:
    """
    Resolve category sources from YAML configuration.

    This function provides centralized category resolution logic used by both
    optimize_search_performance() and smart_downloadable_search() to ensure
    consistent force_category behavior across browse_papers and download_papers.

    Args:
        force_category: Category name to resolve (e.g., "philosophy", "preprints", "journals")
                       If None, returns None (no category filtering)

    Returns:
        List of source names in the category, or None if:
        - force_category is None (no filtering requested)
        - Category not found in configuration
        - Category has no sources defined
        - Error occurred during resolution

    Example:
        >>> category_sources = resolve_category_sources("philosophy")
        >>> if category_sources:
        ...     filtered = {k: v for k, v in funcs.items() if k in category_sources}
    """
    if not force_category:
        return None

    logger.info(f"🎯 Resolving category sources for: {force_category}")

    try:
        from paperez_mcp.config import get_search_service

        search_service = get_search_service()
        category_sources = search_service.resolve_category_sources(force_category)

        if category_sources:
            logger.info(
                f"📋 Category '{force_category}' resolved to {len(category_sources)} sources: {category_sources}"
            )
            return category_sources
        else:
            logger.warning(
                f"⚠️  Category '{force_category}' has no sources, will use all available sources"
            )
            return None

    except Exception as e:
        logger.warning(
            f"❌ Could not resolve category '{force_category}': {e}, will use all available sources"
        )
        return None


def filter_search_functions_by_category(
    search_functions: dict[str, Any],
    force_category: str | None,
) -> dict[str, Any]:
    """
    Filter search functions dictionary by category.

    Used by optimize_search_performance() to filter search functions based on
    force_category parameter.

    Args:
        search_functions: Dictionary mapping source names to search functions
        force_category: Category name to filter by (e.g., "philosophy", "preprints")

    Returns:
        Filtered dictionary containing only sources in the specified category,
        or original dictionary if force_category is None,
        or EMPTY dictionary if category has no sources (prevents silent fallback to all sources).

    Example:
        >>> filtered = filter_search_functions_by_category(
        ...     search_funcs, force_category="philosophy"
        ... )
        >>> # Only philosophy sources remain in filtered dict
    """
    # If no category specified, return all functions
    if not force_category:
        return dict(search_functions)

    category_sources = resolve_category_sources(force_category)

    if category_sources:
        # Filter to only include sources in the category
        filtered_functions = {
            name: func
            for name, func in search_functions.items()
            if name in category_sources
        }
        logger.info(
            f"📋 Filtered to {len(filtered_functions)} category sources: {list(filtered_functions.keys())}"
        )
        return filtered_functions
    else:
        # Category has no sources - return EMPTY dict (not all sources!)
        # This prevents silent fallback and will trigger error handling with helpful message
        logger.error(
            f"❌ Category '{force_category}' has no sources configured. "
            f"Cannot search with empty category. Please add sources to the category configuration."
        )
        return {}
