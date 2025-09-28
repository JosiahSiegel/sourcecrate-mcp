#!/usr/bin/env python3
"""
PaperezMCP - Academic Paper Research Made Easy

A comprehensive academic research server with multi-source fallback,
robust caching, and graceful error handling. Built with modular architecture.
"""

import logging
import os
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# Core imports only - heavy dependencies loaded lazily
from paperez_mcp.config import api_status, cache, config

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
    """Get search functions from unified config system"""
    from paperez_mcp.config import get_search_service

    # Use the new unified config system
    search_service = get_search_service()
    return search_service.get_search_functions()


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

    # Use enhanced routing for metadata search (no downloads)
    papers, search_log = await utils["smart_downloadable_search"](
        query,
        limit,
        search_funcs,
        utils,
        api_status.copy(),
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
        "api_status": api_status.copy(),
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
    if len(browse_results) == 0 and search_log.get("intelligent_error_suggestions"):
        error_info = search_log["intelligent_error_suggestions"]

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

    return [result]


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
        api_status=api_status.copy(),
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
        return {
            "success": False,
            "error": str(e),
            "text_path": None,
            "original_file": file_path,
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
        return {"success": False, "error": f"Download/conversion failed: {str(e)}"}


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
            return {"success": False, "error": f"Directory not found: {directory}"}

        # Find all PDF files
        pdf_files = list(Path(directory).glob("*.pdf"))
        if not pdf_files:
            return {
                "success": False,
                "error": f"No PDF files found in directory: {directory}",
            }

        if output_dir is None:
            output_dir = os.getcwd()

        os.makedirs(output_dir, exist_ok=True)

        results = []
        successful = 0
        failed = 0

        for pdf_file in pdf_files:
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
                        successful += 1
                        results.append(
                            {
                                "input_file": str(pdf_file),
                                "output_file": output_path,
                                "success": True,
                                "characters": result.get("markdown_length", 0),
                            }
                        )
                    else:
                        failed += 1
                        results.append(
                            {
                                "input_file": str(pdf_file),
                                "success": False,
                                "error": save_result.get("error"),
                            }
                        )
                else:
                    # Clean up markdown content even on failure
                    if "markdown" in result:
                        del result["markdown"]

                    failed += 1
                    results.append(
                        {
                            "input_file": str(pdf_file),
                            "success": False,
                            "error": result.get("error"),
                        }
                    )

            except Exception as e:
                failed += 1
                results.append(
                    {"input_file": str(pdf_file), "success": False, "error": str(e)}
                )

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


@mcp.tool
async def get_status() -> dict[str, Any]:
    """
    Get comprehensive system status including API health, source monitoring, and configuration details.

    Reports operational status of all academic databases, detailed health metrics, performance data,
    cache usage, and configuration details with recommendations for system improvements.

    Args:
        None - This tool takes no parameters

    Returns:
        Dictionary containing:
        - api_status: Basic status of all academic database APIs
        - cache_stats: Cache usage and configuration information
        - config: System configuration details
        - health_report: Detailed health monitoring with performance metrics
        - recommendations: Specific recommendations for system improvements
        - monitoring_enabled: Whether health monitoring is active

        health_report contains:
        - overall_status: "healthy", "degraded", or "critical"
        - sources: Detailed metrics for each source (health scores, response times, success rates)
        - summary: Count of healthy/unhealthy/disabled sources

        recommendations include:
        - severity: "high", "medium", or "low"
        - issue: Description of the problem
        - recommendation: Suggested action

    Use Cases:
        - System health monitoring and troubleshooting
        - Performance optimization insights
        - Configuration verification

    Example Usage:
        status = get_status()
        if status["health_report"]["overall_status"] == "critical":
            print("System needs attention")
    """
    # Get basic status
    basic_status: dict[str, Any] = {
        "api_status": api_status.copy(),
        "cache_stats": {
            "size": len(cache),
            "cache_dir": cache.directory,
            "size_limit": cache.size_limit,
        },
        "config": {
            "has_semantic_scholar_key": bool(config.semantic_scholar_api_key),
            "has_scraperapi_key": bool(config.scraperapi_key),
            "crossref_email": config.crossref_email,
            "max_retries": config.max_retries,
        },
    }

    # Add comprehensive health monitoring
    try:
        from paperez_mcp.utils.source_health_monitor import health_monitor

        # Perform active health check
        health_check = await health_monitor.perform_health_check()

        # Save metrics to cache for persistence
        health_monitor.save_metrics_to_cache()

        # Add health data to basic status
        basic_status.update(
            {
                "health_report": health_monitor.get_health_report(),
                "recommendations": health_monitor.get_source_recommendations(),
                "health_check_results": health_check["health_check_results"],
                "monitoring_enabled": health_monitor.monitoring_enabled,
                "timestamp": health_check["overall_report"]["timestamp"],
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

    help_info = {
        "config_guide": {
            "overview": "PaperezMCP uses YAML configuration files to customize sources, categories, and behavior.",
            "setup_steps": [
                "1. Create the configuration directory: .paperez/config/",
                "2. Place your config.yaml file in that directory",
                "3. Restart Claude Code after making changes for them to take effect",
                "4. Use get_status() to verify your configuration is working",
            ],
            "important_notes": [
                "Changes only take effect after pushing to GitHub and restarting Claude Code",
                "User configs override defaults - same-name sources/categories replace entirely",
                "Set use_default_sources: false to disable all built-in sources",
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
            "minimal_config": {
                "description": "Basic configuration with just one source",
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
        "available_categories": {
            "academic_premium": "High-quality peer-reviewed sources",
            "preprints": "Latest research from preprint repositories",
            "medical": "Medical and biomedical research sources",
            "open_access": "Freely available full-text articles",
            "historical": "Historical and archival content",
            "business": "Business, economics, and finance research",
        },
        "available_sources": {
            "crossref": "Primary academic publisher database",
            "semantic_scholar": "AI-powered academic search engine",
            "arxiv": "Preprint repository for STEM fields",
            "pubmed": "Biomedical literature database",
            "pubmed_central": "Full-text biomedical repository",
            "europe_pmc": "European life sciences database",
            "doaj": "Directory of Open Access Journals",
            "hathitrust": "Historical books and documents",
            "internet_archive": "Historical documents and archives",
            "clinicaltrials": "Clinical trials database",
        },
        "troubleshooting": {
            "config_not_loading": [
                "Ensure file is at correct path: .paperez/config/config.yaml",
                "Check YAML syntax is valid (use online YAML validator)",
                "Restart Claude Code after configuration changes",
                "Use get_status() to check if config loaded successfully",
            ],
            "sources_not_working": [
                "Check source 'enabled' field is set to true",
                "Verify API endpoints are accessible",
                "Check timeout and retry settings",
                "Review rate limiting delays",
                "Use get_status() to check API health",
            ],
            "permission_errors": [
                "Ensure .paperez directory is writable",
                "Check file permissions on config.yaml",
                "Verify directory exists before creating config file",
            ],
            "yaml_syntax_errors": [
                "Use consistent indentation (spaces, not tabs)",
                "Quote string values that contain special characters",
                "Ensure proper list formatting with dashes",
                "Check for unclosed brackets or quotes",
            ],
        },
        "quick_start": {
            "basic_setup": [
                "mkdir -p .paperez/config/",
                "Create .paperez/config/config.yaml with your desired sources",
                "Use examples above as starting points",
                "Test with get_status() and browse_papers()",
                "Push changes and restart Claude Code",
            ],
            "recommended_first_config": "Start with 'enhance_defaults_config' example to keep built-in sources while adding custom ones",
        },
    }

    return help_info


def main() -> None:
    """Main entry point for the server"""
    print("🚀 Starting PaperezMCP Server...")
    print("📚 Primary tools:")
    print(
        "  📄 download_papers: Get/download full papers as files (most users want this)"
    )
    print("  🔍 browse_papers: Quick metadata overview (titles/abstracts only)")
    print("  📝 convert_pdf_to_text: Convert PDF to plain text files")
    print("  🔄 convert_pdf_to_markdown: Convert PDF to markdown format")
    print("  📁 batch_convert_pdfs: Convert multiple PDFs in a directory")
    print("  🔧 get_status: Check system health and API status")
    print("  ❓ get_help: Configuration guide and setup instructions")
    print("")
    print("🎯 QUICK START: Use download_papers('topic') to get/download full papers!")
    print("   Only use browse_papers() if you just want to explore titles/abstracts.")
    print("   Use get_help() for configuration guidance and setup instructions.")
    print("")
    print("🔗 PaperezMCP ready at: stdio")
    mcp.run()


if __name__ == "__main__":
    main()
