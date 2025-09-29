#!/usr/bin/env python3
"""
PaperezMCP - Academic Paper Research Made Easy

A comprehensive academic research server with multi-source fallback,
robust caching, and graceful error handling. Built with modular architecture.
"""

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# Core imports only - heavy dependencies loaded lazily
from paperez_mcp.config import get_current_config, get_search_service
from paperez_mcp.utils.pdf_validator import pdf_validator
from paperez_mcp.utils.query_cache import query_cache
from paperez_mcp.utils.result_streaming import create_streaming_search


# Create api_status from current config
def get_api_status() -> dict[str, bool]:
    """Get API status from current configuration with forced initialization if needed.

    This function is called dynamically to ensure fresh configuration
    is loaded, avoiding issues with module-level initialization timing.
    """
    logger.debug("Getting API status...")

    try:
        config = get_current_config()
        status = {source: cfg.enabled for source, cfg in config.sources.items()}

        # If empty, something went wrong - try multiple reload strategies
        if not status:
            logger.warning("Empty API status detected, attempting config reload...")

            # Strategy 1: Force complete initialization
            try:
                from paperez_mcp.config import initialize_configuration_system
                search_service = initialize_configuration_system(enable_hot_reload=False)
                config = get_current_config()
                status = {source: cfg.enabled for source, cfg in config.sources.items()}
                if status:
                    logger.info(f"✓ API status loaded after full initialization: {len(status)} sources")
                    return status
            except Exception as init_error:
                logger.error(f"Full initialization failed: {init_error}")

            # Strategy 2: Force config reload
            from paperez_mcp.config.manager import get_config_manager
            try:
                manager = get_config_manager()
                manager._load_config()
                config = get_current_config()
                status = {source: cfg.enabled for source, cfg in config.sources.items()}
                if status:
                    logger.info(f"✓ API status loaded after config reload: {len(status)} sources")
                    return status
            except Exception as reload_error:
                logger.error(f"Config reload failed: {reload_error}")

            # Strategy 2: Try loading embedded configs
            if not status:
                try:
                    embedded_configs = manager._load_embedded_configs()
                    if embedded_configs and "sources" in embedded_configs:
                        status = {
                            name: src_cfg.get("enabled", True)
                            for name, src_cfg in embedded_configs["sources"].items()
                        }
                        logger.info(f"Loaded {len(status)} sources from embedded configs")
                except Exception as e:
                    logger.error(f"Failed to load embedded configs: {e}")

            # Strategy 3: Force initialization of config system
            if not status:
                try:
                    from paperez_mcp.config import initialize_configuration_system
                    initialize_configuration_system()
                    config = get_current_config()
                    status = {source: cfg.enabled for source, cfg in config.sources.items()}
                except Exception as e:
                    logger.error(f"Failed to initialize config system: {e}")

        # If still no status, return hardcoded defaults
        if not status:
            logger.warning("Using hardcoded API status defaults")
            status = {
                "arxiv": True,
                "pubmed": True,
                "pubmed_central": True,
                "crossref": True,
                "semantic_scholar": True,
                "google_scholar": True,
                "europe_pmc": True,
                "doaj": True,
                "core": True,
            }
            logger.info(f"✓ Loaded {len(status)} hardcoded sources")

        return status

    except Exception as e:
        logger.error(f"Failed to get API status: {e}")
        # Return hardcoded defaults as absolute fallback
        logger.warning("Critical error, using hardcoded defaults")
        return {
            "arxiv": True,
            "pubmed": True,
            "pubmed_central": True,
            "crossref": True,
            "semantic_scholar": True,
            "google_scholar": True,
            "europe_pmc": True,
            "doaj": True,
            "core": True,
        }


# Note: api_status is now retrieved dynamically in each function
# to avoid module-level initialization timing issues

# Lazy import flags
_PYMUPDF4LLM_AVAILABLE = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("PaperezMCP - Academic Paper Research Made Easy")


# Lazy import helpers - Google Scholar setup removed for ToS compliance


def _ensure_pymupdf4llm() -> Any:
    """Lazy import of pymupdf4llm"""
    global _PYMUPDF4LLM_AVAILABLE
    if _PYMUPDF4LLM_AVAILABLE is None:
        try:
            import pymupdf4llm

            _PYMUPDF4LLM_AVAILABLE = True
            return pymupdf4llm
        except ImportError:
            _PYMUPDF4LLM_AVAILABLE = False
            return None
    elif _PYMUPDF4LLM_AVAILABLE:
        import pymupdf4llm

        return pymupdf4llm
    return None


def _lazy_import_search_functions() -> dict[str, Any]:
    """Get search functions from unified config system with forced initialization"""
    logger.info("Loading search functions...")

    # Strategy 1: Try normal loading
    try:
        search_service = get_search_service()
        search_funcs = search_service.get_search_functions()

        # If functions available, return them
        if search_funcs:
            logger.info(f"✓ Loaded {len(search_funcs)} search functions from service")
            return search_funcs
    except Exception as e:
        logger.warning(f"Normal search service loading failed: {e}")

    # Strategy 2: Force complete reinitialization
    logger.info("Attempting forced configuration reinitialization...")
    try:
        from paperez_mcp.config import initialize_configuration_system
        search_service = initialize_configuration_system(enable_hot_reload=False)
        search_funcs = search_service.get_search_functions()
        if search_funcs:
            logger.info(f"✓ Loaded {len(search_funcs)} search functions after reinit")
            return search_funcs
    except Exception as reinit_error:
        logger.warning(f"Configuration reinitialization failed: {reinit_error}")

    # Strategy 3: Direct import of all available search functions
    logger.warning("Using direct import of search functions as fallback...")
    fallback_funcs = {}

    # Try to import all available clients
    client_imports = [
        ("arxiv", "paperez_mcp.api_clients.arxiv_client", "search_arxiv"),
        ("pubmed", "paperez_mcp.api_clients.pubmed_client", "search_pubmed"),
        ("pubmed_central", "paperez_mcp.api_clients.pubmed_client", "search_pubmed_central"),
        ("crossref", "paperez_mcp.api_clients.crossref_client", "search_crossref"),
        ("semantic_scholar", "paperez_mcp.api_clients.semantic_scholar_client", "search_semantic_scholar"),
        ("google_scholar", "paperez_mcp.api_clients.google_scholar_client", "search_google_scholar"),
        ("europe_pmc", "paperez_mcp.api_clients.europe_pmc_client", "search_europe_pmc"),
        ("doaj", "paperez_mcp.api_clients.doaj_client", "search_doaj"),
        ("core", "paperez_mcp.api_clients.core_client", "search_core"),
    ]

    for name, module_path, func_name in client_imports:
        try:
            import importlib
            module = importlib.import_module(module_path)
            search_func = getattr(module, func_name)
            fallback_funcs[name] = search_func
            logger.info(f"  ✓ Imported {name} search function")
        except Exception as e:
            logger.warning(f"  ✗ Failed to import {name}: {e}")

    if fallback_funcs:
        logger.info(f"✓ Successfully imported {len(fallback_funcs)} fallback search functions")
        return fallback_funcs

    # Strategy 4: Return absolute minimum functions
    logger.error("All import strategies failed, returning minimal function set")
    try:
        from paperez_mcp.api_clients.arxiv_client import search_arxiv
        from paperez_mcp.api_clients.pubmed_client import search_pubmed, search_pubmed_central

        return {
            "arxiv": search_arxiv,
            "pubmed": search_pubmed,
            "pubmed_central": search_pubmed_central,
        }
    except ImportError:
        logger.error("Critical: Could not import any search functions!")
        return {}


def _lazy_import_utils() -> dict[str, Any]:
    """Lazy import of utility functions"""
    from paperez_mcp.utils import (
        convert_pdf_to_markdown_content,
        download_pdf,
        extract_pdf_text,
        save_markdown_file,
        smart_downloadable_search,
    )
    from paperez_mcp.utils.pdf_processor import extract_pdf_text_from_local_file

    return {
        "extract_pdf_text": extract_pdf_text,
        "convert_pdf_to_markdown_content": convert_pdf_to_markdown_content,
        "download_pdf": download_pdf,
        "save_markdown_file": save_markdown_file,
        "extract_pdf_text_from_local_file": extract_pdf_text_from_local_file,
        "smart_downloadable_search": smart_downloadable_search,
    }


