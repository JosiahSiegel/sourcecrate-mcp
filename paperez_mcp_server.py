#!/usr/bin/env python3
"""
PaperezMCP - Academic Paper Research Made Easy

A comprehensive academic research server with multi-source fallback,
robust caching, and graceful error handling. Built with modular architecture.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Core imports only - heavy dependencies loaded lazily
from paperez_mcp.config import config, api_status, cache

# Lazy import flags
_PYMUPDF4LLM_AVAILABLE = None
_scholarly_setup_done = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("PaperezMCP - Academic Paper Research Made Easy")

# Lazy import helpers
def _ensure_scholarly_setup() -> None:
    """Lazy initialization of scholarly proxy setup"""
    global _scholarly_setup_done
    if not _scholarly_setup_done:
        from paperez_mcp.api_clients import setup_scholarly_proxy
        setup_scholarly_proxy()
        _scholarly_setup_done = True

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

def _lazy_import_search_functions() -> Dict[str, Any]:
    """Get search functions from unified config system"""
    from paperez_mcp.config import get_search_service

    # Use the new unified config system
    search_service = get_search_service()
    return search_service.get_search_functions()

def _lazy_import_utils() -> Dict[str, Any]:
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
        'extract_pdf_text': extract_pdf_text,
        'convert_pdf_to_markdown_content': convert_pdf_to_markdown_content,
        'download_pdf': download_pdf,
        'save_markdown_file': save_markdown_file,
        'extract_pdf_text_from_local_file': extract_pdf_text_from_local_file,
        'smart_downloadable_search': smart_downloadable_search
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

## 6 Essential Tools:

1. search_papers - Comprehensive search across 5 academic databases
   - Multi-source search (CrossRef, Semantic Scholar, arXiv, PubMed, Google Scholar)
   - Optional full-text extraction and PDF download/conversion (MAX 3 papers)
   - Supports DOI queries, author searches, and keyword searches

2. search_authors - Author profile search with citation metrics
   - Google Scholar integration for author profiles
   - Returns citation count, h-index, i10-index, and affiliations

3. convert_pdf_to_text - Local PDF text extraction
   - PyMuPDF-based extraction with unlimited character support
   - Handles complex academic document layouts

4. convert_pdf_to_markdown - Single PDF to markdown conversion
   - Zero-token conversion using pymupdf4llm
   - Preserves document structure and formatting

5. batch_convert_pdfs - Batch PDF to markdown conversion
   - Processes entire directories of PDFs
   - Zero-token conversion with progress tracking

6. get_status - System health and configuration status
   - API operational status for all databases
   - Cache statistics and configuration details

All file-saving tools default to current directory and accept custom output paths.
"""


