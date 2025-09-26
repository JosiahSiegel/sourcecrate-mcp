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


@mcp.tool
async def comprehensive_search(
    query: str,
    limit: int = 5,
    include_full_text: bool = False,
    download_and_convert: bool = False
) -> List[Dict[str, Any]]:
    """
    Comprehensive search across multiple academic databases with fallback support.

    Args:
        query: Search query for publications
        limit: Maximum number of results to return (default: 5)
        include_full_text: Whether to attempt full text extraction (default: False)
        download_and_convert: Whether to download and convert papers to markdown (default: False)

    Returns:
        List of papers with metadata from multiple sources
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
async def search_publications(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for publications by keywords or title"""
    result = await comprehensive_search_internal(query, limit, include_full_text=False)
    return result.get("results", [])


@mcp.tool
async def search_author(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search for authors by name"""
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
async def get_full_text_by_doi(
    doi: str,
    extract_text: bool = True,
    download_as_markdown: bool = False
) -> Dict[str, Any]:
    """
    Get full text of a paper using its DOI.

    Args:
        doi: DOI of the paper
        extract_text: Whether to extract text from PDF (default: True)
        download_as_markdown: Whether to download and convert to markdown (default: False)

    Returns:
        Dictionary with paper metadata and full text if available
    """
    # Search for the paper by DOI
    query = f"doi:{doi}"
    results = await search_crossref(query, 1)

    if results:
        paper = results[0]
        pdf_url = f"https://sci-hub.se/{doi}"  # Try sci-hub as fallback

        if paper.get("url"):
            try:
                # Download and convert to markdown if requested
                if download_as_markdown:
                    download_result = await download_and_convert_paper(pdf_url)
                    if download_result.get("success"):
                        paper["local_pdf"] = download_result.get("pdf_path")
                        paper["local_markdown"] = download_result.get("markdown_path")
                        paper["markdown_characters"] = download_result.get("markdown_characters", 0)

                # Extract text if requested
                if extract_text:
                    text_result = await extract_pdf_text(pdf_url)
                    if text_result.get("success"):
                        paper["full_text"] = text_result["text"]
                        paper["text_length"] = len(text_result["text"])
                        paper["extraction_method"] = text_result["extraction_method"]

            except Exception as e:
                paper["extraction_error"] = str(e)

        return paper

    return {"error": f"Paper with DOI {doi} not found"}


@mcp.tool
async def get_full_text_by_title(title: str, extract_text: bool = True) -> Dict[str, Any]:
    """
    Get full text of a paper using its title.

    Args:
        title: Title of the paper
        extract_text: Whether to extract text from PDF (default: True)

    Returns:
        Dictionary with paper metadata and full text if available
    """
    # Search for the exact title
    result = await comprehensive_search_internal(title, 1, include_full_text=extract_text)

    if result.get("results"):
        return result["results"][0]

    return {"error": f"Paper with title '{title}' not found"}


@mcp.tool
async def find_open_access_versions(title: str, doi: str = "") -> Dict[str, Any]:
    """
    Find open access versions of a paper using multiple sources.

    Args:
        title: Title of the paper
        doi: DOI of the paper (optional)

    Returns:
        Dictionary with open access information from multiple sources
    """
    # Use comprehensive search to find open access versions
    result = await comprehensive_search_internal(title, 3)

    open_access_sources = []
    for paper in result.get("results", []):
        if paper.get("open_access_pdf") or paper.get("pdf_url"):
            open_access_sources.append({
                "source": paper.get("source"),
                "pdf_url": paper.get("open_access_pdf") or paper.get("pdf_url"),
                "title": paper.get("title"),
                "doi": paper.get("doi", "")
            })

    return {
        "title": title,
        "doi": doi,
        "open_access_sources": open_access_sources,
        "total_sources": len(open_access_sources)
    }


@mcp.tool
async def extract_pdf_text_from_url(pdf_url: str) -> Dict[str, Any]:
    """
    Extract text from a PDF URL.

    Args:
        pdf_url: Direct URL to a PDF file

    Returns:
        Dictionary with extracted text and metadata
    """
    result = await extract_pdf_text(pdf_url)
    return result


@mcp.tool
async def extract_pdf_text_from_local_file_mcp(file_path: str) -> Dict[str, Any]:
    """
    Extract text from a local PDF file.

    Args:
        file_path: Path to local PDF file

    Returns:
        Dictionary with extracted text and metadata
    """
    return extract_pdf_text_from_local_file(file_path)


async def _convert_pdf_to_markdown_internal(file_path: str, title: str = "", authors: list = None) -> Dict[str, Any]:
    """
    Internal function to convert a local PDF file to formatted markdown.
    Duplicates PDF extraction logic to avoid MCP tool calling MCP tool.
    """
    result = convert_pdf_to_markdown_content(file_path, title, authors)

    if result.get("success"):
        # Save to file
        output_dir = os.path.dirname(file_path) + "/../articles_markdown"
        os.makedirs(output_dir, exist_ok=True)

        filename = Path(file_path).stem + "_full.md"
        markdown_path = os.path.join(output_dir, filename)

        save_result = save_markdown_file(result["markdown"], markdown_path)
        if save_result.get("success"):
            result["markdown_path"] = markdown_path

    return result


@mcp.tool
async def convert_pdf_to_markdown(file_path: str, title: str = "", authors: list = None) -> Dict[str, Any]:
    """Convert a local PDF file to formatted markdown."""
    return await _convert_pdf_to_markdown_internal(file_path, title, authors)


@mcp.tool
async def search_with_full_text(query: str, limit: int = 3, extract_text: bool = False) -> List[Dict[str, Any]]:
    """
    Search for papers and attempt to retrieve full text for each result.

    Args:
        query: Search query for publications
        limit: Maximum number of results to return (default: 3)
        extract_text: Whether to extract full text from PDFs (default: False, can be slow)

    Returns:
        List of papers with metadata and full text when available
    """
    result = await comprehensive_search_internal(query, limit, include_full_text=extract_text)
    return result.get("results", [])


@mcp.tool
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
        output_dir: Optional output directory (default: downloaded_papers/)

    Returns:
        Dictionary with download and conversion results
    """
    try:
        if output_dir is None:
            output_dir = "downloaded_papers"

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
async def batch_convert_local_pdfs(
    directory: str = "articles",
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert all PDFs in a directory to markdown using zero AI tokens.

    This function calls an external converter script that uses pymupdf4llm
    to convert PDFs directly to markdown without any text passing through
    the AI context.

    Args:
        directory: Directory containing PDFs (default: articles/)
        output_dir: Optional output directory for markdown files

    Returns:
        Dictionary with batch conversion results
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
            output_dir = directory + "_markdown"

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
async def get_api_status() -> Dict[str, Any]:
    """Get the current status of all APIs and cache statistics."""
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