"""
OPTIMIZED MCP TOOLS - 6 Essential Functions

🚀 QUICK START GUIDE:

## Common Research Workflows:

### "Find and save 10 papers on topic X":
1. search_papers("topic X", limit=10)                    # Get metadata/abstracts
2. Review abstracts, identify papers with PDF URLs
3. For each interesting paper:
   convert_pdf_to_markdown(pdf_url, output_path="papers/paper_N.md")

### "Bulk download from existing PDF directory":
batch_convert_pdfs("pdf_directory/", "markdown_output/")

### "Quick download of top 3 papers":
search_papers("topic", limit=3, download_and_convert=True)

### "Research analysis workflow":
1. search_papers("broad topic", limit=20)               # Survey field
2. search_papers("specific aspect", include_full_text=True)  # Deep analysis
3. Download selected papers for detailed study

⚠️ AVOID COMMON MISTAKES:
- Don't expect full papers from search_papers() by default (metadata only!)
- Don't try to download >3 papers in one call (use multi-step approach)
- Don't confuse include_full_text (memory) vs download_and_convert (files)

## 5 Essential Tools:

1. browse_papers / download_papers - Comprehensive paper search and download
   - Multi-source search (CrossRef, Semantic Scholar, arXiv, PubMed, Google Scholar)
   - browse_papers: Get metadata/abstracts only for exploration
   - download_papers: Download full papers as markdown files (use for "get papers" requests)
   - Supports DOI queries, author searches, and keyword searches

2. convert_pdf_to_text - Local PDF text extraction
   - PyMuPDF-based extraction with unlimited character support
   - Handles complex academic document layouts
   - Zero context window usage

3. convert_pdf_to_markdown - Single PDF to markdown conversion
   - Zero-token conversion using pymupdf4llm
   - Preserves document structure and formatting
   - Zero context window usage

4. batch_convert_pdfs - Batch PDF to markdown conversion
   - Processes entire directories of PDFs
   - Zero-token conversion with progress tracking
   - Zero context window usage

5. get_status - System health and configuration status
   - API operational status for all databases
   - Cache statistics and configuration details

All file-saving tools default to current directory and accept custom output paths.
"""


@mcp.tool
async def browse_papers(
    query: str, limit: int = 10, force_category: str | None = None
) -> list[dict[str, Any]]:
    """
    🔍 BROWSE: Find and explore papers (metadata/abstracts only)

    This function is for DISCOVERING and BROWSING papers - metadata/abstracts only.
    Use this when you want to explore what's available before downloading.

    ⚠️ METADATA ONLY: Returns titles, authors, abstracts, DOIs - no full paper content

    FOR GETTING ACTUAL PAPERS:
    📄 Use download_papers("topic") instead!
    📄 These functions automatically download full papers as markdown files

    Search academic papers across multiple databases with intelligent fallback.
    Searches CrossRef, Semantic Scholar, arXiv, PubMed, and Google Scholar.
    Supports DOI queries, author queries, and keyword searches.

    Args:
        query: Search query (keywords, DOI with "doi:" prefix, title, or author)
        limit: Maximum number of results to return (default: 10, max recommended: 20)
        force_category: 🎯 FORCE SPECIFIC SOURCE TYPES (optional, overrides smart routing)
                       - "preprints" → arXiv, SocArXiv, OSF (latest research, not peer-reviewed)
                       - "journals" → CrossRef, PubMed, DOAJ (peer-reviewed publications)
                       - "open_access" → CORE, DOAJ, arXiv (free full-text available)
                       - "historical" → CORE, CrossRef (older documents, archives)
                       - "recent" → arXiv, Semantic Scholar (newest papers, last few years)

                       💡 USE WHEN: Smart routing fails to find papers or you need specific types
                       💡 EXAMPLE: force_category="historical" for "JFK assassination" queries

    Returns:
        List containing single dict with:
        - results: List of paper objects with metadata
        - total_found: Number of papers found
        - api_status: Status of all academic databases
        - sources_used: List of databases that returned results
        - query: Original search query

        Each paper object contains:
        - title: Paper title
        - authors: List of author names
        - doi: Digital Object Identifier (if available)
        - year: Publication year
        - journal: Journal/venue name
        - abstract: Paper abstract (if available)
        - citation_count: Number of citations
        - url: Direct link to paper
        - source: Database source (CrossRef, Semantic Scholar, etc.)
        - pdf_url: Direct PDF link (if available)
        - open_access_pdf: Open access PDF link (if available)

    Example Usage:
        browse_papers("machine learning", limit=10)  # Fast metadata overview
        browse_papers("Geoffrey Hinton", limit=5)    # Author search
        browse_papers("doi:10.1000/xyz123")          # DOI search
    """
    # Lazy import utilities
    utils = _lazy_import_utils()
    search_funcs = _lazy_import_search_functions()

    # Import performance optimization
    from paperez_mcp.utils.search_analytics import record_search_performance
    from paperez_mcp.utils.search_performance_optimizer import (
        optimize_search_performance,
    )

    start_time = time.time()
    session_id = f"browse_{int(time.time() * 1000)}"

    # Try optimized search first
    try:
        optimized_results, performance_metrics = await optimize_search_performance(
            search_funcs,
            query,
            limit,
            get_api_status(),
            user_preferences={
                "prefer_recent": True,
                "force_category": force_category
            },  # Prefer recent papers for browsing, respect force_category
        )

        if optimized_results:
            # Record performance analytics
            search_time = time.time() - start_time
            record_search_performance(
                session_id=session_id,
                query=query,
                total_time=search_time,
                sources_used=list(performance_metrics.source_response_times.keys()),
                results_found=len(optimized_results),
                cache_hit=performance_metrics.cache_hit_rate > 0,
                quality_score=performance_metrics.result_quality_score,
            )

            # Create search log for compatibility
            search_log = {
                "query": query,
                "sources_searched": list(
                    performance_metrics.source_response_times.keys()
                ),
                "total_found": len(optimized_results),
                "performance_optimized": True,
                "cache_hit_rate": performance_metrics.cache_hit_rate,
                "total_search_time": search_time,
            }

            papers = optimized_results
        else:
            # Fallback to traditional search
            papers, search_log = await utils["smart_downloadable_search"](
                query,
                limit,
                search_funcs,
                utils,
                get_api_status(),
                force_category,
                metadata_only=True,
            )
    except Exception as e:
        logger.warning(
            f"Performance optimization failed, using traditional search: {e}"
        )
        # Fallback to traditional search
        papers, search_log = await utils["smart_downloadable_search"](
            query,
            limit,
            search_funcs,
            utils,
            get_api_status(),
            force_category,
            metadata_only=True,
        )

    # Convert to browse format (metadata only, remove download info)
    browse_results = []
    fallback_used = False
    original_category = None

    for paper in papers:
        browse_paper = {
            k: v
            for k, v in paper.items()
            if k
            not in [
                "download_success",
                "local_markdown",
                "markdown_characters",
                "_fallback_used",
                "_original_category",
            ]
        }
        browse_results.append(browse_paper)

        # Check if any paper used fallback
        if paper.get("_fallback_used"):
            fallback_used = True
            original_category = paper.get("_original_category")

    result = {
        "results": browse_results,
        "total_found": len(browse_results),
        "api_status": get_api_status(),
        "sources_used": list(
            set(paper.get("source", "Unknown") for paper in browse_results)
        ),
        "query": query,
    }

    # Add fallback notification if used
    if fallback_used:
        result["fallback_notification"] = {
            "message": f"Results found using intelligent default search (original {'smart routing' if not original_category else original_category} found no results)",
            "original_category": original_category or "smart_routing",
            "fallback_category": "intelligent_default",
        }

    # Add intelligent error suggestions if no results found
    if len(browse_results) == 0:
        # Use enhanced search error handling
        from paperez_mcp.utils.user_friendly_errors import enhance_search_error

        if search_log.get("intelligent_error_suggestions"):
            # Use existing error info
            error_info = search_log["intelligent_error_suggestions"]

            # Type check error_info before using it
            if not isinstance(error_info, dict):
                error_info = {}

            # Safely extract suggestions and refinements with type checking
            suggestions = error_info.get("suggestions", [])
            if isinstance(suggestions, list):
                safe_suggestions = suggestions[:3]  # Top 3 suggestions
            else:
                safe_suggestions = []

            refinements = error_info.get("query_refinements", [])
            if isinstance(refinements, list):
                safe_refinements = refinements[:2]  # Top 2 refinements
            else:
                safe_refinements = []

            result["error_suggestions"] = {
                "message": error_info.get("message", "No results found"),
                "domain_detected": error_info.get("domain_detected"),
                "suggestions": safe_suggestions,
                "suggested_categories": error_info.get("suggested_categories", []),
                "help_text": error_info.get("help_text"),
                "query_refinements": safe_refinements,
            }
        else:
            # Generate enhanced search error suggestions
            enhanced_search_error = enhance_search_error(query, search_log)
            result["error_suggestions"] = enhanced_search_error
            result["enhanced_no_results"] = True

    return [result]