@mcp.tool
async def browse_papers(
    query: str,
    limit: int = 10,
    force_category: str = None
) -> List[Dict[str, Any]]:
    """
    🔍 BROWSE: Find and explore papers (metadata/abstracts only)

    This function is for DISCOVERING and BROWSING papers - metadata/abstracts only.
    Use this when you want to explore what's available before downloading.

    ⚠️ METADATA ONLY: Returns titles, authors, abstracts, DOIs - no full paper content

    FOR GETTING ACTUAL PAPERS:
    📄 Use get_papers("topic") or download_papers("topic") instead!
    📄 These functions automatically download full papers as markdown files

    🔄 WHEN TO USE EACH FUNCTION:
    "Browse papers" → browse_papers("topic", limit=20) - Fast metadata overview
    "Get papers" → get_papers("topic", limit=5) - Download full papers as files
    "Save papers" → download_papers("topic", output_dir="my_papers")

    Search academic papers across multiple databases with optional full-text extraction and download.
    Searches CrossRef, Semantic Scholar, arXiv, PubMed, and Google Scholar with intelligent fallback.
    Supports DOI queries, author queries, and keyword searches.

    💡 WORKFLOW EXAMPLES:

    ## Research Workflow (Explore → Select → Download):
    Step 1: browse_papers("broad topic", limit=20)  # Get overview
    Step 2: Review abstracts and select interesting papers
    Step 3: For selected papers:
            get_papers("specific topic", limit=3)  # Download chosen papers

    ## Quick Discovery:
    browse_papers("machine learning", limit=10)  # Fast metadata overview
    get_papers("transformer architecture", limit=5)  # Download specific papers

    Args:
        query: Search query (keywords, DOI with "doi:" prefix, title, or author)
               - Keywords: "machine learning transformers", "neural networks"
               - DOI format: "doi:10.1000/xyz123" (must include "doi:" prefix)
               - Author search: "Geoffrey Hinton", "Yoshua Bengio"
               - Title search: "Attention Is All You Need"
        limit: Maximum number of results to return (default: 5, max recommended: 10)
        force_category: 🎯 FORCE SPECIFIC SOURCE TYPES (optional, overrides smart routing)
                       - "preprints" → arXiv, SocArXiv, OSF (latest research, not peer-reviewed)
                       - "journals" → CrossRef, PubMed, DOAJ (peer-reviewed publications)
                       - "open_access" → CORE, DOAJ, arXiv (free full-text available)
                       - "historical" → CORE, CrossRef (older documents, archives)
                       - "recent" → arXiv, Semantic Scholar (newest papers, last few years)
                       - "comprehensive" → Semantic Scholar, CrossRef (broad coverage)

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

        When include_full_text=True, adds:
        - full_text: Extracted text content
        - text_length: Character count of extracted text
        - extraction_method: Method used for text extraction

        When download_and_convert=True, adds:
        - local_pdf: Path to downloaded PDF file
        - local_markdown: Path to converted markdown file
        - markdown_characters: Character count of markdown
        - download_error: Error message if download failed

    🚨 KEY LIMITATIONS:
    - Default: Metadata/abstracts only, no files created
    - download_and_convert=True: MAX 3 papers per call
    - include_full_text=True: Text in memory only, not saved to files
    - For bulk operations: Requires multi-step workflow

    Example Usage:
        # ❌ WRONG - This only gets metadata/abstracts (what user experienced)
        search_papers("Balfour Declaration documents", limit=10)

        # ✅ CORRECT - Get 3 full papers as markdown files
        search_papers("Balfour Declaration documents", limit=3, download_and_convert=True)

        # ✅ CORRECT - Get full text in memory for analysis
        search_papers("Balfour Declaration documents", limit=10, include_full_text=True)

        # ✅ CORRECT - For 10+ papers as files: multi-step workflow
        # Step 1: Get metadata to review
        papers = search_papers("Balfour Declaration documents", limit=10)
        # Step 2: Download selected papers individually
        for paper in papers[0]["results"][:5]:  # Select first 5 papers
            if paper.get("pdf_url"):
                convert_pdf_to_markdown(paper["pdf_url"],
                                      output_path=f"papers/{paper['title'][:50]}.md")

        # 🎯 DIRECT SOLUTION for "get 10 papers on topic and save them":
        # Option A: Multiple download calls (3 papers each)
        search_papers("topic", limit=3, download_and_convert=True)  # Get first 3
        # Option B: Use the multi-step workflow above
    """
    # Lazy import utilities
    _ensure_scholarly_setup()
    utils = _lazy_import_utils()
    search_funcs = _lazy_import_search_functions()

    # Use enhanced routing for metadata search (no downloads)
    papers, search_log = await utils['smart_downloadable_search'](
        query, limit, search_funcs, utils, api_status, force_category, metadata_only=True
    )

    # Convert to browse format (metadata only, remove download info)
    browse_results = []
    fallback_used = False
    original_category = None

    for paper in papers:
        browse_paper = {k: v for k, v in paper.items()
                       if k not in ['download_success', 'local_markdown', 'markdown_characters', '_fallback_used', '_original_category']}
        browse_results.append(browse_paper)

        # Check if any paper used fallback
        if paper.get('_fallback_used'):
            fallback_used = True
            original_category = paper.get('_original_category')

    result = {
        "results": browse_results,
        "total_found": len(browse_results),
        "api_status": api_status,
        "sources_used": list(set(paper.get("source", "Unknown") for paper in browse_results)),
        "query": query
    }

    # Add fallback notification if used
    if fallback_used:
        result["fallback_notification"] = {
            "message": f"Results found using comprehensive sources (original {'smart routing' if not original_category else original_category} found no results)",
            "original_category": original_category or "smart_routing",
            "fallback_category": "comprehensive"
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
            "query_refinements": safe_refinements
        }

    return [result]


