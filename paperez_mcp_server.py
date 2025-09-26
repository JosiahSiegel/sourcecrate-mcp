#!/usr/bin/env python3
"""
PaperezMCP - Academic Paper Research Made Easy

A comprehensive academic research server with multi-source fallback,
robust caching, and graceful error handling. Built with modular architecture.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import tempfile
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
def _ensure_scholarly_setup():
    """Lazy initialization of scholarly proxy setup"""
    global _scholarly_setup_done
    if not _scholarly_setup_done:
        from paperez_mcp.api_clients import setup_scholarly_proxy
        setup_scholarly_proxy()
        _scholarly_setup_done = True

def _ensure_pymupdf4llm():
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

def _lazy_import_search_functions():
    """Lazy import of search API functions"""
    from paperez_mcp.api_clients import (
        search_crossref,
        search_semantic_scholar,
        search_arxiv,
        search_pubmed,
        search_google_scholar_fallback
    )
    return {
        'crossref': search_crossref,
        'semantic_scholar': search_semantic_scholar,
        'arxiv': search_arxiv,
        'pubmed': search_pubmed,
        'google_scholar': search_google_scholar_fallback
    }

def _lazy_import_utils():
    """Lazy import of utility functions"""
    from paperez_mcp.utils import (
        extract_pdf_text,
        convert_pdf_to_markdown_content,
        comprehensive_search_internal,
        download_pdf,
        save_markdown_file
    )
    from paperez_mcp.utils.pdf_processor import extract_pdf_text_from_local_file
    return {
        'extract_pdf_text': extract_pdf_text,
        'convert_pdf_to_markdown_content': convert_pdf_to_markdown_content,
        'comprehensive_search_internal': comprehensive_search_internal,
        'download_pdf': download_pdf,
        'save_markdown_file': save_markdown_file,
        'extract_pdf_text_from_local_file': extract_pdf_text_from_local_file
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

3. extract_pdf_text - Local PDF text extraction
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
    limit: int = 10
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

    🔄 MULTI-STEP PROCESSES:

    ## Research Workflow (Explore → Select → Download):
    Step 1: search_papers("broad topic", limit=20)  # Get overview
    Step 2: Review abstracts and select interesting papers
    Step 3: For selected papers with PDF URLs:
            convert_pdf_to_markdown(pdf_url, output_path="papers/paper_N.md")

    ## Bulk Download Workflow (>3 papers):
    Option A - Multiple Targeted Searches:
      papers1 = search_papers("ML transformers", limit=3, download_and_convert=True)
      papers2 = search_papers("ML attention", limit=3, download_and_convert=True)
      papers3 = search_papers("ML BERT", limit=3, download_and_convert=True)

    Option B - Search Then Individual Download:
      metadata = search_papers("machine learning", limit=10)
      for paper in metadata[0]["results"]:
          if paper.get("pdf_url"):
              convert_pdf_to_markdown(paper["pdf_url"],
                                    output_path=f"papers/{paper['title']}.md")

    ## Content Analysis Workflow:
    Step 1: search_papers("topic", limit=5, include_full_text=True)  # Text in memory
    Step 2: Analyze text content programmatically
    Step 3: Optionally download promising papers as files

    Args:
        query: Search query (keywords, DOI with "doi:" prefix, title, or author)
               - Keywords: "machine learning transformers", "neural networks"
               - DOI format: "doi:10.1000/xyz123" (must include "doi:" prefix)
               - Author search: "Geoffrey Hinton", "Yoshua Bengio"
               - Title search: "Attention Is All You Need"
        limit: Maximum number of results to return (default: 5, max recommended: 10)
        include_full_text: 🚨 CRITICAL PARAMETER FOR FULL TEXT 🚨
                          - False (default): Returns only metadata/abstracts ❌
                          - True: Extracts full text content into memory ✅
                          ⚠️ WARNING: Slow for multiple papers, text stays in memory only
                          📁 For files on disk, use download_and_convert=True instead
        download_and_convert: 🚨 CRITICAL PARAMETER FOR SAVING FILES 🚨
                             - False (default): No files saved, metadata only ❌
                             - True: Downloads PDFs and saves as markdown files ✅
                             🚨 LIMITATION: Only processes top 3 papers to avoid overload
                             📁 Files saved to current directory by default
                             🔄 For >3 papers, use multiple calls or individual conversion

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

    # Get metadata only - no downloads
    result = await utils['comprehensive_search_internal'](query, limit, include_full_text=False)
    return [result]


@mcp.tool
async def download_papers(
    query: str,
    limit: int = 5,
    output_dir: str = "papers"
) -> List[Dict[str, Any]]:
    """
    📄 GET FULL PAPERS: Download academic papers as markdown files

    This function is designed for when you want to actually GET papers, not just search for them.
    It automatically downloads PDFs and converts them to markdown files.

    Use this when:
    - User says "get papers", "download papers", "save papers"
    - You want actual paper content as files
    - Need papers for analysis, reading, or citation

    Args:
        query: Search query (keywords, DOI, title, or author)
        limit: Maximum papers to download (default: 5, recommended: 5-10)
        output_dir: Directory to save markdown files (default: "papers")

    Returns:
        List containing single dict with:
        - results: List of paper objects with local file paths
        - total_found: Number of papers found
        - downloaded_count: Number successfully downloaded
        - output_directory: Where files were saved

    Example Usage:
        # Get 3 papers on machine learning
        download_papers("machine learning transformers", limit=3)

        # Save to specific directory
        download_papers("climate change", limit=5, output_dir="climate_papers")
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Lazy import utilities
    _ensure_scholarly_setup()
    utils = _lazy_import_utils()

    # Search for papers with download enabled
    result = await utils['comprehensive_search_internal'](query, limit, include_full_text=False)

    downloaded_count = 0

    # Download and convert papers
    if result.get("results"):
        for paper in result["results"][:limit]:
            pdf_url = paper.get("pdf_url") or paper.get("open_access_pdf")
            if pdf_url:
                try:
                    # Generate safe filename
                    title = paper.get("title", "paper")[:50]
                    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    output_path = Path(output_dir) / f"{safe_title}.md"

                    # Download PDF
                    pdf_content = await utils['download_pdf'](pdf_url)
                    if pdf_content:
                        # Convert to markdown
                        markdown_content = await utils['convert_pdf_to_markdown_content'](pdf_content, paper.get("title", ""))
                        if markdown_content:
                            # Save markdown file
                            success = await utils['save_markdown_file'](str(output_path), markdown_content)
                            if success:
                                paper["local_markdown"] = str(output_path)
                                paper["markdown_characters"] = len(markdown_content)
                                downloaded_count += 1
                except Exception as e:
                    paper["download_error"] = str(e)

    # Add download metadata
    result["downloaded_count"] = downloaded_count
    result["output_directory"] = output_dir

    return [result]