@mcp.tool
async def browse_papers_streaming(
    query: str, limit: int = 10, force_category: str | None = None
) -> list[dict[str, Any]]:
    """
    🌊 STREAMING BROWSE: Find papers with real-time results as sources complete

    Advanced streaming version of browse_papers that delivers results incrementally
    as each source completes, providing faster initial response times and real-time progress.

    ⚡ PERFORMANCE BENEFITS:
    - First results available in 2-5 seconds instead of waiting for all sources
    - Real-time progress updates showing which sources have completed
    - Adaptive concurrency optimizes response times based on source performance
    - Circuit breaker pattern prevents slow sources from blocking fast ones

    🔍 SEARCH FEATURES:
    - Same comprehensive database coverage as browse_papers
    - Intelligent source prioritization based on query analysis
    - Metadata-only results (titles, authors, abstracts, DOIs)
    - Advanced deduplication and relevance scoring

    Args:
        query: Search query (keywords, DOI with "doi:" prefix, title, or author)
        limit: Maximum number of results to return (default: 10, max recommended: 20)
        force_category: 🎯 FORCE SPECIFIC SOURCE TYPES (optional)
                       - "preprints" → arXiv, SocArXiv, OSF
                       - "journals" → CrossRef, PubMed, DOAJ
                       - "open_access" → CORE, DOAJ, arXiv
                       - "historical" → CORE, CrossRef
                       - "recent" → arXiv, Semantic Scholar

    Returns:
        List containing streaming search results with:
        - streaming_results: List of paper objects with metadata
        - streaming_summary: Performance metrics and source completion status
        - early_results: Results delivered before all sources completed
        - final_results: Complete deduplicated results
        - streaming_stats: Timing and performance statistics

    Example Usage:
        browse_papers_streaming("machine learning transformers", limit=10)
        browse_papers_streaming("quantum computing", force_category="recent")
    """
    # Lazy import utilities
    search_funcs = _lazy_import_search_functions()

    # Filter available search functions
    available_search_funcs = {
        name: func
        for name, func in search_funcs.items()
        if get_api_status().get(name, True) and callable(func)
    }

    if not available_search_funcs:
        return [
            {
                "streaming_results": [],
                "streaming_summary": {
                    "error": "No search sources available",
                    "available_sources": list(search_funcs.keys()),
                    "api_status": get_api_status(),
                },
                "streaming_stats": {},
            }
        ]

    # Apply category filtering if specified
    if force_category:
        category_sources = {
            "preprints": ["search_arxiv", "search_socarxiv", "search_osf_preprints"],
            "journals": [
                "search_crossref",
                "search_pubmed",
                "search_doaj",
                "search_europe_pmc",
            ],
            "open_access": [
                "search_core",
                "search_doaj",
                "search_arxiv",
                "search_pubmed_central",
                "search_socarxiv",
                "search_osf_preprints",
                "search_europe_pmc",
            ],
            "historical": ["search_core", "search_crossref", "search_internet_archive"],
            "recent": [
                "search_arxiv",
                "search_semantic_scholar",
                "search_pubmed_central",
                "search_clinicaltrials",
                "search_osf_preprints",
                "search_europe_pmc",
            ],
            "medical": [
                "search_pubmed",
                "search_pubmed_central",
                "search_clinicaltrials",
                "search_europe_pmc",
            ],
        }

        if force_category in category_sources:
            # Filter to category-specific sources
            category_funcs = {
                name: func
                for name, func in available_search_funcs.items()
                if name in category_sources[force_category]
            }
            if category_funcs:
                available_search_funcs = category_funcs
                logger.info(
                    f"🎯 Streaming search filtered to category '{force_category}': {list(category_funcs.keys())}"
                )
            else:
                logger.warning(
                    f"❌ No available sources for category '{force_category}', using all sources"
                )

    # Collect streaming results
    streaming_results = []
    early_results = []
    final_results = []
    streaming_updates = []
    error_messages = []

    source_completion_order = []
    timing_stats = {}

    try:
        # Create and execute streaming search
        async for update in create_streaming_search(
            available_search_funcs, query, limit, api_status.copy()
        ):
            streaming_updates.append(update)

            if update.type == "source_complete":
                source_completion_order.append(update.source)
                logger.info(f"🌊 Streaming update: {update.source} completed")

            elif update.type == "result":
                if update.results:
                    # Convert StreamedResult objects to dictionaries
                    update_results = []
                    for streamed_result in update.results:
                        result_dict = dict(streamed_result.data)
                        result_dict["_streaming_source"] = streamed_result.source
                        result_dict["_streaming_timestamp"] = streamed_result.timestamp
                        result_dict["_streaming_confidence"] = (
                            streamed_result.confidence_score
                        )
                        update_results.append(result_dict)

                    if (
                        update.progress
                        and update.progress.get("type") == "early_delivery"
                    ):
                        early_results.extend(update_results)
                        logger.info(f"🚀 Early delivery: {len(update_results)} results")
                    else:
                        streaming_results.extend(update_results)

            elif update.type == "error":
                error_messages.append(f"{update.source}: {update.error}")
                logger.warning(f"❌ Streaming error: {update.source}: {update.error}")

            elif update.type == "final":
                if update.results:
                    # Convert final StreamedResult objects to dictionaries
                    for streamed_result in update.results:
                        result_dict = dict(streamed_result.data)
                        result_dict["_streaming_source"] = streamed_result.source
                        result_dict["_streaming_timestamp"] = streamed_result.timestamp
                        result_dict["_streaming_confidence"] = (
                            streamed_result.confidence_score
                        )
                        result_dict["_streaming_final"] = True
                        final_results.append(result_dict)

                # Extract timing statistics
                if update.progress:
                    timing_stats = {
                        "total_time": update.progress.get("total_time", 0),
                        "first_result_time": update.progress.get("first_result_time"),
                        "completed_sources": update.progress.get(
                            "completed_sources", 0
                        ),
                        "error_sources": update.progress.get("error_sources", 0),
                        "total_sources": update.progress.get("total_sources", 0),
                        "streaming_stats": update.progress.get("streaming_stats", {}),
                    }

                logger.info(
                    f"🎯 Streaming complete: {len(final_results)} final results"
                )

    except Exception as e:
        error_messages.append(f"Streaming search failed: {str(e)}")
        logger.error(f"❌ Streaming search error: {e}")

        # Add enhanced error for streaming failures
        from paperez_mcp.utils.user_friendly_errors import enhance_error

        enhanced_streaming_error = enhance_error(
            str(e),
            operation="streaming search",
            context={
                "query": query,
                "available_sources": list(available_search_funcs.keys()),
                "timestamp": time.time(),
            },
            user_input=query,
        )

    # Prepare streaming summary
    streaming_summary = {
        "query": query,
        "limit": limit,
        "force_category": force_category,
        "sources_used": source_completion_order,
        "total_sources": len(available_search_funcs),
        "completed_sources": len(source_completion_order),
        "errors": error_messages if error_messages else None,
        "timing": timing_stats,
        "early_delivery_count": len(early_results),
        "final_result_count": len(final_results),
        "streaming_enabled": True,
    }

    # Add enhanced error information if streaming failed
    if "enhanced_streaming_error" in locals():
        streaming_summary["enhanced_error"] = enhanced_streaming_error["error"]

    # Use final results if available, otherwise use streaming results
    main_results = final_results if final_results else streaming_results

    # Clean up streaming metadata for final output (keep only essential info)
    cleaned_results = []
    for result in main_results[:limit]:
        cleaned_result = {
            k: v for k, v in result.items() if not k.startswith("_streaming_")
        }
        # Keep only essential streaming info
        if "_streaming_source" in result:
            cleaned_result["source"] = result["_streaming_source"]
        cleaned_results.append(cleaned_result)

    return [
        {
            "streaming_results": cleaned_results,
            "streaming_summary": streaming_summary,
            "early_results": (
                early_results[:5] if early_results else []
            ),  # First 5 early results for reference
            "streaming_stats": timing_stats,
        }
    ]