@mcp.tool
async def download_papers(
    query: str,
    limit: int = 5,
    output_dir: str = ".paperez",
    force_category: str = None,
    convert_to_markdown: bool = True
) -> List[Dict[str, Any]]:
    """
    📄 GET FULL PAPERS: Download academic papers as files (PDF or Markdown)

    This function is designed for when you want to actually GET papers, not just search for them.
    It downloads PDFs with readable filenames and optionally converts them to markdown files.

    Use this when:
    - User says "get papers", "download papers", "save papers"
    - You want actual paper content as files (PDF or Markdown)
    - Need papers for analysis, reading, or citation

    Args:
        query: Search query (keywords, DOI, title, or author)
        limit: Maximum papers to download (default: 5, recommended: 5-10)
        output_dir: Directory to save files (default: ".paperez")
        force_category: 🎯 FORCE SPECIFIC SOURCE TYPES (optional, overrides smart routing)
        convert_to_markdown: If True (default), convert PDFs to markdown. If False, keep as PDFs only.
        force_category options:
                       - "preprints" → arXiv, SocArXiv, OSF (latest research, not peer-reviewed)
                       - "journals" → CrossRef, PubMed, DOAJ (peer-reviewed publications)
                       - "open_access" → CORE, DOAJ, arXiv (free full-text available)
                       - "historical" → CORE, CrossRef (older documents, archives)
                       - "recent" → arXiv, Semantic Scholar (newest papers, last few years)
                       - "comprehensive" → Semantic Scholar, CrossRef (broad coverage)

                       💡 USE WHEN: Smart routing fails to find papers or you need specific types
                       💡 EXAMPLE: force_category="historical" for "JFK assassination" queries

    Returns:
        List containing single dict with:
        - results: List of paper objects with local file paths
        - total_found: Number of papers found
        - downloaded_count: Number successfully downloaded
        - output_directory: Where files were saved

    Example Usage:
        # Get 3 papers as markdown (default)
        download_papers("machine learning transformers", limit=3)

        # Get papers as PDFs with readable filenames
        download_papers("neural networks", limit=2, convert_to_markdown=False)

        # Save to specific directory
        download_papers("climate change", limit=5, output_dir="climate_papers")
    """
    # Lazy import utilities
    _ensure_scholarly_setup()
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
        api_status=api_status,
        force_category=force_category,
        convert_to_markdown=convert_to_markdown
    )

    return [result]


@mcp.tool
async def get_papers(
    query: str,
    limit: int = 5,
    output_dir: str = ".paperez",
    force_category: str = None,
    convert_to_markdown: bool = True
) -> List[Dict[str, Any]]:
    """
    📄 GET FULL PAPERS: Download academic papers as files (PDF or Markdown)

    This is an alias for download_papers() that matches natural language.
    When users say "get papers", they typically want the actual papers, not metadata.
    Downloads PDFs with readable filenames and optionally converts to markdown.

    Use this when:
    - User says "get papers on [topic]"
    - User wants actual content as files (PDF or Markdown), not just summaries
    - Need papers for analysis, reading, or citation

    Args:
        query: Search query (keywords, DOI, title, or author)
        limit: Maximum papers to get (default: 5, recommended: 5-10)
        output_dir: Directory to save papers (default: ".paperez")
        force_category: 🎯 FORCE SPECIFIC SOURCE TYPES (optional, overrides smart routing)
        convert_to_markdown: If True (default), convert PDFs to markdown. If False, keep as PDFs only.
        force_category options:
                       - "preprints" → arXiv, SocArXiv, OSF (latest research, not peer-reviewed)
                       - "journals" → CrossRef, PubMed, DOAJ (peer-reviewed publications)
                       - "open_access" → CORE, DOAJ, arXiv (free full-text available)
                       - "historical" → CORE, CrossRef (older documents, archives)
                       - "recent" → arXiv, Semantic Scholar (newest papers, last few years)
                       - "comprehensive" → Semantic Scholar, CrossRef (broad coverage)

                       💡 USE WHEN: Smart routing fails to find papers or you need specific types
                       💡 EXAMPLE: force_category="historical" for "JFK assassination" queries

    Returns:
        Same as download_papers() - papers saved as files (PDF or Markdown)

    Example Usage:
        # Get papers as markdown (default)
        get_papers("neural networks", limit=5)

        # Get papers as PDFs with readable filenames
        get_papers("quantum computing", convert_to_markdown=False)

        # Get papers to specific folder
        get_papers("climate research", output_dir="climate_papers")
    """
    # Lazy import utilities
    _ensure_scholarly_setup()
    utils = _lazy_import_utils()
    search_funcs = _lazy_import_search_functions()

    # Import the new paper processor service
    from paperez_mcp.services.paper_processor import process_papers

    # Use the extracted paper processing service (same as download_papers)
    result = await process_papers(
        query=query,
        limit=limit,
        output_dir=output_dir,
        search_funcs=search_funcs,
        utils=utils,
        api_status=api_status,
        force_category=force_category,
        convert_to_markdown=convert_to_markdown
    )

    return [result]