@mcp.tool
async def get_papers(
    query: str,
    limit: int = 5,
    output_dir: str = "papers"
) -> List[Dict[str, Any]]:
    """
    📄 GET FULL PAPERS: Alias for download_papers()

    This is an alias for download_papers() that matches natural language.
    When users say "get papers", they typically want the actual papers, not metadata.

    Use this when:
    - User says "get papers on [topic]"
    - User wants actual content, not just summaries
    - Need papers for research or analysis

    Args:
        query: Search query (keywords, DOI, title, or author)
        limit: Maximum papers to get (default: 5, recommended: 5-10)
        output_dir: Directory to save papers (default: "papers")

    Returns:
        Same as download_papers() - papers saved as markdown files

    Example Usage:
        # Get papers on a topic
        get_papers("neural networks", limit=5)

        # Get papers to specific folder
        get_papers("quantum computing", output_dir="quantum_research")
    """
    return await download_papers(query, limit, output_dir)


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
            def _search_author():
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
async def extract_pdf_text(file_path: str) -> Dict[str, Any]:
    """
    Extract text from a local PDF file.

    Uses PyMuPDF for robust text extraction with unlimited character support.
    Handles academic papers, preprints, and complex document layouts.

    Args:
        file_path: Path to local PDF file
                   - Supports absolute paths: "/home/user/papers/paper.pdf"
                   - Supports relative paths: "papers/paper.pdf", "./documents/research.pdf"
                   - Must be a valid PDF file (will return error for non-PDF files)
                   - File must exist and be readable

    Returns:
        Dictionary containing:
        - success: Boolean indicating if extraction succeeded
        - text: Full extracted text content from all pages
        - num_pages: Total number of pages in the PDF
        - file_size: Size of the PDF file in bytes
        - text_length: Character count of extracted text
        - extraction_method: Method used ("PyMuPDF Local")
        - file_path: Original file path provided

        On success, text field contains:
        - All text content with page separators
        - Preserved formatting where possible
        - Special characters and Unicode support
        - Academic symbols and mathematical notation

        On failure, includes:
        - success: false
        - error: Error message explaining the failure
        - text: Empty string

    Capabilities:
        - Handles complex academic layouts (multi-column, figures, tables)
        - Extracts text from scanned PDFs (if they contain text layers)
        - Supports Unicode and special characters
        - Unlimited character extraction (no truncation)
        - Fast processing using optimized PyMuPDF engine

    Limitations:
        - Cannot extract text from image-only PDFs without OCR
        - May have issues with heavily formatted or corrupted PDFs
        - Does not extract images, only text content
        - Password-protected PDFs are not supported

    Example Usage:
        # Extract from local file
        extract_pdf_text("/path/to/research_paper.pdf")

        # Extract from relative path
        extract_pdf_text("./documents/paper.pdf")

        # Check success before using text
        result = extract_pdf_text("paper.pdf")
        if result["success"]:
            text = result["text"]
            pages = result["num_pages"]
    """
    utils = _lazy_import_utils()
    return utils['extract_pdf_text_from_local_file'](file_path)