@mcp.tool
async def download_papers(
    query: str,
    limit: int = 5,
    output_dir: str = ".paperez",
    force_category: str | None = None,
    convert_to_markdown: bool = True,
) -> list[dict[str, Any]]:
    """
    📄 GET FULL PAPERS: Download academic papers as files (PDF or Markdown)

    This function is designed for when you want to actually GET papers, not just search for them.
    It downloads PDFs with readable filenames and optionally converts them to markdown files.

    Use this when users say "get papers", "download papers", or "save papers".

    Args:
        query: Search query (keywords, DOI, title, or author)
        limit: Maximum papers to download (default: 5, recommended: 5-10)
        output_dir: Directory to save files (default: ".paperez")
        force_category: 🎯 FORCE SPECIFIC SOURCE TYPES (optional, overrides smart routing)
                       - "preprints" → arXiv, SocArXiv, OSF (latest research, not peer-reviewed)
                       - "journals" → CrossRef, PubMed, DOAJ (peer-reviewed publications)
                       - "open_access" → CORE, DOAJ, arXiv (free full-text available)
                       - "historical" → CORE, CrossRef (older documents, archives)
                       - "recent" → arXiv, Semantic Scholar (newest papers, last few years)

                       💡 USE WHEN: Smart routing fails to find papers or you need specific types
                       💡 EXAMPLE: force_category="historical" for "JFK assassination" queries
        convert_to_markdown: If True (default), convert PDFs to markdown. If False, keep as PDFs only.

    Returns:
        List containing single dict with:
        - results: List of paper objects with local file paths
        - total_found: Number of papers found
        - downloaded_count: Number successfully downloaded
        - output_directory: Where files were saved

    Example Usage:
        download_papers("machine learning transformers", limit=3)  # Get as markdown
        download_papers("neural networks", limit=2, convert_to_markdown=False)  # Keep as PDFs
        download_papers("climate change", limit=5, output_dir="climate_papers")  # Custom directory
    """
    # Lazy import utilities
    utils = _lazy_import_utils()
    search_funcs = _lazy_import_search_functions()

    # Import the new paper processor service
    from paperez_mcp.services.paper_processor import process_papers

    # Use the extracted paper processing service
    result = await process_papers(
        query=query,
        limit=limit,
        output_dir=output_dir,
        search_funcs=search_funcs,
        utils=utils,
        api_status=get_api_status(),
        force_category=force_category,
        convert_to_markdown=convert_to_markdown,
    )

    return [result]


@mcp.tool
async def convert_pdf_to_text(
    file_path: str,
    output_path: str | None = None,
    title: str = "",
    authors: list[str] | None = None,
) -> dict[str, Any]:
    """
    Convert a local PDF file to plain text and save to a text file.

    Uses PyMuPDF for robust text extraction, creating a text file output
    to avoid consuming context window space. Similar to convert_pdf_to_markdown
    but outputs plain text instead.

    Args:
        file_path: Path to local PDF file
                   - Supports absolute and relative paths
                   - Must be a valid PDF file
        output_path: Output path for text file (default: current directory)
                     - If None, creates file with format: "{filename}_full.txt"
                     - Automatically creates directories if they don't exist
        title: Optional title for the document header (default: "")
               - Added as header at top of text file
        authors: Optional list of authors for the document header (default: None)
                 - Added as author list after title

    Returns:
        Dictionary containing:
        - success: Boolean indicating if extraction succeeded
        - text_path: Path to saved text file (if save succeeded)
        - text_length: Character count of extracted text
        - original_file: Original PDF file path
        - pages_extracted: Number of pages processed
        - file_size: Size of the PDF file in bytes
        - extraction_method: Method used ("PyMuPDF Local")

        On failure, includes:
        - success: false
        - error: Error message explaining the failure
        - text_path: None

    Features:
        - Zero context window consumption (content saved to files, not returned)
        - Preserves all text content with page separators
        - Fast processing using optimized PyMuPDF engine

    Example Usage:
        convert_pdf_to_text("research_paper.pdf")
        convert_pdf_to_text("paper.pdf", title="My Research Paper", authors=["John Doe"])
        convert_pdf_to_text("input.pdf", output_path="/documents/extracted/paper.txt")
    """
    try:
        # First extract the text using existing method
        utils = _lazy_import_utils()
        extraction_result = utils["extract_pdf_text_from_local_file"](file_path)

        if not extraction_result.get("success", False):
            return extraction_result  # type: ignore[no-any-return]

        # Generate output path if not provided
        if output_path is None:
            base_name = Path(file_path).stem
            output_path = f".paperez/{base_name}_full.txt"

        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Prepare text content with optional header
        content_parts = []

        if title:
            content_parts.append(f"# {title}\n")

        if authors:
            if isinstance(authors, list) and authors:
                authors_str = ", ".join(authors)
                content_parts.append(f"Authors: {authors_str}\n")

        if title or authors:
            content_parts.append(
                f"Pages: {extraction_result.get('num_pages', 'Unknown')}"
            )
            content_parts.append(f"File: {file_path}")
            content_parts.append(
                f"Extraction Method: {extraction_result.get('extraction_method', 'Unknown')}"
            )
            content_parts.append("\n" + "=" * 80 + "\n")

        # Add the extracted text
        content_parts.append(extraction_result.get("text", ""))

        # Combine all parts
        full_content = "\n".join(content_parts)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        # Return metadata only (no text content to save context)
        result = {
            "success": True,
            "text_path": output_path,
            "text_length": len(full_content),
            "original_file": file_path,
            "pages_extracted": extraction_result.get("num_pages", 0),
            "file_size": extraction_result.get("file_size", 0),
            "extraction_method": extraction_result.get(
                "extraction_method", "PyMuPDF Local"
            ),
        }

        return result  # type: ignore[no-any-return]

    except Exception as e:
        logger.error(f"Error in convert_pdf_to_text: {e}")

        # Import enhanced error handling
        from paperez_mcp.utils.user_friendly_errors import enhance_error

        enhanced_error = enhance_error(
            str(e),
            operation="PDF to text conversion",
            context={"file_path": file_path, "timestamp": time.time()},
            user_input=file_path,
        )

        # Return both original format and enhanced error info
        return {
            "success": False,
            "error": str(e),
            "text_path": None,
            "original_file": file_path,
            "enhanced_error": enhanced_error["error"],
        }


async def _convert_pdf_to_markdown_internal(
    file_path: str,
    title: str = "",
    authors: list[str] | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """
    Internal function to convert a local PDF file to formatted markdown.
    Duplicates PDF extraction logic to avoid MCP tool calling MCP tool.
    """
    utils = _lazy_import_utils()
    result = utils["convert_pdf_to_markdown_content"](file_path, title, authors)

    if result.get("success"):
        # Determine output path
        if output_path:
            markdown_path = output_path
        else:
            # Default to .paperez directory with same name as PDF
            filename = Path(file_path).stem + "_full.md"
            markdown_path = os.path.join(".paperez", filename)

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(markdown_path), exist_ok=True)

        save_result = utils["save_markdown_file"](result["markdown"], markdown_path)
        if save_result.get("success"):
            result["markdown_path"] = markdown_path

        # Store markdown length and remove content to avoid context window usage
        if "markdown" in result:
            result["markdown_length"] = len(result["markdown"])
            # Don't delete markdown here yet - batch_convert_pdfs needs it
            # Will be cleaned up by the calling function

    return result  # type: ignore[no-any-return]


