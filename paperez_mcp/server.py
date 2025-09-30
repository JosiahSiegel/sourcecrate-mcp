#!/usr/bin/env python3
"""
PaperezMCP - Academic Paper Research Made Easy

A comprehensive academic research server with multi-source fallback,
robust caching, and graceful error handling. Built with modular architecture.
"""

import asyncio
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


# Simple lazy initialization using singleton
def get_api_status() -> dict[str, bool]:
    """Get API status from configuration manager.

    Uses lazy initialization to ensure configuration is loaded only when needed.
    """
    from paperez_mcp.config.singleton import get_config_manager

    manager = get_config_manager()
    return manager.api_status


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
    """Get search functions using lazy initialization with forced init if needed."""
    from paperez_mcp.config.singleton import get_config_manager

    manager = get_config_manager()

    # Force initialization if not already done
    if not manager.search_functions:
        logger.info("Search functions not initialized, forcing initialization...")
        success = manager.initialize()
        if not success:
            logger.warning(
                "Initialization from singleton failed, attempting direct import..."
            )
            # Fallback: directly import search functions
            manager._import_search_functions_directly()

    search_funcs = manager.search_functions

    if not search_funcs:
        # Log error with helpful message
        logger.error(
            "No search functions available. Configuration may have failed to load. "
            "Check logs for initialization errors."
        )
        if manager.initialization_error:
            logger.error(f"Initialization error: {manager.initialization_error}")

    return search_funcs


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

    ⚠️ CRITICAL - QUERY OPTIMIZATION REQUIRED FOR AI CALLERS:
    Academic databases use simple keyword matching. Follow these rules for best results:

    1. **OPTIMAL LENGTH**: Use 2-4 core concepts (not 1, not 7+)
       - Too few terms (1) = too generic, poor relevance
       - Too many terms (7+) = all must match (AND logic), often 0 results
       - Sweet spot: 2-4 carefully chosen terms

    2. **SPACE = AND**: Most APIs treat spaces as AND (all terms must match)
       ❌ "egyptology ancient egypt pharaohs archaeology" = 5 ANDs = 0 results
       ✅ "ancient egypt archaeology" = 3 terms = good results

    3. **USE PHRASES**: Use quotes for multi-word concepts
       ❌ "machine learning neural networks" = must match all 4 words separately
       ✅ "machine learning" = phrase match, better precision

    4. **ACADEMIC TERMINOLOGY**: Use specific domain vocabulary
       ❌ "egypt history" (too generic)
       ✅ "ancient egypt archaeology" (specific field)

    GOOD query expansion examples:
      User: "egypt history" → You: "ancient egypt archaeology"
      User: "climate" → You: "climate change"
      User: "AI" → You: "machine learning artificial intelligence"

    BAD query expansion (TOO MANY TERMS - causes 0 results):
      ❌ "egyptology ancient egypt pharaohs archaeology historical civilization"
      ❌ "climate change climatology atmospheric environmental science"

    Keep queries concise: 2-4 core concepts maximum for best results.

    ---

    This function is for DISCOVERING and BROWSING papers - metadata/abstracts only.
    Use this when you want to explore what's available before downloading.

    ⚠️ METADATA ONLY: Returns titles, authors, abstracts, DOIs - no full paper content

    FOR GETTING ACTUAL PAPERS:
    📄 Use download_papers("topic") instead!
    📄 These functions automatically download full papers as markdown files

    Search academic papers across multiple databases with intelligent fallback.
    Searches CrossRef, Semantic Scholar, arXiv, PubMed, and Google Scholar.
    Supports DOI queries, author queries, and keyword searches.

    📋 SCOPE & LIMITATIONS:
    This tool searches for ACADEMIC RESEARCH PAPERS:
    ✅ Journal articles, preprints, conference papers, dissertations
    ✅ Papers ABOUT topics (e.g., "scholarship on Le Morte d'Arthur")
    ❌ Primary literary texts/books (e.g., "Le Morte d'Arthur full text")
    ❌ Non-scholarly content (news, blogs, general books)

    🔗 FOR PRIMARY LITERARY TEXTS:
    - Project Gutenberg: gutenberg.org (public domain books)
    - Internet Archive: archive.org (books, manuscripts, media)
    - HathiTrust: hathitrust.org (digitized books)
    - Google Books: books.google.com (book search)

    💡 EXAMPLE:
    ✅ "scholarship on Arthurian legend" → Use paperez (finds academic papers)
    ❌ "Le Morte d'Arthur full text" → Use Project Gutenberg (finds the book)

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

    🤖 AI USERS - WHEN TO CREATE CUSTOM CONFIGS:
    If you get 0 results with an optimized query (2-4 keywords, proper terms), this is a DOMAIN COVERAGE ISSUE, not a query problem.

    ⚠️ CRITICAL: No amount of query optimization will help if default sources don't cover your research domain. Immediately check if your topic needs custom configs below.

    🚨 PROACTIVE TRIGGERS - Create custom config when you see ANY of these:

    1. ❌ ZERO RESULTS: Optimized query (2-4 keywords) returns 0 papers
    2. ❌ LOW RESULTS: < 5 papers for well-known topics/figures (e.g., "Kant ethics" with 2 results)
    3. ❌ DISCIPLINE MISMATCH: Philosophy query returns only CS/AI papers (wrong field, not philosophy scholarship)
    4. ❌ SOURCE MISMATCH: All results from arXiv/Semantic Scholar for humanities topics

    💡 QUALITY > QUANTITY: 2 CS papers about formalizing Kant ≠ philosophy scholarship coverage
       Even if you get results, check if they're FROM the right discipline, not just ABOUT the topic.

    ✅ DON'T CREATE CUSTOM CONFIG IF:
    - Default sources return relevant, high-quality results that match your query intent
    - Results are FROM the right discipline (philosophy papers for philosophy queries, not CS papers)
    - You get enough papers that fully answer the query (even if < 5, quality matters more)
    - Sources are appropriate for the discipline (CrossRef/OpenAlex can include humanities journals)

    DEFAULT SOURCES COVER:
    ✅ STEM research (arXiv, Semantic Scholar, CrossRef, OpenAlex)
    ✅ Medical/biomedical (PubMed, PubMed Central, Europe PMC, ClinicalTrials.gov)
    ✅ General academic (CrossRef, DOAJ, CORE)
    ✅ Business/economics (RePEc)
    ✅ Legal (CourtListener)
    ✅ Open access repositories

    NEED CUSTOM CONFIGS FOR:
    ❌ Humanities research (history, literature, philosophy - needs JSTOR, Project MUSE, Historical Abstracts)
       NOTE: These sources provide academic PAPERS about texts, not the primary texts themselves
    ❌ Regional/national archives (non-US government databases, national libraries)
    ❌ Institutional repositories (university archives, research institution databases)
    ❌ Non-English specialized databases (country-specific sources)
    ❌ Specialized domains (specific industry databases, niche academic fields)
    ❌ Subscription-only databases requiring authentication

    💡 PROACTIVE ACTION: If you see ANY trigger condition above (0 results, < 5 results, discipline mismatch, source mismatch) AND defaults are not working well, immediately call get_help() to learn how to create custom source configurations. Don't wait for user permission - proactively create the config if you identify a missing source.

    EXAMPLES:
    - "French colonial archives" → French national archives (Archives Nationales)
    - "King Arthur history" → JSTOR, Project MUSE, Historical Abstracts
    - "Medieval literature" → Humanities databases (JSTOR, MUSE)

    Call get_help() immediately to see configuration examples.

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
                "force_category": force_category,
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

    # Validate PDF URLs to ensure papers are actually downloadable
    validation_start_time = time.time()
    validated_urls: dict[str, bool] = {}
    urls_to_validate: list[tuple[int, str]] = []

    # Collect all PDF URLs that need validation
    for idx, paper in enumerate(papers):
        pdf_url = paper.get("pdf_url") or paper.get("open_access_pdf")
        if pdf_url:
            urls_to_validate.append((idx, pdf_url))

    # Validate URLs concurrently (up to 20 at a time for performance)
    if urls_to_validate:
        logger.info(f"🔍 Validating {len(urls_to_validate)} PDF URLs...")
        validation_tasks = [
            pdf_validator.validate_pdf_url(url) for _, url in urls_to_validate
        ]

        # Run validations with timeout
        try:
            validation_results = await asyncio.gather(
                *validation_tasks, return_exceptions=True
            )

            # Process validation results
            for (_, url), validation_result in zip(
                urls_to_validate, validation_results, strict=True
            ):
                if isinstance(validation_result, Exception):
                    logger.debug(f"Validation error for {url}: {validation_result}")
                    validated_urls[url] = False
                elif (
                    isinstance(validation_result, tuple) and len(validation_result) == 2
                ):
                    is_valid, _ = validation_result
                    validated_urls[url] = is_valid
                else:
                    validated_urls[url] = False

        except Exception as e:
            logger.warning(f"PDF validation failed: {e}")
            # Fall back to not validating (assume all URLs are valid)
            for _, url in urls_to_validate:
                validated_urls[url] = True

    validation_time = time.time() - validation_start_time
    valid_count = sum(1 for valid in validated_urls.values() if valid)
    invalid_count = len(validated_urls) - valid_count

    logger.info(
        f"✅ PDF validation complete: {valid_count} valid, {invalid_count} invalid (took {validation_time:.2f}s)"
    )

    # Convert to browse format (metadata only, remove download info)
    # Filter to only include papers with validated PDF URLs
    browse_results = []
    non_downloadable_count = 0
    invalid_pdf_count = 0
    fallback_used = False
    original_category = None

    for paper in papers:
        # Check if paper has PDF URL
        pdf_url = paper.get("pdf_url") or paper.get("open_access_pdf")

        if pdf_url:
            # Check if URL was validated successfully
            is_valid = validated_urls.get(pdf_url, False)

            if is_valid:
                # Include only papers with validated PDFs
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
                # Add downloadability indicators
                browse_paper["is_downloadable"] = True
                browse_paper["pdf_validated"] = True
                browse_results.append(browse_paper)
            else:
                # Count papers with invalid PDF URLs
                invalid_pdf_count += 1
        else:
            # Count papers without PDF URLs that were filtered out
            non_downloadable_count += 1

        # Check if any paper used fallback
        if paper.get("_fallback_used"):
            fallback_used = True
            original_category = paper.get("_original_category")

    # Deduplicate browse_results by DOI or title to prevent duplicates
    # This handles cases where optimize_search_performance doesn't deduplicate
    seen_papers = set()
    deduplicated_results = []
    duplicate_count = 0

    for paper in browse_results:
        # Create identifier from DOI or title
        identifier = paper.get("doi") or paper.get("title", "").lower().strip()
        if identifier and identifier not in seen_papers:
            seen_papers.add(identifier)
            deduplicated_results.append(paper)
        else:
            duplicate_count += 1

    if duplicate_count > 0:
        logger.info(
            f"🔄 Removed {duplicate_count} duplicate papers (showing {len(deduplicated_results)} unique papers)"
        )

    browse_results = deduplicated_results

    # Log filtering statistics
    total_filtered = non_downloadable_count + invalid_pdf_count
    if total_filtered > 0:
        logger.info(
            f"📊 Filtered {total_filtered} papers: {non_downloadable_count} without PDF URLs, "
            f"{invalid_pdf_count} with invalid URLs (showing {len(browse_results)} validated papers)"
        )

    result = {
        "results": browse_results,
        "total_found": len(browse_results),
        "api_status": get_api_status(),
        "sources_used": list(
            set(paper.get("source", "Unknown") for paper in browse_results)
        ),
        "query": query,
    }

    # Add validation statistics (always include to show validation happened)
    if urls_to_validate:
        result["validation_stats"] = {
            "urls_checked": len(validated_urls),
            "valid_urls": valid_count,
            "invalid_urls": invalid_count,
            "validation_time_seconds": round(validation_time, 2),
            "note": "PDF URLs validated via HEAD requests to ensure downloadability",
        }

    # Add filtering statistics if papers were filtered
    if total_filtered > 0:
        result["filtering_stats"] = {
            "total_candidates": len(papers),
            "validated_downloadable": len(browse_results),
            "filtered_no_pdf": non_downloadable_count,
            "filtered_invalid_pdf": invalid_pdf_count,
            "note": "Only showing papers with validated, accessible PDF downloads",
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

    ⚠️ CRITICAL - QUERY OPTIMIZATION REQUIRED FOR AI CALLERS:
    Academic databases use simple keyword matching. Follow these rules for best results:

    1. **OPTIMAL LENGTH**: Use 2-4 core concepts (not 1, not 7+)
       - Too few terms (1) = too generic, poor relevance
       - Too many terms (7+) = all must match (AND logic), often 0 results
       - Sweet spot: 2-4 carefully chosen terms

    2. **SPACE = AND**: Most APIs treat spaces as AND (all terms must match)
       ❌ "egyptology ancient egypt pharaohs archaeology" = 5 ANDs = 0 results
       ✅ "ancient egypt archaeology" = 3 terms = good results

    3. **USE PHRASES**: Use quotes for multi-word concepts
       ❌ "machine learning neural networks" = must match all 4 words separately
       ✅ "machine learning" = phrase match, better precision

    4. **ACADEMIC TERMINOLOGY**: Use specific domain vocabulary
       ❌ "egypt history" (too generic)
       ✅ "ancient egypt archaeology" (specific field)

    GOOD query expansion examples:
      User: "egypt history" → You: "ancient egypt archaeology"
      User: "climate" → You: "climate change"
      User: "AI" → You: "machine learning artificial intelligence"

    BAD query expansion (TOO MANY TERMS - causes 0 results):
      ❌ "egyptology ancient egypt pharaohs archaeology historical civilization"
      ❌ "climate change climatology atmospheric environmental science"

    Keep queries concise: 2-4 core concepts maximum for best results.

    ---

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

    📋 SCOPE & LIMITATIONS:
    This tool searches for ACADEMIC RESEARCH PAPERS:
    ✅ Journal articles, preprints, conference papers, dissertations
    ✅ Papers ABOUT topics (e.g., "scholarship on Le Morte d'Arthur")
    ❌ Primary literary texts/books (e.g., "Le Morte d'Arthur full text")
    ❌ Non-scholarly content (news, blogs, general books)

    🔗 FOR PRIMARY LITERARY TEXTS:
    - Project Gutenberg: gutenberg.org (public domain books)
    - Internet Archive: archive.org (books, manuscripts, media)
    - HathiTrust: hathitrust.org (digitized books)
    - Google Books: books.google.com (book search)

    💡 EXAMPLE:
    ✅ "scholarship on Arthurian legend" → Use paperez (finds academic papers)
    ❌ "Le Morte d'Arthur full text" → Use Project Gutenberg (finds the book)

    Args:
        query: Search query (keywords, DOI with "doi:" prefix, title, or author)
        limit: Maximum number of results to return (default: 10, max recommended: 20)
        force_category: 🎯 FORCE SPECIFIC SOURCE TYPES (optional)
                       - "preprints" → arXiv, SocArXiv, OSF
                       - "journals" → CrossRef, PubMed, DOAJ
                       - "open_access" → CORE, DOAJ, arXiv
                       - "historical" → CORE, CrossRef
                       - "recent" → arXiv, Semantic Scholar

    🤖 AI USERS - WHEN TO CREATE CUSTOM CONFIGS:
    If you get 0 results with an optimized query (2-4 keywords, proper terms), this is a DOMAIN COVERAGE ISSUE, not a query problem.

    ⚠️ CRITICAL: No amount of query optimization will help if default sources don't cover your research domain. Immediately check if your topic needs custom configs below.

    🚨 PROACTIVE TRIGGERS - Create custom config when you see ANY of these:

    1. ❌ ZERO RESULTS: Optimized query (2-4 keywords) returns 0 papers
    2. ❌ LOW RESULTS: < 5 papers for well-known topics/figures (e.g., "Kant ethics" with 2 results)
    3. ❌ DISCIPLINE MISMATCH: Philosophy query returns only CS/AI papers (wrong field, not philosophy scholarship)
    4. ❌ SOURCE MISMATCH: All results from arXiv/Semantic Scholar for humanities topics

    💡 QUALITY > QUANTITY: 2 CS papers about formalizing Kant ≠ philosophy scholarship coverage
       Even if you get results, check if they're FROM the right discipline, not just ABOUT the topic.

    ✅ DON'T CREATE CUSTOM CONFIG IF:
    - Default sources return relevant, high-quality results that match your query intent
    - Results are FROM the right discipline (philosophy papers for philosophy queries, not CS papers)
    - You get enough papers that fully answer the query (even if < 5, quality matters more)
    - Sources are appropriate for the discipline (CrossRef/OpenAlex can include humanities journals)

    DEFAULT SOURCES COVER:
    ✅ STEM research (arXiv, Semantic Scholar, CrossRef, OpenAlex)
    ✅ Medical/biomedical (PubMed, PubMed Central, Europe PMC, ClinicalTrials.gov)
    ✅ General academic (CrossRef, DOAJ, CORE)
    ✅ Business/economics (RePEc)
    ✅ Legal (CourtListener)
    ✅ Open access repositories

    NEED CUSTOM CONFIGS FOR:
    ❌ Humanities research (history, literature, philosophy - needs JSTOR, Project MUSE, Historical Abstracts)
       NOTE: These sources provide academic PAPERS about texts, not the primary texts themselves
    ❌ Regional/national archives (non-US government databases, national libraries)
    ❌ Institutional repositories (university archives, research institution databases)
    ❌ Non-English specialized databases (country-specific sources)
    ❌ Specialized domains (specific industry databases, niche academic fields)
    ❌ Subscription-only databases requiring authentication

    💡 PROACTIVE ACTION: If you see ANY trigger condition above (0 results, < 5 results, discipline mismatch, source mismatch) AND defaults are not working well, immediately call get_help() to learn how to create custom source configurations. Don't wait for user permission - proactively create the config if you identify a missing source.

    EXAMPLES:
    - "French colonial archives" → French national archives (Archives Nationales)
    - "King Arthur history" → JSTOR, Project MUSE, Historical Abstracts
    - "Medieval literature" → Humanities databases (JSTOR, MUSE)

    Call get_help() immediately to see configuration examples.

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
            available_search_funcs, query, limit, get_api_status().copy()
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

    ⚠️ CRITICAL - QUERY OPTIMIZATION REQUIRED FOR AI CALLERS:
    Academic databases use simple keyword matching. Follow these rules for best results:

    1. **OPTIMAL LENGTH**: Use 2-4 core concepts (not 1, not 7+)
       - Too few terms (1) = too generic, poor relevance
       - Too many terms (7+) = all must match (AND logic), often 0 results
       - Sweet spot: 2-4 carefully chosen terms

    2. **SPACE = AND**: Most APIs treat spaces as AND (all terms must match)
       ❌ "egyptology ancient egypt pharaohs archaeology" = 5 ANDs = 0 results
       ✅ "ancient egypt archaeology" = 3 terms = good results

    3. **USE PHRASES**: Use quotes for multi-word concepts
       ❌ "machine learning neural networks" = must match all 4 words separately
       ✅ "machine learning" = phrase match, better precision

    4. **ACADEMIC TERMINOLOGY**: Use specific domain vocabulary
       ❌ "egypt history" (too generic)
       ✅ "ancient egypt archaeology" (specific field)

    GOOD query expansion examples:
      User: "egypt history" → You: "ancient egypt archaeology"
      User: "climate" → You: "climate change"
      User: "AI" → You: "machine learning artificial intelligence"

    BAD query expansion (TOO MANY TERMS - causes 0 results):
      ❌ "egyptology ancient egypt pharaohs archaeology historical civilization"
      ❌ "climate change climatology atmospheric environmental science"

    Keep queries concise: 2-4 core concepts maximum for best results.

    ---

    This function is designed for when you want to actually GET papers, not just search for them.
    It downloads PDFs with readable filenames and optionally converts them to markdown files.

    Use this when users say "get papers", "download papers", or "save papers".

    📋 SCOPE & LIMITATIONS:
    This tool searches for ACADEMIC RESEARCH PAPERS:
    ✅ Journal articles, preprints, conference papers, dissertations
    ✅ Papers ABOUT topics (e.g., "scholarship on Le Morte d'Arthur")
    ❌ Primary literary texts/books (e.g., "Le Morte d'Arthur full text")
    ❌ Non-scholarly content (news, blogs, general books)

    🔗 FOR PRIMARY LITERARY TEXTS:
    - Project Gutenberg: gutenberg.org (public domain books)
    - Internet Archive: archive.org (books, manuscripts, media)
    - HathiTrust: hathitrust.org (digitized books)
    - Google Books: books.google.com (book search)

    💡 EXAMPLE:
    ✅ "scholarship on Arthurian legend" → Use paperez (finds academic papers)
    ❌ "Le Morte d'Arthur full text" → Use Project Gutenberg (finds the book)

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

    🤖 AI USERS - WHEN TO CREATE CUSTOM CONFIGS:
    If you get 0 results with an optimized query (2-4 keywords, proper terms), this is a DOMAIN COVERAGE ISSUE, not a query problem.

    ⚠️ CRITICAL: No amount of query optimization will help if default sources don't cover your research domain. Immediately check if your topic needs custom configs below.

    🚨 PROACTIVE TRIGGERS - Create custom config when you see ANY of these:

    1. ❌ ZERO RESULTS: Optimized query (2-4 keywords) returns 0 papers
    2. ❌ LOW RESULTS: < 5 papers for well-known topics/figures (e.g., "Kant ethics" with 2 results)
    3. ❌ DISCIPLINE MISMATCH: Philosophy query returns only CS/AI papers (wrong field, not philosophy scholarship)
    4. ❌ SOURCE MISMATCH: All results from arXiv/Semantic Scholar for humanities topics

    💡 QUALITY > QUANTITY: 2 CS papers about formalizing Kant ≠ philosophy scholarship coverage
       Even if you get results, check if they're FROM the right discipline, not just ABOUT the topic.

    ✅ DON'T CREATE CUSTOM CONFIG IF:
    - Default sources return relevant, high-quality results that match your query intent
    - Results are FROM the right discipline (philosophy papers for philosophy queries, not CS papers)
    - You get enough papers that fully answer the query (even if < 5, quality matters more)
    - Sources are appropriate for the discipline (CrossRef/OpenAlex can include humanities journals)

    DEFAULT SOURCES COVER:
    ✅ STEM research (arXiv, Semantic Scholar, CrossRef, OpenAlex)
    ✅ Medical/biomedical (PubMed, PubMed Central, Europe PMC, ClinicalTrials.gov)
    ✅ General academic (CrossRef, DOAJ, CORE)
    ✅ Business/economics (RePEc)
    ✅ Legal (CourtListener)
    ✅ Open access repositories

    NEED CUSTOM CONFIGS FOR:
    ❌ Humanities research (history, literature, philosophy - needs JSTOR, Project MUSE, Historical Abstracts)
       NOTE: These sources provide academic PAPERS about texts, not the primary texts themselves
    ❌ Regional/national archives (non-US government databases, national libraries)
    ❌ Institutional repositories (university archives, research institution databases)
    ❌ Non-English specialized databases (country-specific sources)
    ❌ Specialized domains (specific industry databases, niche academic fields)
    ❌ Subscription-only databases requiring authentication

    💡 PROACTIVE ACTION: If you see ANY trigger condition above (0 results, < 5 results, discipline mismatch, source mismatch) AND defaults are not working well, immediately call get_help() to learn how to create custom source configurations. Don't wait for user permission - proactively create the config if you identify a missing source.

    EXAMPLES:
    - "French colonial archives" → French national archives (Archives Nationales)
    - "King Arthur history" → JSTOR, Project MUSE, Historical Abstracts
    - "Medieval literature" → Humanities databases (JSTOR, MUSE)

    Call get_help() immediately to see configuration examples.

    Args (continued):
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
            available_categories[cat_name] = cat_info.get(
                "description", "Custom category"
            )

        # Get available sources with descriptions
        available_sources = {}
        for source_name, source_config in config.sources.items():
            if source_config.enabled:
                description = getattr(
                    source_config.config,
                    "description",
                    f"{source_name} academic database",
                )
                available_sources[source_name] = description

        return {
            "available_categories": available_categories,
            "available_sources": available_sources,
            "category_count": len(available_categories),
            "source_count": len(available_sources),
            "note": "This data is loaded dynamically from your current configuration",
        }

    except Exception as e:
        return {
            "available_categories": {"error": f"Could not load categories: {str(e)}"},
            "available_sources": {"error": f"Could not load sources: {str(e)}"},
            "category_count": 0,
            "source_count": 0,
            "note": "Error loading dynamic configuration data",
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
                sources_available = [
                    s for s in resolved_sources if current_api_status.get(s, False)
                ]
                sources_unavailable = [
                    s for s in resolved_sources if not current_api_status.get(s, False)
                ]

                categories_info[cat_name] = {
                    "display_name": cat_config.display_name,
                    "description": cat_config.description,
                    "type": cat_config.type,
                    "sources": sources if cat_config.type == "standard" else [],
                    "includes": (
                        cat_config.includes if cat_config.type == "meta" else []
                    ),
                    "resolved_sources": resolved_sources,
                    "sources_available": sources_available,
                    "sources_unavailable": sources_unavailable,
                    "functional": len(sources_available) > 0,
                    "max_results_per_source": cat_config.max_results_per_source,
                    "parallel_search": cat_config.parallel_search,
                    "merge_strategy": getattr(cat_config, "merge_strategy", None),
                    "weights": getattr(cat_config, "weights", {}),
                }
            except Exception as e:
                # If there's an error processing a category, include error info
                categories_info[cat_name] = {
                    "error": f"Failed to process category: {str(e)}",
                    "type": cat_config.type,
                    "functional": False,
                }

        # Count functional categories
        functional_categories = sum(
            1 for info in categories_info.values() if info.get("functional", False)
        )
        total_categories = len(categories_info)

        # Get routing configuration
        routing_info = (
            {
                "enabled": config.routing.enabled,
                "fallback_enabled": config.routing.fallback_enabled,
                "domain_keywords": dict(config.routing.domain_keywords),
                "domain_categories": dict(config.routing.domain_categories),
            }
            if config.routing
            else {"enabled": False}
        )

        return {
            "configuration_loaded": True,
            "yaml_config": "Using YAML-based configuration",
            "version": config.version,
            "default_category": config.default_category,
            "categories": {
                "total_categories": total_categories,
                "functional_categories": functional_categories,
                "available_categories": list(categories_info.keys()),
                "category_details": categories_info,
            },
            "sources": {
                "total_sources": len(config.sources),
                "enabled_sources": len(
                    [s for s, cfg in config.sources.items() if cfg.enabled]
                ),
                "available_sources": len(
                    [
                        s
                        for s in get_api_status().keys()
                        if get_api_status().get(s, False)
                    ]
                ),
                "source_names": list(config.sources.keys()),
            },
            "routing": routing_info,
            "performance": {
                "max_concurrent_searches": config.max_concurrent_searches,
                "global_cache_enabled": config.global_cache_enabled,
                "global_cache_expire": config.global_cache_expire,
                "default_output_dir": config.default_output_dir,
            },
        }

    except Exception as e:
        return {
            "configuration_loaded": False,
            "error": f"Failed to load configuration: {str(e)}",
            "yaml_config": "Configuration loading failed",
        }


@mcp.tool
async def get_status(force_reload: bool = False) -> dict[str, Any]:
    """
    Get comprehensive system status including API health, source monitoring, and configuration details.

    Reports operational status of all academic databases, detailed health metrics, performance data,
    cache usage, and comprehensive configuration details with category verification for AI users.

    Args:
        force_reload: If True, force reload configuration before checking status.
                     Useful when custom configs added after server startup.
                     When watchdog is unavailable, use this to manually reload configs.
                     Default: False

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
    # Force reload configuration if requested
    if force_reload:
        try:
            from paperez_mcp.config import get_config_manager

            config_manager = get_config_manager()
            config_manager._reload_config()
            logger.info(
                "🔄 Configuration force-reloaded by get_status(force_reload=True)"
            )
        except Exception as e:
            logger.warning(f"Failed to force-reload configuration: {e}")

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

    # Add config diagnostics
    try:
        from paperez_mcp.config import get_config_manager

        # Check if watchdog is available
        try:
            from watchdog.observers import Observer  # type: ignore[import-not-found]

            _ = Observer  # Mark as intentionally imported for availability check
            watchdog_available = True
        except ImportError:
            watchdog_available = False

        config_manager = get_config_manager()
        config_directories = [
            str(d) for d in config_manager.config_directories.values()
        ]

        # Get failed configs
        failed_configs = config_manager.get_failed_configs()

        basic_status["config_diagnostics"] = {
            "hot_reload_available": watchdog_available,
            "config_directories_watched": (
                config_directories if watchdog_available else []
            ),
            "restart_required_for_new_configs": not watchdog_available,
            "manual_reload_available": True,
            "manual_reload_command": "get_status(force_reload=True)",
            "failed_configs": failed_configs,
            "failed_configs_count": len(failed_configs),
            "has_failed_configs": len(failed_configs) > 0,
        }
    except Exception as e:
        logger.warning(f"Failed to add config diagnostics: {e}")
        basic_status["config_diagnostics"] = {"error": str(e)}

    return basic_status


@mcp.tool
async def get_help() -> dict[str, Any]:
    """
    Get comprehensive configuration guidance and help for PaperezMCP.

    ⚠️ AI USERS: You can call this proactively! Don't wait to be asked.
    If you need a custom category or source for any research topic, create it.
    Examples: regional databases, institutional repositories, domain-specific APIs.

    Provides detailed instructions on how to create configuration files, including
    file paths, schemas, available options, and examples for customizing the system.

    Args:
        None - This tool takes no parameters

    Returns:
        Dictionary containing:
        - config_guide: Complete configuration setup guide
        - file_paths: Required file paths for configuration
        - schema_info: Configuration schema and structure
        - examples: Common configuration examples (including authentication & obscure sources)
        - troubleshooting: Common issues and solutions
    """

    from pathlib import Path

    # Get dynamic category and source information first
    dynamic_info = await _get_current_categories_and_sources()

    help_info = {
        "config_guide": {
            "overview": (
                "PaperezMCP uses YAML configuration files to customize sources, categories, and behavior.\n\n"
                "📁 CONFIG FILE CHANGES: Detected dynamically - NO restart needed!\n"
                "🔧 MCP SERVER CODE CHANGES: Require pushing to GitHub + restarting Claude Code.\n\n"
                "💡 When to restart: Only when the Python code (.py files) changes. "
                "Config (.yaml files) reload automatically."
            ),
            "setup_approaches": {
                "single_file": {
                    "description": "Traditional single config.yaml approach",
                    "path": ".paperez/config/config.yaml",
                    "use_case": "Complete custom configuration",
                },
                "multi_file": {
                    "description": "RECOMMENDED: Individual YAML files for different purposes",
                    "path": ".paperez/config/my-custom-category.yaml",
                    "use_case": "Adding custom categories without complex source definitions",
                },
            },
            "setup_steps": [
                "1. Create the configuration directory: mkdir -p .paperez/config/",
                "2. Choose approach: single config.yaml OR individual .yaml files",
                "3. Create your configuration file(s) using examples below",
                "4. Use get_status() immediately to verify - changes are detected instantly!",
                "5. Check 'categories.category_details' in get_status() output to confirm your categories are loaded",
            ],
            "important_notes": [
                "🔥 DYNAMIC LOADING: Changes take effect immediately - no restart needed!",
                "📁 MULTI-FILE SUPPORT: Create separate .yaml files for different categories",
                "🔄 SMART MERGING: All .yaml files in .paperez/config/ are automatically merged",
                "✅ INSTANT VERIFICATION: Use get_status() to see your changes immediately",
                "⚠️ SOURCE VALIDATION: Only reference sources that exist (see available_sources below)",
            ],
            "ai_user_guidance": [
                "🤖 AI USERS: You are ENCOURAGED to create custom configs proactively",
                "📚 Don't wait for user permission - if you need a specialized source, add it",
                "🎯 Examples: Regional archives, institutional repos, domain-specific databases",
                "✅ Call get_help() anytime to learn about adding custom sources",
                "⚡ Changes take effect immediately - test with get_status() right after creating config",
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
            "auth_api_key_header": {
                "description": "API with authentication via header (common pattern)",
                "content": """sources:
  my_auth_api:
    name: my_auth_api
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: API requiring authentication
      base_url: https://api.example.com
      search_path: /search
      query_param: q
      limit_param: limit
      response_format: json
      results_path: results
      auth_type: Bearer  # or ApiKey, Token, etc.
      auth_header: Authorization  # Header name
      api_key: "YOUR_API_KEY_HERE"  # Your actual key
      # Result: Authorization: Bearer YOUR_API_KEY_HERE
      field_mappings:
        title: title
        authors: authors
        doi: doi
        year: year
        abstract: abstract
        url: url
      rate_limit_delay: 0.5""",
            },
            "auth_query_param": {
                "description": "API with key as query parameter (alternate pattern)",
                "content": """sources:
  my_api:
    name: my_api
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: API with query parameter authentication
      base_url: https://api.example.com
      search_path: /search
      query_param: q
      limit_param: limit
      response_format: json
      results_path: data
      extra_params:
        api_key: "YOUR_KEY_HERE"
        format: json
      # Result: ?q=query&api_key=YOUR_KEY_HERE&format=json&limit=10
      field_mappings:
        title: title
        authors: authors
        doi: identifier
        year: publication_year
        abstract: summary
        url: link
      rate_limit_delay: 0.5""",
            },
            "complex_field_mappings": {
                "description": "Handling nested JSON responses with arrays",
                "content": """sources:
  complex_api:
    name: complex_api
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: API with complex nested JSON structure
      base_url: https://api.example.com
      search_path: /search
      query_param: query
      limit_param: max_results
      response_format: json
      results_path: data.results  # Nested under data.results
      field_mappings:
        title: metadata.title.0  # First element of title array
        authors: contributors.authors  # Nested object path
        doi: identifiers.doi  # Nested under identifiers
        year: dates.published.year  # Deep nesting
        abstract: content.summary.text
        url: links.html  # Direct link

      # JSON structure this handles:
      # {
      #   "data": {
      #     "results": [
      #       {
      #         "metadata": {"title": ["Paper Title"]},
      #         "contributors": {"authors": [...]},
      #         "identifiers": {"doi": "10.1234/..."},
      #         "dates": {"published": {"year": 2023}},
      #         "content": {"summary": {"text": "Abstract..."}},
      #         "links": {"html": "https://..."}
      #       }
      #     ]
      #   }
      # }
      rate_limit_delay: 0.5""",
            },
            "institutional_repository": {
                "description": "DSpace institutional repository (common university archive pattern)",
                "content": """sources:
  university_archive:
    name: university_archive
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: "University XYZ Institutional Repository (DSpace)"
      coverage: university research, theses, dissertations, faculty publications
      base_url: https://repository.university.edu
      search_path: /rest/items
      query_param: query
      limit_param: limit
      response_format: json
      field_mappings:
        title: name
        authors: metadata.dc.creator
        abstract: metadata.dc.description.abstract
        year: metadata.dc.date.issued
        url: handle
        doi: metadata.dc.identifier.doi
      rate_limit_delay: 1.0  # Be respectful to university servers

# NOTE: DSpace is used by many universities. Replace base_url with:
# - MIT: https://dspace.mit.edu
# - Cambridge: https://www.repository.cam.ac.uk
# - Find yours: search "[your university] institutional repository dspace\"""",
            },
            "regional_preprint_server": {
                "description": "Regional preprint server (ChemRxiv, bioRxiv pattern)",
                "content": """sources:
  chemrxiv:
    name: chemrxiv
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: "ChemRxiv - Chemistry preprint server"
      coverage: chemistry preprints, chemical research, early-stage chemistry findings
      base_url: https://chemrxiv.org/engage/api-gateway/chemrxiv/public-api/v1
      search_path: /items
      query_param: term
      limit_param: limit
      response_format: json
      results_path: itemHits
      field_mappings:
        title: item.title
        authors: item.authors
        abstract: item.abstract
        year: item.publishedDate
        doi: item.doi
        url: item.url
      rate_limit_delay: 0.5

# Similar preprint servers you can add:
# - bioRxiv (biology): biorxiv.org
# - medRxiv (medicine): medrxiv.org
# - SocArXiv (social sciences): osf.io/preprints/socarxiv
# - PsyArXiv (psychology): osf.io/preprints/psyarxiv""",
            },
            "non_english_database": {
                "description": "Non-English database (HAL French archive pattern)",
                "content": """sources:
  hal_french:
    name: hal_french
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: "HAL - French open science archive"
      coverage: French academic research, multidisciplinary, European research
      base_url: https://api.archives-ouvertes.fr
      search_path: /search
      query_param: q
      limit_param: rows
      response_format: json
      results_path: response.docs
      extra_params:
        wt: json
        fl: "title_s,authFullName_s,abstract_s,producedDateY_i,uri_s,doiId_s"
      field_mappings:
        title: title_s.0
        authors: authFullName_s
        abstract: abstract_s.0
        year: producedDateY_i
        url: uri_s
        doi: doiId_s
      rate_limit_delay: 0.5

# Other non-English archives:
# - J-STAGE (Japan): jstage.jst.go.jp
# - SciELO (Latin America): scielo.org
# - CNKI (China): cnki.net
# - Redalyc (Latin America): redalyc.org""",
            },
            "government_data_portal": {
                "description": "Government data portal (data.gov pattern)",
                "content": """sources:
  datagov:
    name: datagov
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: "Data.gov - US government open data"
      coverage: government datasets, research data, policy documents, public data
      base_url: https://catalog.data.gov/api/3/action
      search_path: /package_search
      query_param: q
      limit_param: rows
      response_format: json
      results_path: result.results
      field_mappings:
        title: title
        authors: organization.title
        abstract: notes
        year: metadata_created
        url: url
      rate_limit_delay: 0.2

# Similar government portals:
# - EU Open Data: data.europa.eu
# - UK Government: data.gov.uk
# - Canada: open.canada.ca
# - Australia: data.gov.au""",
            },
            "domain_specific_astrophysics": {
                "description": "Domain-specific example: NASA Astrophysics Data System",
                "content": """sources:
  nasa_ads:
    name: nasa_ads
    type: http_api
    enabled: false  # Requires API key
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: "NASA ADS - Astrophysics Data System"
      coverage: astronomy, astrophysics, planetary science, physics
      base_url: https://api.adsabs.harvard.edu/v1
      search_path: /search/query
      query_param: q
      limit_param: rows
      response_format: json
      results_path: response.docs
      auth_type: Bearer
      auth_header: Authorization
      # api_key: "YOUR_NASA_ADS_KEY"  # Get from: ui.adsabs.harvard.edu
      field_mappings:
        title: title.0
        authors: author
        abstract: abstract
        year: year
        doi: doi.0
        url: url
      rate_limit_delay: 0.1

# Instructions:
# 1. Create account at ui.adsabs.harvard.edu
# 2. Generate API key from account settings
# 3. Add key above and set enabled: true""",
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
                    "example": "Instead of defining new sources, reference existing ones like: sources: [arxiv, crossref]",
                },
                "category_not_appearing": {
                    "error": "Custom category doesn't show in get_status()",
                    "cause": "YAML syntax error or invalid source references",
                    "solution": "Check YAML indentation, ensure sources exist in available_sources list below",
                },
            },
            "faulty_configs": {
                "description": "Faulty configs are IGNORED, not break the system - check get_status()['config_diagnostics']['failed_configs']",
                "common_errors": {
                    "YAML syntax": "Invalid YAML: tabs instead of spaces, missing quotes, mismatched brackets",
                    "Schema validation": "Invalid field names, wrong types, required fields missing",
                    "File permissions": "Cannot read config file due to permission issues",
                },
                "how_to_check": [
                    "1. Run get_status() and check 'config_diagnostics.has_failed_configs'",
                    "2. If true, inspect 'config_diagnostics.failed_configs' for details",
                    "3. Each entry shows: file path, error message, error type",
                    "4. Fix the error and run get_status(force_reload=True) to retry",
                ],
                "system_behavior": [
                    "✅ Faulty configs are skipped - system continues with working configs",
                    "✅ Default sources always available as fallback",
                    "⚠️ Failed configs are logged with details in get_status()",
                    "🔄 Fix the error and reload with get_status(force_reload=True)",
                ],
                "prevention": [
                    "🧪 Test config immediately after creation with get_status()",
                    "📝 Validate YAML syntax before committing (use online validator)",
                    "🔍 Check example configs in get_help() for correct structure",
                    "⚡ Make small changes and test incrementally",
                ],
            },
            "config_not_loading": [
                "✅ FIRST: Run get_status() - config loads dynamically, check 'configuration_loaded' field",
                "📁 Check file path: .paperez/config/ directory with .yaml extension",
                "📝 Validate YAML syntax (use online YAML validator)",
                "🔍 Check 'categories.total_categories' in get_status() - should increase with your additions",
                "⚠️ Ensure source names match exactly those in 'available_sources' below",
            ],
            "sources_not_working": [
                "🔍 Run get_status() and check 'config.categories.category_details.YOUR_CATEGORY.functional'",
                "✅ Verify sources in your category exist in 'available_sources' list below",
                "📊 Check 'sources_available' vs 'sources_unavailable' in get_status() output",
                "⚡ API issues are temporary - categories remain functional when APIs recover",
            ],
            "yaml_syntax_errors": [
                "🔤 Use spaces for indentation, never tabs",
                '📝 Quote strings with special characters: display_name: "My Research & Analysis"',
                "📋 List format: sources: [arxiv, crossref] OR sources:\\n  - arxiv\\n  - crossref",
                "🔍 Check brackets, quotes, and colons are properly closed",
                "🧪 Test immediately with get_status() after each change",
            ],
            "verification_workflow": [
                "1. Create your .yaml file in .paperez/config/",
                "2. Immediately run get_status() - no restart needed!",
                "3. Check 'config.categories.total_categories' increased",
                "4. Find your category in 'config.categories.category_details'",
                "5. Verify 'functional: true' and correct source count",
                "6. Test with browse_papers(force_category='your_category_name')",
            ],
            "obscure_source_tips": {
                "finding_api_documentation": [
                    "🔍 Search: '[source name] API documentation'",
                    "📚 Look for: OpenAPI spec, REST API docs, developer portal",
                    "🧪 Test endpoint: Use curl or httpie to test API responses first",
                    "📊 Inspect response: Understand JSON structure before field mapping",
                    "💡 Similar patterns: Many archives use DSpace, ePrints, or OJS software",
                ],
                "common_repository_patterns": {
                    "DSpace": "base_url/rest/items?query=X (many universities)",
                    "EPrints": "base_url/cgi/search/simple?q=X&output=JSON (UK universities)",
                    "OJS": "base_url/api/v1/submissions?searchPhrase=X (journal systems)",
                    "Dataverse": "base_url/api/search?q=X&type=dataset (Harvard pattern)",
                    "CKAN": "base_url/api/3/action/package_search?q=X (data portals)",
                },
                "rate_limiting_strategy": [
                    "⏱️ Start conservative: rate_limit_delay: 1.0 (1 second between requests)",
                    "📉 Decrease gradually: If API is fast and tolerant, try 0.5 or 0.2",
                    "📈 Increase if needed: If you get 429 (Too Many Requests), increase delay",
                    "🚫 Check limits: Some APIs have hourly limits (check documentation)",
                    "⚡ Academic APIs usually generous: Typically thousands of requests per hour",
                    "🤝 Be respectful: University/institutional servers may be less robust",
                ],
                "field_mapping_tips": [
                    "🎯 Test with single result first: Use limit=1 to inspect response",
                    "📝 Use browser/curl: Visit API endpoint directly to see JSON structure",
                    "🔍 Handle arrays: Use .0 for first element (e.g., title.0)",
                    "🔗 Nested paths: Use dots for nesting (e.g., metadata.authors.name)",
                    "⚠️ Missing fields: System handles missing fields gracefully",
                    "🧪 Test incrementally: Add one mapping at a time, verify with get_status()",
                ],
                "authentication_troubleshooting": [
                    "🔑 Header vs Query: Check if API wants key in header or URL parameter",
                    "📋 Token prefix: Some need 'Bearer', 'Token', or 'ApiKey' prefix",
                    "🔐 Environment vars: Consider using env vars for keys (not in committed YAML)",
                    "✅ Test first: Use curl with your key before adding to config",
                    "📚 Check docs: API documentation usually has authentication examples",
                ],
            },
            "config_reload_and_visibility": {
                "custom_category_not_showing": {
                    "symptoms": "Created custom config but get_status() doesn't show new category",
                    "diagnosis": "Config loaded once on startup, not automatically reloaded in some environments",
                    "solutions": [
                        "Solution 1 (Recommended): Restart Claude Code after creating custom config",
                        "Solution 2: Call get_status(force_reload=True) to manually reload config",
                        "Solution 3: Verify watchdog is installed: pip install watchdog>=3.0.0 (enables auto-reload)",
                        "Solution 4: Check config file syntax with online YAML validator",
                    ],
                    "verification": "After reload, 'total_categories' in get_status() should increase",
                },
                "config_reload_behavior": {
                    "hot_reload_enabled": "Config changes detected automatically within 1-2 seconds (requires watchdog package)",
                    "hot_reload_disabled": "Restart Claude Code or use get_status(force_reload=True)",
                    "check_status": "Run get_status() and look at 'config_diagnostics.hot_reload_available' field",
                },
                "common_reload_issues": [
                    {
                        "issue": "Category not found when using force_category",
                        "fix": "Check spelling matches exactly (case-sensitive)",
                    },
                    {
                        "issue": "Category functional=False",
                        "fix": "Verify source names in category exist in sources list",
                    },
                    {
                        "issue": "Category shows 0 sources_available",
                        "fix": "Check that sources in category are enabled in config",
                    },
                    {
                        "issue": "Config changes not taking effect",
                        "fix": "Use get_status(force_reload=True) or restart Claude Code",
                    },
                    {
                        "issue": "Watchdog not available warning in logs",
                        "fix": "Install watchdog: pip install watchdog>=3.0.0 for automatic config reloading",
                    },
                ],
            },
        },
        "scope_and_use_cases": {
            "what_paperez_does": {
                "description": "Paperez finds ACADEMIC RESEARCH PAPERS",
                "supported_content": [
                    "Journal articles (Nature, Science, PLOS)",
                    "Preprints (arXiv, bioRxiv, SocArXiv)",
                    "Conference papers (ACM, IEEE)",
                    "Dissertations/theses",
                    "Research reports",
                    "Scholarly articles with DOIs/citations",
                ],
                "what_you_get": "Metadata (title, authors, abstract, DOI) + PDF download + markdown conversion",
            },
            "what_paperez_does_not_do": {
                "description": "Paperez does NOT provide primary literary texts or full books",
                "out_of_scope": [
                    "❌ Full text of novels/literature (e.g., 'Le Morte d'Arthur')",
                    "❌ Non-academic books (fiction, popular non-fiction)",
                    "❌ Primary source manuscripts",
                    "❌ News articles, blog posts",
                    "❌ General web content",
                ],
                "use_instead": {
                    "literary_texts": "Project Gutenberg (gutenberg.org), Internet Archive (archive.org)",
                    "books": "Google Books (books.google.com), HathiTrust (hathitrust.org)",
                    "manuscripts": "Institutional digital libraries, national archives",
                },
            },
            "use_case_examples": {
                "humanities_research_correct": {
                    "query": "scholarship on Arthurian legend Malory",
                    "tool": "paperez",
                    "result": "Academic papers ABOUT Le Morte d'Arthur (literary analysis, historical context)",
                },
                "humanities_research_incorrect": {
                    "query": "Le Morte d'Arthur full text",
                    "tool": "Project Gutenberg (gutenberg.org/ebooks/46853)",
                    "why_not_paperez": "Primary literary text, not an academic paper",
                },
                "stem_research": {
                    "query": "machine learning transformers",
                    "tool": "paperez",
                    "result": "Recent research papers from arXiv, Semantic Scholar, etc.",
                },
            },
        },
        "quick_start": {
            "ai_user_workflow": [
                "🤖 YOU CAN DO THIS UNPROMPTED - don't wait to be asked!",
                "🚀 FASTEST: Use 'custom_category_only' example for simple needs",
                "🔧 ADVANCED: Use real-world examples below for obscure sources",
                "1. mkdir -p .paperez/config/",
                "2. Create .yaml file (use appropriate example)",
                "3. Run get_status() to verify immediately",
                "4. Test with browse_papers(force_category='your_category')",
                "",
                "💡 When to add custom sources (DO THIS PROACTIVELY, but check if defaults work first!):",
                "- 0 results OR < 5 results for well-known topics = coverage gap",
                "- Discipline mismatch: philosophy query → only STEM papers = missing sources",
                "- Source mismatch: All results from arXiv/Semantic Scholar for humanities topics",
                "- Humanities research (history, literature, philosophy) - needs JSTOR/Project MUSE",
                "- User needs regional/institutional database",
                "- Research topic needs domain-specific source",
                "- User mentions specific archive/repository",
                "- You know of better sources for their query",
                "",
                "✅ DON'T CREATE if defaults return relevant, high-quality results (even if < 5)",
                "💡 Remember: 2 CS papers about Kant ≠ philosophy scholarship coverage (quality > quantity)",
            ],
            "recommended_approach": "Start with 'custom_category_only' - uses existing sources, no complex setup required",
            "verification_command": "get_status()['config']['categories']['total_categories'] should increase after adding your config",
            "success_indicators": [
                "✅ 'configuration_loaded': True in get_status()",
                "✅ 'total_categories' increased by number of categories you added",
                "✅ Your category name appears in 'available_categories' list",
                "✅ 'functional': True in your category's details",
                "✅ 'sources_available' > 0 for your category",
            ],
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
    """Main entry point for the server - with forced initialization for local path support."""
    logger.info("Starting PaperezMCP Server...")

    # Force configuration initialization at startup to fix local path invocation
    # This ensures the server works correctly when invoked via local file path
    try:
        from paperez_mcp.config.singleton import get_config_manager

        manager = get_config_manager()

        logger.info("Initializing configuration system at server startup...")
        success = manager.initialize()

        if success:
            # Verify configuration is complete
            if manager.config and manager.config.sources and manager.config.categories:
                logger.info(
                    f"✓ Configuration initialized successfully: "
                    f"{len(manager.api_status)} sources, "
                    f"{len(manager.search_functions)} search functions, "
                    f"{len(manager.config.categories)} categories ready"
                )
            else:
                logger.warning(
                    "Configuration incomplete, attempting to rebuild from hardcoded defaults"
                )
                manager._set_minimal_defaults()
                if manager.search_functions:
                    logger.info(
                        f"✓ Rebuilt configuration: {len(manager.search_functions)} search functions ready"
                    )
        else:
            logger.warning(
                "Configuration initialization failed, using comprehensive fallback"
            )
            # Force loading from hardcoded defaults
            manager._set_minimal_defaults()

            # Verify we have working search functions
            if manager.search_functions:
                logger.info(
                    f"✓ Fallback successful: {len(manager.search_functions)} search functions ready"
                )
            else:
                logger.error(
                    "CRITICAL: No search functions available even after fallback"
                )
                logger.error("Server may not function properly - consider reinstalling")
    except Exception as e:
        logger.error(f"Error during startup initialization: {e}")
        # Continue anyway - lazy loading might still work

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