async def _convert_pdf_to_markdown_internal(file_path: str, title: str = "", authors: list = None, output_path: Optional[str] = None) -> Dict[str, Any]:
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
            # Default to current directory with same name as PDF
            filename = Path(file_path).stem + "_full.md"
            markdown_path = os.path.join(os.getcwd(), filename)

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(markdown_path), exist_ok=True)

        save_result = save_markdown_file(result["markdown"], markdown_path)
        if save_result.get("success"):
            result["markdown_path"] = markdown_path

    return result


@mcp.tool
async def convert_pdf_to_markdown(
    file_path: str,
    title: str = "",
    authors: list = None,
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
        - markdown: Full markdown content (only if success=True)
        - markdown_length: Character count of markdown content
        - original_file: Original PDF file path
        - pages_extracted: Number of pages processed
        - text_length: Character count of original text
        - markdown_path: Path to saved markdown file (if save succeeded)

        On success, markdown contains:
        - Structured content with preserved headings
        - Formatted tables and lists
        - Mathematical notation and special characters
        - Document metadata (title, authors, page count, etc.)
        - Page-by-page content with clear separators

        On failure, includes:
        - success: false
        - error: Error message explaining the failure
        - markdown: Empty string

    Features:
        - Zero AI tokens used (direct PDF→markdown conversion)
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
    return await _convert_pdf_to_markdown_internal(file_path, title, authors, output_path)




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
        if output_dir is None:
            output_dir = os.getcwd()

        # Download PDF
        download_result = await download_pdf(pdf_url, output_dir)

        if not download_result.get("success"):
            return download_result

        pdf_path = download_result["pdf_path"]

        # Convert to markdown if requested
        if convert_to_markdown:
            if PYMUPDF4LLM_AVAILABLE:
                # Use pymupdf4llm directly (zero tokens)
                try:
                    markdown_content = pymupdf4llm.to_markdown(pdf_path)

                    # Save markdown
                    markdown_path = pdf_path.replace('.pdf', '.md')
                    save_result = save_markdown_file(markdown_content, markdown_path)

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

                    save_result = save_markdown_file(result["markdown"], output_path)
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


def main():
    """Main entry point for the server"""
    print("🚀 Starting PaperezMCP Server...")
    print("📚 Primary tools:")
    print("  📄 get_papers: Get full papers as files (most users want this)")
    print("  📄 download_papers: Same as get_papers but more explicit")
    print("  🔍 browse_papers: Quick metadata overview (titles/abstracts only)")
    print("  👤 search_authors: Find author profiles with citation metrics")
    print("  📝 extract_pdf_text: Extract text from local PDF files")
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