@mcp.tool
async def convert_pdf_to_markdown(
    file_path: str,
    title: str = "",
    authors: list[str] | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """
    Convert a local PDF file to formatted markdown.

    Uses pymupdf4llm for zero-token conversion preserving document structure,
    headings, and formatting. Ideal for academic papers and research documents.

    Args:
        file_path: Path to the PDF file to convert
                   - Supports absolute and relative paths
                   - Must be a valid PDF file
        title: Optional title for the document header (default: "")
               - Added as H1 header at top of markdown
        authors: Optional list of authors for the document header (default: None)
                 - Added as author list after title
        output_path: Output path for markdown file (default: current directory)
                     - If None, creates file with format: "{filename}_full.md"
                     - Automatically creates directories if they don't exist

    Returns:
        Dictionary containing:
        - success: Boolean indicating if conversion succeeded
        - markdown_length: Character count of markdown content
        - original_file: Original PDF file path
        - pages_extracted: Number of pages processed
        - text_length: Character count of original text
        - markdown_path: Path to saved markdown file (if save succeeded)

        Note: The full markdown content is NOT returned to avoid consuming context window space.
        The markdown content is saved to the file specified in markdown_path.

        On failure, includes:
        - success: false
        - error: Error message explaining the failure

    Features:
        - Zero AI tokens used (direct PDF→markdown conversion)
        - Zero context window consumption (content saved to files, not returned)
        - Preserves document structure and formatting
        - Fast processing with pymupdf4llm

    Example Usage:
        convert_pdf_to_markdown("research_paper.pdf")
        convert_pdf_to_markdown("paper.pdf", title="My Research Paper", authors=["John Doe"])
        convert_pdf_to_markdown("input.pdf", output_path="/documents/converted/paper.md")
    """
    result = await _convert_pdf_to_markdown_internal(
        file_path, title, authors, output_path
    )

    # Remove markdown content to avoid context window usage
    if "markdown" in result:
        del result["markdown"]

    return result  # type: ignore[no-any-return]


async def download_and_convert_paper(
    pdf_url: str, convert_to_markdown: bool = True, output_dir: str | None = None
) -> dict[str, Any]:
    """
    Download a PDF and optionally convert it to markdown (default behavior).

    This function uses ZERO AI tokens for conversion - it calls an external
    converter script that uses pymupdf4llm to convert PDFs directly to markdown.

    Args:
        pdf_url: URL of the PDF to download
        convert_to_markdown: If True (default), convert to markdown. If False, keep as PDF only.
        output_dir: Optional output directory (defaults to current directory)

    Returns:
        Dictionary with download and conversion results
    """
    try:
        utils = _lazy_import_utils()

        if output_dir is None:
            output_dir = os.getcwd()

        # Download PDF
        download_result = await utils["download_pdf"](pdf_url, output_dir)

        if not download_result.get("success"):
            return download_result  # type: ignore[no-any-return]

        pdf_path = download_result["pdf_path"]

        # Convert to markdown if requested
        if convert_to_markdown:
            pymupdf4llm = _ensure_pymupdf4llm()
            if pymupdf4llm:
                # Use pymupdf4llm directly (zero tokens)
                try:
                    markdown_content = pymupdf4llm.to_markdown(pdf_path)

                    # Save markdown
                    markdown_path = pdf_path.replace(".pdf", ".md")
                    save_result = utils["save_markdown_file"](
                        markdown_content, markdown_path
                    )

                    if save_result.get("success"):
                        return {
                            "success": True,
                            "pdf_path": pdf_path,
                            "markdown_path": markdown_path,
                            "markdown_characters": len(markdown_content),
                            "method": "pymupdf4llm_direct",
                        }
                except Exception as e:
                    logger.warning(f"Direct conversion failed: {e}")

            # Fallback to internal converter
            try:
                result = await _convert_pdf_to_markdown_internal(pdf_path)
                if result.get("success"):
                    return {
                        "success": True,
                        "pdf_path": pdf_path,
                        "markdown_path": result.get("markdown_path"),
                        "markdown_characters": result.get("markdown_length", 0),
                        "method": "internal_converter",
                    }
            except Exception as e:
                logger.warning(f"Internal conversion failed: {e}")

        return {
            "success": True,
            "pdf_path": pdf_path,
            "message": "PDF downloaded successfully"
            + (" but markdown conversion failed" if convert_to_markdown else ""),
        }

    except Exception as e:
        from paperez_mcp.utils.user_friendly_errors import enhance_error

        enhanced_error = enhance_error(
            str(e),
            operation="PDF download and conversion",
            context={"pdf_url": pdf_url, "timestamp": time.time()},
            user_input=pdf_url,
        )

        return {
            "success": False,
            "error": f"Download/conversion failed: {str(e)}",
            "enhanced_error": enhanced_error["error"],
        }


@mcp.tool
async def batch_convert_pdfs(
    directory: str = "articles", output_dir: str | None = None
) -> dict[str, Any]:
    """
    Convert all PDFs in a directory to markdown format.

    Uses zero AI tokens - employs pymupdf4llm for direct PDF-to-markdown conversion
    without text passing through AI context. Preserves document structure and formatting.

    Args:
        directory: Directory containing PDFs (default: "articles")
                   - Supports absolute and relative paths
                   - Recursively searches for PDF files (*.pdf, case-insensitive)
        output_dir: Output directory for markdown files (default: current directory)
                    - Automatically creates directory if it doesn't exist
                    - Preserves original filenames with "_full.md" suffix

    Returns:
        Dictionary containing:
        - success: Boolean indicating overall batch operation success
        - directory: Input directory path that was processed
        - output_directory: Output directory where files were saved
        - total_files: Total number of PDF files found
        - successful_conversions: Number of PDFs successfully converted
        - failed_conversions: Number of PDFs that failed to convert
        - files: List of conversion results for each file

        Each file entry in 'files' list contains:
        - input_file: Original PDF file path
        - output_file: Generated markdown file path
        - success: Boolean indicating if this file conversion succeeded
        - characters: Character count of generated markdown (if successful)
        - error: Error message (if conversion failed)

    Features:
        - Zero AI tokens consumed during conversion
        - Zero context window consumption (content saved to files, not returned)
        - Fast processing using optimized pymupdf4llm engine
        - Memory efficient for large directories

    Example Usage:
        batch_convert_pdfs()  # Convert from default "articles" directory
        batch_convert_pdfs("research_papers/")  # Convert from specific directory
        batch_convert_pdfs("pdfs/", "output/")  # Custom input and output directories
    """
    try:
        utils = _lazy_import_utils()

        if not os.path.isdir(directory):
            from paperez_mcp.utils.user_friendly_errors import enhance_error

            enhanced_error = enhance_error(
                f"Directory not found: {directory}",
                operation="batch PDF conversion",
                context={"directory": directory, "timestamp": time.time()},
                user_input=directory,
            )

            return {
                "success": False,
                "error": f"Directory not found: {directory}",
                "enhanced_error": enhanced_error["error"],
            }

        # Find all PDF files
        pdf_files = list(Path(directory).glob("*.pdf"))
        if not pdf_files:
            from paperez_mcp.utils.user_friendly_errors import enhance_error

            enhanced_error = enhance_error(
                f"No PDF files found in directory: {directory}",
                operation="batch PDF conversion",
                context={"directory": directory, "timestamp": time.time()},
                user_input=directory,
            )

            return {
                "success": False,
                "error": f"No PDF files found in directory: {directory}",
                "enhanced_error": enhanced_error["error"],
            }

        if output_dir is None:
            output_dir = os.getcwd()

        os.makedirs(output_dir, exist_ok=True)

        import asyncio

        results = []
        successful = 0
        failed = 0

        async def process_single_pdf(
            pdf_file: Path, semaphore: asyncio.Semaphore
        ) -> dict[str, Any]:
            """Process a single PDF file and return result."""
            async with semaphore:  # Limit concurrent processing
                try:
                    result = await _convert_pdf_to_markdown_internal(str(pdf_file))

                    if result.get("success"):
                        # Move to output directory
                        filename = pdf_file.stem + "_full.md"
                        output_path = os.path.join(output_dir, filename)

                        save_result = utils["save_markdown_file"](
                            result["markdown"], output_path
                        )

                        # Clean up markdown content to avoid context window usage
                        if "markdown" in result:
                            del result["markdown"]

                        if save_result.get("success"):
                            return {
                                "input_file": str(pdf_file),
                                "output_file": output_path,
                                "success": True,
                                "characters": result.get("markdown_length", 0),
                            }
                        else:
                            return {
                                "input_file": str(pdf_file),
                                "success": False,
                                "error": save_result.get("error"),
                            }
                    else:
                        # Clean up markdown content even on failure
                        if "markdown" in result:
                            del result["markdown"]

                        return {
                            "input_file": str(pdf_file),
                            "success": False,
                            "error": result.get("error"),
                        }

                except Exception as e:
                    return {
                        "input_file": str(pdf_file),
                        "success": False,
                        "error": str(e),
                    }

        # Process PDFs in parallel for better performance
        if len(pdf_files) > 1:
            # Limit concurrent PDF processing to avoid overwhelming the system
            max_concurrent_pdfs = min(
                5, len(pdf_files)
            )  # Process max 5 PDFs concurrently
            semaphore = asyncio.Semaphore(max_concurrent_pdfs)

            # Create tasks for parallel processing
            pdf_tasks = [
                process_single_pdf(pdf_file, semaphore) for pdf_file in pdf_files
            ]

            # Execute all tasks concurrently
            pdf_results = await asyncio.gather(*pdf_tasks, return_exceptions=True)

            # Collect results
            for i, result in enumerate(pdf_results):
                if isinstance(result, Exception):
                    # Handle exception from gather
                    failed += 1
                    results.append(
                        {
                            "input_file": str(pdf_files[i]),
                            "success": False,
                            "error": str(result),
                        }
                    )
                elif isinstance(result, dict) and result.get("success"):
                    successful += 1
                    results.append(result)
                else:
                    failed += 1
                    if isinstance(result, dict):
                        results.append(result)
                    else:
                        results.append(
                            {
                                "input_file": str(pdf_files[i]),
                                "success": False,
                                "error": f"Unexpected result type: {type(result)}",
                            }
                        )
        else:
            # For single files, process directly
            semaphore = asyncio.Semaphore(1)
            for pdf_file in pdf_files:
                result = await process_single_pdf(pdf_file, semaphore)
                if result.get("success"):
                    successful += 1
                else:
                    failed += 1
                results.append(result)

        return {
            "success": True,
            "directory": directory,
            "output_directory": output_dir,
            "total_files": len(pdf_files),
            "successful_conversions": successful,
            "failed_conversions": failed,
            "files": results,
        }

    except Exception as e:
        return {"success": False, "error": f"Batch conversion failed: {str(e)}"}


async def _get_current_categories_and_sources() -> dict[str, Any]:
    """Get current categories and sources for dynamic help information."""
    try:
        search_service = get_search_service()
        category_resolver = search_service.category_resolver
        config = get_current_config()

        # Get available categories with descriptions
        available_categories = {}
        for cat_name in category_resolver.get_available_categories():
            cat_info = category_resolver.get_category_info(cat_name)
            available_categories[cat_name] = cat_info.get('description', 'Custom category')

        # Get available sources with descriptions
        available_sources = {}
        for source_name, source_config in config.sources.items():
            if source_config.enabled:
                description = getattr(source_config.config, 'description', f'{source_name} academic database')
                available_sources[source_name] = description

        return {
            "available_categories": available_categories,
            "available_sources": available_sources,
            "category_count": len(available_categories),
            "source_count": len(available_sources),
            "note": "This data is loaded dynamically from your current configuration"
        }

    except Exception as e:
        return {
            "available_categories": {"error": f"Could not load categories: {str(e)}"},
            "available_sources": {"error": f"Could not load sources: {str(e)}"},
            "category_count": 0,
            "source_count": 0,
            "note": "Error loading dynamic configuration data"
        }


async def _get_comprehensive_config_info() -> dict[str, Any]:
    """Get comprehensive configuration information including all categories."""
    try:
        config = get_current_config()
        search_service = get_search_service()
        resolver = search_service.category_resolver

        # Collect category information
        categories_info = {}
        for cat_name, cat_config in config.categories.items():
            try:
                # Resolve category sources
                if cat_config.type == "standard":
                    sources = cat_config.sources
                    resolved_sources = resolver.resolve_category(cat_name)
                else:
                    # Meta categories
                    sources = []
                    resolved_sources = resolver.resolve_category(cat_name)

                # Check which sources are available
                current_api_status = get_api_status()
                sources_available = [s for s in resolved_sources if current_api_status.get(s, False)]
                sources_unavailable = [s for s in resolved_sources if not current_api_status.get(s, False)]

                categories_info[cat_name] = {
                    "display_name": cat_config.display_name,
                    "description": cat_config.description,
                    "type": cat_config.type,
                    "sources": sources if cat_config.type == "standard" else [],
                    "includes": cat_config.includes if cat_config.type == "meta" else [],
                    "resolved_sources": resolved_sources,
                    "sources_available": sources_available,
                    "sources_unavailable": sources_unavailable,
                    "functional": len(sources_available) > 0,
                    "max_results_per_source": cat_config.max_results_per_source,
                    "parallel_search": cat_config.parallel_search,
                    "merge_strategy": getattr(cat_config, 'merge_strategy', None),
                    "weights": getattr(cat_config, 'weights', {}),
                }
            except Exception as e:
                # If there's an error processing a category, include error info
                categories_info[cat_name] = {
                    "error": f"Failed to process category: {str(e)}",
                    "type": cat_config.type,
                    "functional": False
                }

        # Count functional categories
        functional_categories = sum(1 for info in categories_info.values() if info.get("functional", False))
        total_categories = len(categories_info)

        # Get routing configuration
        routing_info = {
            "enabled": config.routing.enabled,
            "fallback_enabled": config.routing.fallback_enabled,
            "domain_keywords": dict(config.routing.domain_keywords),
            "domain_categories": dict(config.routing.domain_categories),
        } if config.routing else {"enabled": False}

        return {
            "configuration_loaded": True,
            "yaml_config": "Using YAML-based configuration",
            "version": config.version,
            "default_category": config.default_category,
            "categories": {
                "total_categories": total_categories,
                "functional_categories": functional_categories,
                "available_categories": list(categories_info.keys()),
                "category_details": categories_info
            },
            "sources": {
                "total_sources": len(config.sources),
                "enabled_sources": len([s for s, cfg in config.sources.items() if cfg.enabled]),
                "available_sources": len([s for s in get_api_status().keys() if get_api_status().get(s, False)]),
                "source_names": list(config.sources.keys())
            },
            "routing": routing_info,
            "performance": {
                "max_concurrent_searches": config.max_concurrent_searches,
                "global_cache_enabled": config.global_cache_enabled,
                "global_cache_expire": config.global_cache_expire,
                "default_output_dir": config.default_output_dir
            }
        }

    except Exception as e:
        return {
            "configuration_loaded": False,
            "error": f"Failed to load configuration: {str(e)}",
            "yaml_config": "Configuration loading failed"
        }


@mcp.tool
async def get_status() -> dict[str, Any]:
    """
    Get comprehensive system status including API health, source monitoring, and configuration details.

    Reports operational status of all academic databases, detailed health metrics, performance data,
    cache usage, and comprehensive configuration details with category verification for AI users.

    Args:
        None - This tool takes no parameters

    Returns:
        Dictionary containing:
        - api_status: Basic status of all academic database APIs
        - cache_stats: Cache usage and configuration information
        - config: Comprehensive configuration details including:
          * categories.total_categories: Total number of loaded categories
          * categories.functional_categories: Categories with available sources
          * categories.available_categories: List of all category names
          * categories.category_details: Detailed info for each category (type, sources, functionality)
          * sources: Summary of available sources and their status
        - health_report: Detailed health monitoring with performance metrics
        - recommendations: Specific recommendations for system improvements
        - monitoring_enabled: Whether health monitoring is active

    AI User Configuration Verification:
        Use config.categories.category_details to verify your custom categories:
        - Check if your custom category appears in available_categories
        - Verify 'functional': True for your category
        - Confirm correct source count in 'sources_available'
        - Review 'resolved_sources' matches your category definition

    Use Cases:
        - System health monitoring and troubleshooting
        - Performance optimization insights
        - Custom configuration verification (especially for AI users)
        - Debugging category and source resolution issues

    Example Usage:
        status = get_status()
        if status["config"]["categories"]["total_categories"] > 10:
            print("Custom categories detected")

        # Verify custom category
        my_category = status["config"]["categories"]["category_details"].get("my_ai_research")
        if my_category and my_category["functional"]:
            print("Custom category working correctly")
    """
    # Get basic status
    basic_status: dict[str, Any] = {
        "api_status": get_api_status(),
        "cache_stats": {
            "query_cache": {
                **query_cache.get_cache_stats(),
                **query_cache.get_cache_size_info(),
            },
            "pdf_validation": pdf_validator.get_validation_stats(),
        },
        "config": await _get_comprehensive_config_info(),
    }

    # Add comprehensive health monitoring
    try:
        from paperez_mcp.utils.search_analytics import get_performance_dashboard
        from paperez_mcp.utils.search_performance_optimizer import intelligent_cache
        from paperez_mcp.utils.source_health_monitor import health_monitor

        # Perform active health check
        health_check = await health_monitor.perform_health_check()

        # Save metrics to cache for persistence
        health_monitor.save_metrics_to_cache()

        # Get performance analytics
        performance_dashboard = get_performance_dashboard()

        # Get cache statistics
        cache_stats = intelligent_cache.get_stats()

        # Add health data and performance analytics to basic status
        basic_status.update(
            {
                "health_report": health_monitor.get_health_report(),
                "recommendations": health_monitor.get_source_recommendations(),
                "health_check_results": health_check["health_check_results"],
                "monitoring_enabled": health_monitor.monitoring_enabled,
                "timestamp": health_check["overall_report"]["timestamp"],
                "performance_analytics": performance_dashboard,
                "cache_performance": cache_stats,
                "optimization_enabled": True,
            }
        )

    except Exception as e:
        logger.warning(f"Health monitoring unavailable: {e}")
        basic_status.update(
            {
                "health_report": {"status": "monitoring_unavailable"},
                "recommendations": [],  # list[dict[str, Any]] - empty list is valid
                "monitoring_enabled": False,  # bool - matches successful case
                "health_check_results": {},
                "timestamp": "",
            }
        )

    return basic_status


@mcp.tool
async def get_help() -> dict[str, Any]:
    """
    Get comprehensive configuration guidance and help for PaperezMCP.

    Provides detailed instructions on how to create configuration files, including
    file paths, schemas, available options, and examples for customizing the system.

    Args:
        None - This tool takes no parameters

    Returns:
        Dictionary containing:
        - config_guide: Complete configuration setup guide
        - file_paths: Required file paths for configuration
        - schema_info: Configuration schema and structure
        - examples: Common configuration examples
        - troubleshooting: Common issues and solutions
    """

    from pathlib import Path

    # Get dynamic category and source information first
    dynamic_info = await _get_current_categories_and_sources()

    help_info = {
        "config_guide": {
            "overview": "PaperezMCP uses YAML configuration files to customize sources, categories, and behavior. Changes are detected dynamically - no restart required!",
            "setup_approaches": {
                "single_file": {
                    "description": "Traditional single config.yaml approach",
                    "path": ".paperez/config/config.yaml",
                    "use_case": "Complete custom configuration"
                },
                "multi_file": {
                    "description": "RECOMMENDED: Individual YAML files for different purposes",
                    "path": ".paperez/config/my-custom-category.yaml",
                    "use_case": "Adding custom categories without complex source definitions"
                }
            },
            "setup_steps": [
                "1. Create the configuration directory: mkdir -p .paperez/config/",
                "2. Choose approach: single config.yaml OR individual .yaml files",
                "3. Create your configuration file(s) using examples below",
                "4. Use get_status() immediately to verify - changes are detected instantly!",
                "5. Check 'categories.category_details' in get_status() output to confirm your categories are loaded"
            ],
            "important_notes": [
                "🔥 DYNAMIC LOADING: Changes take effect immediately - no restart needed!",
                "📁 MULTI-FILE SUPPORT: Create separate .yaml files for different categories",
                "🔄 SMART MERGING: All .yaml files in .paperez/config/ are automatically merged",
                "✅ INSTANT VERIFICATION: Use get_status() to see your changes immediately",
                "⚠️ SOURCE VALIDATION: Only reference sources that exist (see available_sources below)"
            ],
        },
        "file_paths": {
            "user_config_path": str(
                Path.home() / ".paperez" / "config" / "config.yaml"
            ),
            "project_config_path": str(
                Path.cwd() / ".paperez" / "config" / "config.yaml"
            ),
            "config_directory": ".paperez/config/",
            "create_commands": [
                "mkdir -p .paperez/config/",
                "touch .paperez/config/config.yaml",
            ],
        },
        "schema_info": {
            "required_fields": {
                "version": "Configuration version (string, e.g., '1.0')",
                "sources": "Dictionary of source configurations",
                "categories": "Dictionary of search categories",
            },
            "optional_fields": {
                "use_default_sources": "Boolean - whether to include built-in sources (default: true)",
                "default_category": "String - default search category (default: intelligent routing)",
                "max_concurrent_searches": "Integer - max parallel searches (default: 15)",
                "global_cache_enabled": "Boolean - enable caching (default: true)",
                "global_cache_expire": "Integer - cache expiration in seconds (default: 7200)",
                "default_output_dir": "String - default output directory (default: '.paperez')",
                "cleanup_temp_files": "Boolean - clean temporary files (default: true)",
            },
            "source_structure": {
                "name": "Unique identifier for the source",
                "type": "Source type: 'http_api' or 'builtin'",
                "enabled": "Boolean - whether source is active",
                "timeout": "Integer - request timeout in seconds",
                "max_retries": "Integer - max retry attempts",
                "cache_expire": "Integer - cache duration in seconds",
                "config": "Source-specific configuration dictionary",
            },
            "category_structure": {
                "name": "Unique identifier for the category",
                "display_name": "Human-readable name",
                "description": "Description of the category purpose",
                "type": "Category type (usually 'standard')",
                "sources": "List of source names to include",
                "max_results_per_source": "Integer - max results per source",
                "parallel_search": "Boolean - enable parallel searching",
            },
        },
        "examples": {
            "custom_category_only": {
                "description": "RECOMMENDED: Add custom category using existing sources (file: .paperez/config/my-research.yaml)",
                "content": """# Custom Research Category
# This creates a new category without defining sources
# Uses existing sources: arxiv, semantic_scholar, crossref

categories:
  my_ai_research:
    name: my_ai_research
    display_name: "My AI Research"
    description: "Custom category for my specific AI research needs"
    type: standard
    sources:
      - arxiv
      - semantic_scholar
      - crossref
    max_results_per_source: 8
    parallel_search: true""",
            },
            "multiple_custom_categories": {
                "description": "Add multiple categories in one file (file: .paperez/config/research-categories.yaml)",
                "content": """# Multiple Custom Categories
# Each category uses different combinations of existing sources

categories:
  quantum_computing:
    name: quantum_computing
    display_name: "Quantum Computing Research"
    description: "Focus on quantum computing and quantum information"
    type: standard
    sources:
      - arxiv
      - semantic_scholar
    max_results_per_source: 5
    parallel_search: true

  biomedical_ai:
    name: biomedical_ai
    display_name: "Biomedical AI"
    description: "AI applications in medicine and biology"
    type: standard
    sources:
      - pubmed
      - pubmed_central
      - semantic_scholar
    max_results_per_source: 10
    parallel_search: true""",
            },
            "minimal_config": {
                "description": "Complete custom configuration (file: .paperez/config/config.yaml)",
                "content": """version: "1.0"
use_default_sources: false
sources:
  crossref:
    name: crossref
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: Primary academic publisher database
      base_url: https://api.crossref.org
      search_path: /works
      query_param: query
      limit_param: rows
      response_format: json
      results_path: message.items
      field_mappings:
        title: title.0
        authors: author
        doi: DOI
        year: published-print.date-parts.0.0
categories:
  simple:
    name: simple
    display_name: Simple Search
    description: Basic CrossRef search
    type: standard
    sources:
      - crossref
    max_results_per_source: 10
    parallel_search: false""",
            },
            "custom_source_config": {
                "description": "Adding a custom HTTP API source",
                "content": """sources:
  my_custom_api:
    name: my_custom_api
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: My custom academic API
      base_url: https://api.example.com
      search_path: /search
      query_param: q
      limit_param: limit
      response_format: json
      results_path: results
      field_mappings:
        title: title
        authors: authors
        doi: doi
        year: publication_year
        abstract: abstract
        url: url
      rate_limit_delay: 0.5""",
            },
            "disable_defaults_config": {
                "description": "Disable all default sources and use only custom ones",
                "content": """version: "1.0"
use_default_sources: false
# Your custom sources and categories here""",
            },
            "enhance_defaults_config": {
                "description": "Keep defaults but add custom sources",
                "content": """version: "1.0"
use_default_sources: true
# Add your custom sources - they will be merged with defaults
sources:
  my_source:
    # custom source configuration
categories:
  my_category:
    # custom category configuration""",
            },
        },
        # Get dynamic category and source information from actual configuration
        "dynamic_info": dynamic_info,
        "troubleshooting": {
            "validation_errors": {
                "sources_must_be_dict": {
                    "error": "1 validation error for PaperezConfig: sources - Input should be a valid dictionary",
                    "cause": "Empty or missing sources section when using category-only config",
                    "solution": "Remove 'sources:' line completely OR use existing sources in categories",
                    "example": "Instead of defining new sources, reference existing ones like: sources: [arxiv, crossref]"
                },
                "category_not_appearing": {
                    "error": "Custom category doesn't show in get_status()",
                    "cause": "YAML syntax error or invalid source references",
                    "solution": "Check YAML indentation, ensure sources exist in available_sources list below"
                }
            },
            "config_not_loading": [
                "✅ FIRST: Run get_status() - config loads dynamically, check 'configuration_loaded' field",
                "📁 Check file path: .paperez/config/ directory with .yaml extension",
                "📝 Validate YAML syntax (use online YAML validator)",
                "🔍 Check 'categories.total_categories' in get_status() - should increase with your additions",
                "⚠️ Ensure source names match exactly those in 'available_sources' below"
            ],
            "sources_not_working": [
                "🔍 Run get_status() and check 'config.categories.category_details.YOUR_CATEGORY.functional'",
                "✅ Verify sources in your category exist in 'available_sources' list below",
                "📊 Check 'sources_available' vs 'sources_unavailable' in get_status() output",
                "⚡ API issues are temporary - categories remain functional when APIs recover"
            ],
            "yaml_syntax_errors": [
                "🔤 Use spaces for indentation, never tabs",
                "📝 Quote strings with special characters: display_name: \"My Research & Analysis\"",
                "📋 List format: sources: [arxiv, crossref] OR sources:\\n  - arxiv\\n  - crossref",
                "🔍 Check brackets, quotes, and colons are properly closed",
                "🧪 Test immediately with get_status() after each change"
            ],
            "verification_workflow": [
                "1. Create your .yaml file in .paperez/config/",
                "2. Immediately run get_status() - no restart needed!",
                "3. Check 'config.categories.total_categories' increased",
                "4. Find your category in 'config.categories.category_details'",
                "5. Verify 'functional: true' and correct source count",
                "6. Test with browse_papers(force_category='your_category_name')"
            ]
        },
        "quick_start": {
            "ai_user_workflow": [
                "🚀 FASTEST: Use 'custom_category_only' example above",
                "1. mkdir -p .paperez/config/",
                "2. Create .paperez/config/my-research.yaml (use example above)",
                "3. Immediately run get_status() to verify",
                "4. Your category appears instantly in 'categories.category_details'",
                "5. Test with browse_papers(force_category='my_ai_research')"
            ],
            "recommended_approach": "Start with 'custom_category_only' - uses existing sources, no complex setup required",
            "verification_command": "get_status()['config']['categories']['total_categories'] should increase after adding your config",
            "success_indicators": [
                "✅ 'configuration_loaded': True in get_status()",
                "✅ 'total_categories' increased by number of categories you added",
                "✅ Your category name appears in 'available_categories' list",
                "✅ 'functional': True in your category's details",
                "✅ 'sources_available' > 0 for your category"
            ]
        },
    }

    return help_info


def _configure_utf8_output() -> bool:
    """Configure UTF-8 output for cross-platform compatibility.

    Returns:
        bool: True if UTF-8 encoding is available, False if fallback needed
    """
    try:
        # For Python 3.7+, reconfigure stdout/stderr to UTF-8
        if hasattr(sys.stdout, "reconfigure") and callable(
            getattr(sys.stdout, "reconfigure", None)
        ):
            # Type: ignore because mypy doesn't recognize reconfigure on TextIO
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
            return True
        # For older Python versions, check if UTF-8 is supported
        elif hasattr(sys.stdout, "encoding"):
            # Test if we can encode emojis
            test_str = "🚀"
            encoding = getattr(sys.stdout, "encoding", "utf-8")
            if encoding:
                test_str.encode(encoding)
            else:
                test_str.encode("utf-8")
            return True
    except (UnicodeEncodeError, LookupError, AttributeError):
        pass
    return False


def _safe_print(message: str, ascii_fallback: str = "") -> None:
    """Print message with Unicode support and ASCII fallback.

    Args:
        message: Message with potential Unicode characters
        ascii_fallback: ASCII-only version (optional)
    """
    try:
        print(message)
    except UnicodeEncodeError:
        # Fall back to ASCII version if provided, otherwise strip non-ASCII
        if ascii_fallback:
            print(ascii_fallback)
        else:
            # Remove non-ASCII characters
            ascii_msg = message.encode("ascii", errors="ignore").decode("ascii")
            print(ascii_msg)


def main() -> None:
    """Main entry point for the server"""
    # Force configuration initialization at server startup
    logger.info("Initializing PaperezMCP configuration system...")
    try:
        from paperez_mcp.config import initialize_configuration_system
        search_service = initialize_configuration_system(enable_hot_reload=False)

        # Verify configuration loaded successfully
        config = get_current_config()
        api_status = get_api_status()

        if config and config.sources:
            logger.info(f"✓ Configuration loaded with {len(config.sources)} sources")
        else:
            logger.warning("⚠ Configuration loading incomplete, using defaults")

        if api_status:
            enabled_sources = [k for k, v in api_status.items() if v]
            logger.info(f"✓ API status initialized with {len(enabled_sources)} enabled sources")
        else:
            logger.warning("⚠ API status empty, will attempt lazy initialization")

    except Exception as e:
        logger.error(f"Configuration initialization failed: {e}")
        logger.info("Server will attempt lazy initialization on first request")

    # Configure UTF-8 encoding for cross-platform compatibility
    utf8_available = _configure_utf8_output()

    if utf8_available:
        # Use emoji version if UTF-8 is available
        _safe_print(
            "🚀 Starting PaperezMCP Server...", "[*] Starting PaperezMCP Server..."
        )
        _safe_print("📚 Primary tools:", "Primary tools:")
        _safe_print(
            "  📄 download_papers: Get/download full papers as files (most users want this)",
            "  [PDF] download_papers: Get/download full papers as files (most users want this)",
        )
        _safe_print(
            "  🔍 browse_papers: Quick metadata overview (titles/abstracts only)",
            "  [SEARCH] browse_papers: Quick metadata overview (titles/abstracts only)",
        )
        _safe_print(
            "  📝 convert_pdf_to_text: Convert PDF to plain text files",
            "  [TEXT] convert_pdf_to_text: Convert PDF to plain text files",
        )
        _safe_print(
            "  🔄 convert_pdf_to_markdown: Convert PDF to markdown format",
            "  [CONVERT] convert_pdf_to_markdown: Convert PDF to markdown format",
        )
        _safe_print(
            "  📁 batch_convert_pdfs: Convert multiple PDFs in a directory",
            "  [BATCH] batch_convert_pdfs: Convert multiple PDFs in a directory",
        )
        _safe_print(
            "  🔧 get_status: Check system health and API status",
            "  [STATUS] get_status: Check system health and API status",
        )
        _safe_print(
            "  ❓ get_help: Configuration guide and setup instructions",
            "  [HELP] get_help: Configuration guide and setup instructions",
        )
        print("")
        _safe_print(
            "🎯 QUICK START: Use download_papers('topic') to get/download full papers!",
            "[START] QUICK START: Use download_papers('topic') to get/download full papers!",
        )
        print(
            "   Only use browse_papers() if you just want to explore titles/abstracts."
        )
        print("   Use get_help() for configuration guidance and setup instructions.")
        print("")
        _safe_print(
            "🔗 PaperezMCP ready at: stdio", "[READY] PaperezMCP ready at: stdio"
        )
    else:
        # Use ASCII-only version
        print("[*] Starting PaperezMCP Server...")
        print("Primary tools:")
        print(
            "  [PDF] download_papers: Get/download full papers as files (most users want this)"
        )
        print(
            "  [SEARCH] browse_papers: Quick metadata overview (titles/abstracts only)"
        )
        print("  [TEXT] convert_pdf_to_text: Convert PDF to plain text files")
        print("  [CONVERT] convert_pdf_to_markdown: Convert PDF to markdown format")
        print("  [BATCH] batch_convert_pdfs: Convert multiple PDFs in a directory")
        print("  [STATUS] get_status: Check system health and API status")
        print("  [HELP] get_help: Configuration guide and setup instructions")
        print("")
        print(
            "[START] QUICK START: Use download_papers('topic') to get/download full papers!"
        )
        print(
            "   Only use browse_papers() if you just want to explore titles/abstracts."
        )
        print("   Use get_help() for configuration guidance and setup instructions.")
        print("")
        print("[READY] PaperezMCP ready at: stdio")

    mcp.run()


if __name__ == "__main__":
    main()