@mcp.tool
async def search_authors(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for academic authors by name.

    Returns author profiles with affiliation, research interests, citation metrics,
    and publication indices from Google Scholar.

    Args:
        name: Author name to search for
              - Full names work best: "Geoffrey Hinton", "Yoshua Bengio"
              - Partial names: "Hinton", "LeCun"
              - Names with special characters: "Jürgen Schmidhuber"
              - Institution-qualified: "Andrew Ng Stanford"
        limit: Maximum number of authors to return (default: 5, max recommended: 10)
               Higher limits may increase response time significantly

    Returns:
        List of author profile dictionaries, each containing:
        - name: Full author name as listed on Google Scholar
        - affiliation: Current institutional affiliation
        - email: Email address (if publicly available)
        - interests: List of research interests/keywords
        - citation_count: Total number of citations across all publications
        - h_index: h-index metric (papers with h or more citations)
        - i10_index: i10-index metric (papers with 10 or more citations)
        - source: Always "Google Scholar" for this tool

        Returns empty list if:
        - No authors found matching the search query
        - Google Scholar API is unavailable
        - Network connectivity issues

    Notes:
        - Google Scholar is the primary source for comprehensive author metrics
        - Results may vary based on author name variants and Google Scholar indexing
        - Citation metrics are updated by Google Scholar periodically
        - Some author profiles may be incomplete or restricted

    Example Usage:
        # Search for specific researcher
        search_authors("Geoffrey Hinton")

        # Search with broader terms
        search_authors("Bengio deep learning", limit=3)

        # Find authors by institution
        search_authors("OpenAI research", limit=5)
    """
    # Use Google Scholar for author search as it's most comprehensive for this
    if api_status["google_scholar"]:
        try:
            def _search_author() -> List[Dict[str, Any]]:
                from scholarly import scholarly
                search_query = scholarly.search_author(name)
                results = []

                for i, author in enumerate(search_query):
                    if i >= limit:
                        break

                    filled = scholarly.fill(author, sections=['basics', 'indices'])
                    result = {
                        "name": filled.get('name', ''),
                        "affiliation": filled.get('affiliation', ''),
                        "email": filled.get('email', ''),
                        "interests": filled.get('interests', []),
                        "citation_count": filled.get('citedby', 0),
                        "h_index": filled.get('hindex', 0),
                        "i10_index": filled.get('i10index', 0),
                        "source": "Google Scholar"
                    }
                    results.append(result)
                return results

            results = await asyncio.to_thread(_search_author)
            return results

        except Exception as e:
            logger.warning(f"Author search failed: {e}")

    return []










@mcp.tool
async def convert_pdf_to_text(file_path: str, output_path: Optional[str] = None, title: str = "", authors: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convert a local PDF file to plain text and save to a text file.

    Uses PyMuPDF for robust text extraction, creating a text file output
    to avoid consuming context window space. Similar to convert_pdf_to_markdown
    but outputs plain text instead.

    Args:
        file_path: Path to local PDF file
                   - Supports absolute paths: "/home/user/papers/paper.pdf"
                   - Supports relative paths: "papers/paper.pdf", "./documents/research.pdf"
                   - Must be a valid PDF file (will return error for non-PDF files)
                   - File must exist and be readable
        output_path: Output path for text file (default: current directory)
                     - If provided, uses exact path: "/path/to/output.txt"
                     - If None, creates file in current directory with format: "{filename}_full.txt"
                     - Automatically creates directories if they don't exist
                     - Overwrites existing files
        title: Optional title for the document header (default: "")
               - Added as header at top of text file
               - Example: "Attention Is All You Need"
               - If empty, no title header is added
        authors: Optional list of authors for the document header (default: None)
                 - Added as author list after title
                 - Example: ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"]
                 - If None or empty, no author section is added

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
        - Creates text files instead of returning content in response
        - Zero context window consumption (content saved to files, not returned)
        - Preserves all text content with page separators
        - Handles complex academic layouts (multi-column, figures, tables)
        - Supports Unicode and special characters
        - Fast processing using optimized PyMuPDF engine

    Limitations:
        - Cannot extract text from image-only PDFs without OCR
        - May have issues with heavily formatted or corrupted PDFs
        - Does not extract images, only text content
        - Password-protected PDFs are not supported

    Example Usage:
        # Basic conversion
        convert_pdf_to_text("research_paper.pdf")

        # With custom title and authors
        convert_pdf_to_text(
            "paper.pdf",
            title="My Research Paper",
            authors=["John Doe", "Jane Smith"]
        )

        # Custom output location
        convert_pdf_to_text(
            "input.pdf",
            output_path="/documents/extracted/paper.txt"
        )

        # Check success and get file path
        result = convert_pdf_to_text("paper.pdf")
        if result["success"]:
            text_file = result["text_path"]
            char_count = result["text_length"]
    """
    try:
        # First extract the text using existing method
        utils = _lazy_import_utils()
        extraction_result = utils['extract_pdf_text_from_local_file'](file_path)

        if not extraction_result.get("success", False):
            return extraction_result

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
            content_parts.append(f"Pages: {extraction_result.get('num_pages', 'Unknown')}")
            content_parts.append(f"File: {file_path}")
            content_parts.append(f"Extraction Method: {extraction_result.get('extraction_method', 'Unknown')}")
            content_parts.append("\n" + "="*80 + "\n")

        # Add the extracted text
        content_parts.append(extraction_result.get("text", ""))

        # Combine all parts
        full_content = "\n".join(content_parts)

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        # Return metadata only (no text content to save context)
        result = {
            "success": True,
            "text_path": output_path,
            "text_length": len(full_content),
            "original_file": file_path,
            "pages_extracted": extraction_result.get("num_pages", 0),
            "file_size": extraction_result.get("file_size", 0),
            "extraction_method": extraction_result.get("extraction_method", "PyMuPDF Local")
        }

        return result

    except Exception as e:
        logger.error(f"Error in convert_pdf_to_text: {e}")
        return {"success": False, "error": str(e), "text_path": None, "original_file": file_path}


async def _convert_pdf_to_markdown_internal(file_path: str, title: str = "", authors: Optional[List[str]] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Internal function to convert a local PDF file to formatted markdown.
    Duplicates PDF extraction logic to avoid MCP tool calling MCP tool.
    """
    utils = _lazy_import_utils()
    result = utils['convert_pdf_to_markdown_content'](file_path, title, authors)

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

        save_result = utils['save_markdown_file'](result["markdown"], markdown_path)
        if save_result.get("success"):
            result["markdown_path"] = markdown_path

        # Store markdown length and remove content to avoid context window usage
        if "markdown" in result:
            result["markdown_length"] = len(result["markdown"])
            # Don't delete markdown here yet - batch_convert_pdfs needs it
            # Will be cleaned up by the calling function

    return result


@mcp.tool
async def convert_pdf_to_markdown(
    file_path: str,
    title: str = "",
    authors: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert a local PDF file to formatted markdown.

    Uses pymupdf4llm for zero-token conversion preserving document structure,
    headings, and formatting. Ideal for academic papers and research documents.

    Args:
        file_path: Path to the PDF file to convert
                   - Supports absolute paths: "/home/user/papers/paper.pdf"
                   - Supports relative paths: "papers/paper.pdf", "./documents/research.pdf"
                   - Must be a valid PDF file (will return error for non-PDF files)
                   - File must exist and be readable
        title: Optional title for the document header (default: "")
               - Added as H1 header at top of markdown
               - Example: "Attention Is All You Need"
               - If empty, no title header is added
        authors: Optional list of authors for the document header (default: None)
                 - Added as author list after title
                 - Example: ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"]
                 - If None or empty, no author section is added
        output_path: Output path for markdown file (default: current directory)
                     - If provided, uses exact path: "/path/to/output.md"
                     - If None, creates file in current directory with format: "{filename}_full.md"
                     - Automatically creates directories if they don't exist
                     - Overwrites existing files

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

        The generated markdown file contains:
        - Structured content with preserved headings
        - Formatted tables and lists
        - Mathematical notation and special characters
        - Document metadata (title, authors, page count, etc.)
        - Page-by-page content with clear separators

        On failure, includes:
        - success: false
        - error: Error message explaining the failure

    Features:
        - Zero AI tokens used (direct PDF→markdown conversion)
        - Zero context window consumption (content saved to files, not returned)
        - Preserves document structure and formatting
        - Handles complex academic layouts
        - Maintains headings, tables, and lists
        - Supports Unicode and mathematical notation
        - Fast processing with pymupdf4llm

    Limitations:
        - Cannot handle image-only PDFs without text layers
        - Some complex formatting may be simplified
        - Tables with complex layouts may need manual adjustment
        - Figures and images are not included in output

    Example Usage:
        # Basic conversion
        convert_pdf_to_markdown("research_paper.pdf")

        # With custom title and authors
        convert_pdf_to_markdown(
            "paper.pdf",
            title="My Research Paper",
            authors=["John Doe", "Jane Smith"]
        )

        # Custom output location
        convert_pdf_to_markdown(
            "input.pdf",
            output_path="/documents/converted/paper.md"
        )

        # Check success and get file path
        result = convert_pdf_to_markdown("paper.pdf")
        if result["success"]:
            markdown_file = result["markdown_path"]
            char_count = result["markdown_length"]
    """
    result = await _convert_pdf_to_markdown_internal(file_path, title, authors, output_path)

    # Remove markdown content to avoid context window usage
    if "markdown" in result:
        del result["markdown"]

    return result




async def download_and_convert_paper(
    pdf_url: str,
    convert_to_markdown: bool = True,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
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
        download_result = await utils['download_pdf'](pdf_url, output_dir)

        if not download_result.get("success"):
            return download_result

        pdf_path = download_result["pdf_path"]

        # Convert to markdown if requested
        if convert_to_markdown:
            pymupdf4llm = _ensure_pymupdf4llm()
            if pymupdf4llm:
                # Use pymupdf4llm directly (zero tokens)
                try:
                    markdown_content = pymupdf4llm.to_markdown(pdf_path)

                    # Save markdown
                    markdown_path = pdf_path.replace('.pdf', '.md')
                    save_result = utils['save_markdown_file'](markdown_content, markdown_path)

                    if save_result.get("success"):
                        return {
                            "success": True,
                            "pdf_path": pdf_path,
                            "markdown_path": markdown_path,
                            "markdown_characters": len(markdown_content),
                            "method": "pymupdf4llm_direct"
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
                        "method": "internal_converter"
                    }
            except Exception as e:
                logger.warning(f"Internal conversion failed: {e}")

        return {
            "success": True,
            "pdf_path": pdf_path,
            "message": "PDF downloaded successfully" + (" but markdown conversion failed" if convert_to_markdown else "")
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Download/conversion failed: {str(e)}"
        }


@mcp.tool
async def batch_convert_pdfs(
    directory: str = "articles",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert all PDFs in a directory to markdown format.

    Uses zero AI tokens - employs pymupdf4llm for direct PDF-to-markdown conversion
    without text passing through AI context. Preserves document structure and formatting.

    🔗 RESEARCH INTEGRATION:
    This tool complements search_papers() for bulk workflows:

    1. Use search_papers() to find papers and note PDF URLs
    2. Download PDFs manually or with individual calls to a directory
    3. Use batch_convert_pdfs() to convert all PDFs to markdown
    4. Organize results for analysis

    Example Research Workflow:
    # Step 1: Search and identify papers
    papers = search_papers("machine learning", limit=10)

    # Step 2: Download PDFs to directory (manual or scripted)
    # Create "research_pdfs/" directory and save PDFs there

    # Step 3: Convert all PDFs to markdown
    batch_convert_pdfs("research_pdfs/", "analysis_markdown/")

    # Alternative: Direct workflow with search_papers download limits
    # Get 3 papers at a time with automatic download
    batch1 = search_papers("ML topic A", limit=3, download_and_convert=True)
    batch2 = search_papers("ML topic B", limit=3, download_and_convert=True)
    # Then use batch_convert_pdfs if you have additional PDFs

    Args:
        directory: Directory containing PDFs (default: "articles")
                   - Supports absolute paths: "/home/user/research_papers/"
                   - Supports relative paths: "papers/", "./documents/pdfs/"
                   - If directory doesn't exist, returns error
                   - Recursively searches for PDF files (*.pdf, case-insensitive)
                   - Skips non-PDF files automatically
        output_dir: Output directory for markdown files (default: current directory)
                    - If None, saves to current working directory
                    - If provided, uses exact path: "/path/to/output/"
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

        Overall operation fails if:
        - Input directory doesn't exist
        - No PDF files found in directory
        - All individual conversions fail

    Processing Details:
        - Processes all PDF files found in the directory
        - Skips files that are already being processed
        - Creates markdown files with "{original_name}_full.md" format
        - Overwrites existing markdown files without warning
        - Continues processing remaining files if individual conversions fail
        - Provides detailed progress information for each file

    Performance:
        - Zero AI tokens consumed during conversion
        - Zero context window consumption (content saved to files, not returned)
        - Fast processing using optimized pymupdf4llm engine
        - Parallel processing not implemented (sequential conversion)
        - Memory efficient for large directories

    Example Usage:
        # Convert PDFs from default articles directory
        batch_convert_pdfs()

        # Convert from specific directory
        batch_convert_pdfs("research_papers/")

        # Convert with custom output location
        batch_convert_pdfs(
            directory="/home/user/papers/",
            output_dir="/home/user/markdown_output/"
        )

        # Check results and handle errors
        result = batch_convert_pdfs("pdfs/")
        if result["success"]:
            print(f"Converted {result['successful_conversions']} files")
            for file in result["files"]:
                if file["success"]:
                    print(f"✓ {file['input_file']} → {file['output_file']}")
                else:
                    print(f"✗ {file['input_file']}: {file.get('error', 'Unknown error')}")
    """
    try:
        utils = _lazy_import_utils()

        if not os.path.isdir(directory):
            return {
                "success": False,
                "error": f"Directory not found: {directory}"
            }

        # Find all PDF files
        pdf_files = list(Path(directory).glob('*.pdf'))
        if not pdf_files:
            return {
                "success": False,
                "error": f"No PDF files found in directory: {directory}"
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

                    save_result = utils['save_markdown_file'](result["markdown"], output_path)

                    # Clean up markdown content to avoid context window usage
                    if "markdown" in result:
                        del result["markdown"]

                    if save_result.get("success"):
                        successful += 1
                        results.append({
                            "input_file": str(pdf_file),
                            "output_file": output_path,
                            "success": True,
                            "characters": result.get("markdown_length", 0)
                        })
                    else:
                        failed += 1
                        results.append({
                            "input_file": str(pdf_file),
                            "success": False,
                            "error": save_result.get("error")
                        })
                else:
                    # Clean up markdown content even on failure
                    if "markdown" in result:
                        del result["markdown"]

                    failed += 1
                    results.append({
                        "input_file": str(pdf_file),
                        "success": False,
                        "error": result.get("error")
                    })

            except Exception as e:
                failed += 1
                results.append({
                    "input_file": str(pdf_file),
                    "success": False,
                    "error": str(e)
                })

        return {
            "success": True,
            "directory": directory,
            "output_directory": output_dir,
            "total_files": len(pdf_files),
            "successful_conversions": successful,
            "failed_conversions": failed,
            "files": results
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Batch conversion failed: {str(e)}"
        }


@mcp.tool
async def get_source_health() -> Dict[str, Any]:
    """
    Get comprehensive source health monitoring report.

    Provides detailed health metrics, performance data, and recommendations
    for all academic database sources. Includes active health checks.

    Args:
        None - This tool takes no parameters

    Returns:
        Dictionary containing:
        - health_report: Overall health status and source metrics
        - recommendations: Specific recommendations for improving source health
        - health_check_results: Results from active health checks
        - monitoring_enabled: Whether health monitoring is active

    Health Report contains:
        - overall_status: "healthy", "degraded", or "critical"
        - sources: Detailed metrics for each source including:
          - health_score: 0.0 to 1.0 health rating
          - success_rate: Percentage of successful requests
          - average_response_time: Average response time in seconds
          - consecutive_failures: Number of consecutive failures
          - last_success/failure: Timestamps of last success/failure
        - summary: Count of healthy/unhealthy/disabled sources

    Recommendations include:
        - severity: "high", "medium", or "low"
        - issue: Description of the problem
        - recommendation: Suggested action
        - action: Specific next steps

    Use Cases:
        - Monitor system health proactively
        - Identify sources with performance issues
        - Get recommendations for system improvements
        - Troubleshoot search performance problems
        - Plan maintenance and optimization

    Example Usage:
        # Get comprehensive health report
        health = get_source_health()

        # Check overall system status
        if health["health_report"]["overall_status"] == "critical":
            print("System needs immediate attention")

        # Review recommendations
        for rec in health["recommendations"]:
            if rec["severity"] == "high":
                print(f"URGENT: {rec['recommendation']}")
    """
    from paperez_mcp.utils.source_health_monitor import health_monitor

    # Perform active health check
    health_check = await health_monitor.perform_health_check()

    # Save metrics to cache for persistence
    health_monitor.save_metrics_to_cache()

    return {
        "health_report": health_monitor.get_health_report(),
        "recommendations": health_monitor.get_source_recommendations(),
        "health_check_results": health_check["health_check_results"],
        "monitoring_enabled": health_monitor.monitoring_enabled,
        "timestamp": health_check["overall_report"]["timestamp"]
    }


@mcp.tool
async def get_status() -> Dict[str, Any]:
    """
    Get system status including API health and cache statistics.

    Reports the operational status of all academic databases (CrossRef, Semantic Scholar,
    arXiv, PubMed, Google Scholar), cache usage, and configuration details.

    Args:
        None - This tool takes no parameters

    Returns:
        Dictionary containing:
        - api_status: Status of all academic database APIs
        - cache_stats: Cache usage and configuration information
        - config: System configuration details

        api_status contains:
        - crossref: Boolean indicating CrossRef API availability
        - semantic_scholar: Boolean indicating Semantic Scholar API availability
        - arxiv: Boolean indicating arXiv API availability
        - pubmed: Boolean indicating PubMed API availability
        - google_scholar: Boolean indicating Google Scholar availability

        cache_stats contains:
        - size: Number of cached entries currently stored
        - cache_dir: Directory path where cache files are stored
        - size_limit: Maximum cache size in bytes (default: 1GB)

        config contains:
        - has_semantic_scholar_key: Boolean indicating if API key is configured
        - has_scraperapi_key: Boolean indicating if scraper API key is configured
        - crossref_email: Email address used for CrossRef API requests
        - max_retries: Maximum number of retry attempts for failed requests

    Status Interpretation:
        - api_status true = API is operational and accessible
        - api_status false = API is unavailable, rate-limited, or has connectivity issues
        - cache size indicates how many search results are cached
        - Missing API keys may limit access to certain features

    Use Cases:
        - Troubleshooting API connectivity issues
        - Monitoring cache usage and performance
        - Verifying system configuration
        - Checking which databases are available for searches
        - Debugging search failures

    Example Usage:
        # Check overall system health
        status = get_status()

        # Verify specific API availability
        if status["api_status"]["crossref"]:
            print("CrossRef API is operational")

        # Monitor cache usage
        cache_size = status["cache_stats"]["size"]
        if cache_size > 1000:
            print(f"Cache has {cache_size} entries")

        # Check configuration
        config = status["config"]
        if not config["has_semantic_scholar_key"]:
            print("Consider adding Semantic Scholar API key for better performance")
    """
    return {
        "api_status": api_status.copy(),
        "cache_stats": {
            "size": len(cache),
            "cache_dir": cache.directory,
            "size_limit": cache.size_limit
        },
        "config": {
            "has_semantic_scholar_key": bool(config.semantic_scholar_api_key),
            "has_scraperapi_key": bool(config.scraperapi_key),
            "crossref_email": config.crossref_email,
            "max_retries": config.max_retries
        }
    }


def main() -> None:
    """Main entry point for the server"""
    print("🚀 Starting PaperezMCP Server...")
    print("📚 Primary tools:")
    print("  📄 get_papers: Get full papers as files (most users want this)")
    print("  📄 download_papers: Same as get_papers but more explicit")
    print("  🔍 browse_papers: Quick metadata overview (titles/abstracts only)")
    print("  👤 search_authors: Find author profiles with citation metrics")
    print("  📝 convert_pdf_to_text: Convert PDF to plain text files")
    print("  🔄 convert_pdf_to_markdown: Convert PDF to markdown format")
    print("  📁 batch_convert_pdfs: Convert multiple PDFs in a directory")
    print("  🔧 get_status: Check system health and API status")
    print("")
    print("🎯 QUICK START: Use get_papers('topic') to download full papers!")
    print("   Only use browse_papers() if you just want to explore titles/abstracts.")
    print("")
    print("🔗 PaperezMCP ready at: stdio")
    mcp.run()


if __name__ == "__main__":
    main()
