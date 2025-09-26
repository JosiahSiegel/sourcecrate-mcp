#!/usr/bin/env python3
"""
Enhanced Scholarly MCP Server

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

try:
    import pymupdf4llm
    PYMUPDF4LLM_AVAILABLE = True
except ImportError:
    PYMUPDF4LLM_AVAILABLE = False

from fastmcp import FastMCP

# Import modular components
from scholarly_mcp.config import config, api_status, cache
from scholarly_mcp.api_clients import (
    search_crossref,
    search_semantic_scholar,
    search_arxiv,
    search_pubmed,
    search_google_scholar_fallback,
    setup_scholarly_proxy
)
from scholarly_mcp.utils import (
    extract_pdf_text,
    convert_pdf_to_markdown_content,
    comprehensive_search_internal,
    download_pdf,
    save_markdown_file
)
from scholarly_mcp.utils.pdf_processor import extract_pdf_text_from_local_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Enhanced Scholarly MCP Server - Modular Version")

# Setup scholarly proxy on startup
setup_scholarly_proxy()

"""
OPTIMIZED MCP TOOLS - 6 Essential Functions

This modular server provides 6 optimized MCP tools for academic research:

1. search_papers - Comprehensive search across 5 academic databases
   - Multi-source search (CrossRef, Semantic Scholar, arXiv, PubMed, Google Scholar)
   - Optional full-text extraction and PDF download/conversion
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
async def search_papers(
    query: str,
    limit: int = 5,
    include_full_text: bool = False,
    download_and_convert: bool = False
) -> List[Dict[str, Any]]:
    """
    Search academic papers across multiple databases with optional full-text extraction and download.

    Searches CrossRef, Semantic Scholar, arXiv, PubMed, and Google Scholar with intelligent fallback.
    Supports DOI queries (use "doi:10.1000/xyz"), author queries, and keyword searches.

    Args:
        query: Search query (keywords, DOI with "doi:" prefix, title, or author)
        limit: Maximum number of results to return (default: 5)
        include_full_text: Extract full text from PDFs when available (default: False)
        download_and_convert: Download PDFs and convert to markdown (default: False)

    Returns:
        List of papers with metadata, optional full text, and optional local files
    """
    result = await comprehensive_search_internal(query, limit, include_full_text)

    # Optionally download and convert papers
    if download_and_convert and result.get("results"):
        for paper in result["results"][:3]:  # Limit to top 3 papers
            pdf_url = paper.get("pdf_url") or paper.get("open_access_pdf")
            if pdf_url:
                try:
                    download_result = await download_and_convert_paper(pdf_url)
                    if download_result.get("success"):
                        paper["local_pdf"] = download_result.get("pdf_path")
                        paper["local_markdown"] = download_result.get("markdown_path")
                        paper["markdown_characters"] = download_result.get("markdown_characters", 0)
                except Exception as e:
                    paper["download_error"] = str(e)

    return [result]




@mcp.tool
async def search_authors(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for academic authors by name.

    Returns author profiles with affiliation, research interests, citation metrics,
    and publication indices from Google Scholar.

    Args:
        name: Author name to search for
        limit: Maximum number of authors to return (default: 5)

    Returns:
        List of author profiles with citation count, h-index, and i10-index
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

    Returns:
        Dictionary with extracted text, character count, and extraction metadata
    """
    return extract_pdf_text_from_local_file(file_path)


async def _convert_pdf_to_markdown_internal(file_path: str, title: str = "", authors: list = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Internal function to convert a local PDF file to formatted markdown.
    Duplicates PDF extraction logic to avoid MCP tool calling MCP tool.
    """
    result = convert_pdf_to_markdown_content(file_path, title, authors)

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
        title: Optional title for the document header
        authors: Optional list of authors for the document header
        output_path: Output path for markdown file (default: current directory)

    Returns:
        Dictionary with conversion results and output file path
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

    Args:
        directory: Directory containing PDFs (default: current directory/articles/)
        output_dir: Output directory for markdown files (default: current directory)

    Returns:
        Dictionary with batch conversion results and per-file status
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

    Returns:
        Dictionary with API status, cache stats, and configuration info
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
    mcp.run()


if __name__ == "__main__":
    main()