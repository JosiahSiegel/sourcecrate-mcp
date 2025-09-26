#!/usr/bin/env python3
"""
Enhanced Scholarly MCP Server with Full-Text Retrieval Capabilities

This server extends the basic scholarly functionality with comprehensive
full-text retrieval from multiple open access sources.
"""

from fastmcp import FastMCP
from scholarly import scholarly
import asyncio
import aiohttp
import httpx
import fitz  # PyMuPDF
import requests
import re
import time
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlparse, urljoin
import json
import logging
from dataclasses import dataclass
from pathlib import Path
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the FastMCP server
mcp = FastMCP("Enhanced Scholarly MCP Server with Full-Text Retrieval")

# Rate limiting and caching
RATE_LIMIT_DELAY = 1.0  # seconds between API calls
last_api_call = {}

@dataclass
class FullTextResult:
    """Container for full-text retrieval results"""
    title: str
    authors: List[str]
    doi: str
    abstract: str
    full_text: Optional[str]
    source: str
    open_access_url: Optional[str]
    metadata: Dict[str, Any]
    extraction_method: str
    error: Optional[str] = None

def rate_limit(api_name: str):
    """Simple rate limiting function"""
    global last_api_call
    if api_name in last_api_call:
        elapsed = time.time() - last_api_call[api_name]
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
    last_api_call[api_name] = time.time()

async def check_unpaywall(doi: str, email: str = "research@example.com") -> Dict[str, Any]:
    """Check Unpaywall for open access version of a DOI"""
    rate_limit("unpaywall")

    if not doi:
        return {"is_oa": False, "error": "No DOI provided"}

    # Clean DOI
    doi = doi.replace("https://doi.org/", "").replace("http://dx.doi.org/", "")

    url = f"https://api.unpaywall.org/v2/{doi}?email={email}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                return {"is_oa": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"is_oa": False, "error": str(e)}

async def search_core_api(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search CORE API for open access papers"""
    rate_limit("core")

    # Note: CORE API requires registration for API key
    # This is a placeholder implementation
    url = "https://api.core.ac.uk/v3/search/works"

    try:
        # This would require a valid API key
        headers = {
            "Authorization": "Bearer YOUR_CORE_API_KEY",
            "Content-Type": "application/json"
        }

        params = {
            "q": query,
            "limit": limit,
            "offset": 0
        }

        # For now, return placeholder response
        return {
            "results": [],
            "error": "CORE API requires registration and API key"
        }

    except Exception as e:
        return {"results": [], "error": str(e)}

async def search_semantic_scholar(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search Semantic Scholar API"""
    rate_limit("semantic_scholar")

    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": query,
        "limit": limit,
        "fields": "paperId,title,authors,year,abstract,venue,citationCount,url,openAccessPdf"
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                return {"data": [], "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"data": [], "error": str(e)}

async def get_arxiv_paper(arxiv_id: str) -> Dict[str, Any]:
    """Get paper from arXiv API"""
    rate_limit("arxiv")

    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                # Parse XML response (simplified)
                content = response.text
                # Extract PDF link
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                return {
                    "title": "arXiv Paper",  # Would parse from XML
                    "pdf_url": pdf_url,
                    "source": "arXiv"
                }
            else:
                return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        full_text = ""

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            full_text += f"\n--- Page {page_num + 1} ---\n{text}\n"

        doc.close()

        return {
            "text": full_text,
            "num_pages": len(doc),
            "extraction_method": "PyMuPDF"
        }
    except Exception as e:
        return {"error": str(e), "extraction_method": "PyMuPDF"}

async def download_and_extract_pdf(pdf_url: str) -> Dict[str, Any]:
    """Download PDF and extract text"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(pdf_url)

            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name

                # Extract text
                result = extract_text_from_pdf(tmp_path)

                # Clean up
                os.unlink(tmp_path)

                return result
            else:
                return {"error": f"Failed to download PDF: HTTP {response.status_code}"}

    except Exception as e:
        return {"error": f"PDF download/extraction failed: {str(e)}"}

@mcp.tool
def search_author(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for authors by name on Google Scholar.

    Args:
        name: The author's name to search for
        limit: Maximum number of results to return (default: 5)

    Returns:
        List of author information dictionaries
    """
    try:
        search_query = scholarly.search_author(name)
        results = []

        for i, author in enumerate(search_query):
            if i >= limit:
                break
            results.append({
                'name': author.get('name', ''),
                'affiliation': author.get('affiliation', ''),
                'scholar_id': author.get('scholar_id', ''),
                'citedby': author.get('citedby', 0),
                'interests': author.get('interests', []),
                'email_domain': author.get('email_domain', ''),
                'url_picture': author.get('url_picture', '')
            })

        return results
    except Exception as e:
        return [{"error": f"Failed to search for author: {str(e)}"}]

@mcp.tool
def search_publications(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for publications by keywords or title.

    Args:
        query: Search query for publications
        limit: Maximum number of results to return (default: 5)

    Returns:
        List of publication information dictionaries
    """
    try:
        search_query = scholarly.search_pubs(query)
        results = []

        for i, pub in enumerate(search_query):
            if i >= limit:
                break

            bib = pub.get('bib', {})
            results.append({
                'title': bib.get('title', ''),
                'author': bib.get('author', []),
                'venue': bib.get('venue', ''),
                'year': bib.get('pub_year', ''),
                'abstract': bib.get('abstract', ''),
                'num_citations': pub.get('num_citations', 0),
                'pub_url': pub.get('pub_url', ''),
                'eprint_url': pub.get('eprint_url', ''),
                'author_id': pub.get('author_id', [])
            })

        return results
    except Exception as e:
        return [{"error": f"Failed to search for publications: {str(e)}"}]

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
    results = {
        "title": title,
        "doi": doi,
        "open_access_sources": [],
        "errors": []
    }

    # Check Unpaywall if DOI is available
    if doi:
        unpaywall_result = await check_unpaywall(doi)
        if unpaywall_result.get("is_oa"):
            results["open_access_sources"].append({
                "source": "Unpaywall",
                "url": unpaywall_result.get("best_oa_location", {}).get("url_for_pdf"),
                "host_type": unpaywall_result.get("best_oa_location", {}).get("host_type"),
                "license": unpaywall_result.get("best_oa_location", {}).get("license")
            })
        elif unpaywall_result.get("error"):
            results["errors"].append(f"Unpaywall: {unpaywall_result['error']}")

    # Check Semantic Scholar
    semantic_result = await search_semantic_scholar(title, limit=1)
    if semantic_result.get("data"):
        for paper in semantic_result["data"]:
            if paper.get("openAccessPdf"):
                results["open_access_sources"].append({
                    "source": "Semantic Scholar",
                    "url": paper["openAccessPdf"].get("url"),
                    "status": paper["openAccessPdf"].get("status")
                })
    elif semantic_result.get("error"):
        results["errors"].append(f"Semantic Scholar: {semantic_result['error']}")

    # Check if it's an arXiv paper
    arxiv_pattern = r'arXiv:(\d+\.\d+)'
    arxiv_match = re.search(arxiv_pattern, title + " " + str(doi))
    if arxiv_match:
        arxiv_id = arxiv_match.group(1)
        arxiv_result = await get_arxiv_paper(arxiv_id)
        if arxiv_result.get("pdf_url"):
            results["open_access_sources"].append({
                "source": "arXiv",
                "url": arxiv_result["pdf_url"],
                "type": "preprint"
            })

    return results

@mcp.tool
async def get_full_text_by_doi(doi: str, extract_text: bool = True) -> Dict[str, Any]:
    """
    Get full text of a paper using its DOI.

    Args:
        doi: DOI of the paper
        extract_text: Whether to extract text from PDF (default: True)

    Returns:
        Dictionary with paper metadata and full text if available
    """
    if not doi:
        return {"error": "No DOI provided"}

    # Get open access versions
    oa_result = await find_open_access_versions("", doi)

    if not oa_result["open_access_sources"]:
        return {
            "doi": doi,
            "full_text": None,
            "error": "No open access version found",
            "checked_sources": ["Unpaywall", "Semantic Scholar", "arXiv"]
        }

    # Try to extract text from the first available PDF
    for source in oa_result["open_access_sources"]:
        pdf_url = source.get("url")
        if pdf_url and extract_text:
            logger.info(f"Attempting to extract text from {pdf_url}")
            extraction_result = await download_and_extract_pdf(pdf_url)

            if extraction_result.get("text"):
                return {
                    "doi": doi,
                    "full_text": extraction_result["text"],
                    "source": source["source"],
                    "pdf_url": pdf_url,
                    "extraction_method": extraction_result.get("extraction_method"),
                    "num_pages": extraction_result.get("num_pages"),
                    "error": None
                }
            else:
                logger.warning(f"Failed to extract text: {extraction_result.get('error')}")

    # Return available URLs even if extraction failed
    return {
        "doi": doi,
        "full_text": None,
        "open_access_sources": oa_result["open_access_sources"],
        "error": "PDF text extraction failed, but open access URLs available"
    }

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
    # First, search for the paper to get DOI
    scholarly_results = search_publications(title, limit=1)

    if not scholarly_results or scholarly_results[0].get("error"):
        return {"error": "Paper not found in Google Scholar"}

    paper = scholarly_results[0]

    # Extract DOI from URLs if available
    doi = ""
    for url in [paper.get("pub_url"), paper.get("eprint_url")]:
        if url and "doi.org" in url:
            doi = url.split("doi.org/")[-1]
            break

    # Get open access versions
    oa_result = await find_open_access_versions(title, doi)

    result = {
        "title": title,
        "authors": paper.get("author", []),
        "venue": paper.get("venue", ""),
        "year": paper.get("year", ""),
        "abstract": paper.get("abstract", ""),
        "doi": doi,
        "citations": paper.get("num_citations", 0)
    }

    if not oa_result["open_access_sources"]:
        result.update({
            "full_text": None,
            "error": "No open access version found"
        })
        return result

    # Try to extract text from the first available PDF
    if extract_text:
        for source in oa_result["open_access_sources"]:
            pdf_url = source.get("url")
            if pdf_url:
                extraction_result = await download_and_extract_pdf(pdf_url)

                if extraction_result.get("text"):
                    result.update({
                        "full_text": extraction_result["text"],
                        "source": source["source"],
                        "pdf_url": pdf_url,
                        "extraction_method": extraction_result.get("extraction_method"),
                        "num_pages": extraction_result.get("num_pages")
                    })
                    return result

    # Return metadata with available URLs
    result.update({
        "full_text": None,
        "open_access_sources": oa_result["open_access_sources"],
        "error": "PDF text extraction failed, but open access URLs available"
    })

    return result

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
    # Get initial search results
    papers = search_publications(query, limit)

    if not papers or papers[0].get("error"):
        return papers

    enhanced_results = []

    for paper in papers:
        title = paper.get("title", "")
        if not title:
            enhanced_results.append(paper)
            continue

        # Try to get full text
        try:
            full_text_result = await get_full_text_by_title(title, extract_text)

            # Merge the results
            enhanced_paper = {**paper}
            if full_text_result.get("full_text"):
                enhanced_paper["full_text"] = full_text_result["full_text"]
                enhanced_paper["full_text_source"] = full_text_result.get("source")
                enhanced_paper["extraction_method"] = full_text_result.get("extraction_method")
            elif full_text_result.get("open_access_sources"):
                enhanced_paper["open_access_urls"] = [
                    source.get("url") for source in full_text_result["open_access_sources"]
                    if source.get("url")
                ]

            enhanced_results.append(enhanced_paper)

        except Exception as e:
            paper["full_text_error"] = str(e)
            enhanced_results.append(paper)

    return enhanced_results

@mcp.tool
def extract_pdf_text_from_url(pdf_url: str) -> Dict[str, Any]:
    """
    Extract text from a PDF URL.

    Args:
        pdf_url: Direct URL to a PDF file

    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        # Download and extract in synchronous context
        response = requests.get(pdf_url, timeout=60)

        if response.status_code == 200:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            # Extract text
            result = extract_text_from_pdf(tmp_path)

            # Clean up
            os.unlink(tmp_path)

            result["pdf_url"] = pdf_url
            return result
        else:
            return {"error": f"Failed to download PDF: HTTP {response.status_code}"}

    except Exception as e:
        return {"error": f"PDF extraction failed: {str(e)}"}

# Run the server
if __name__ == "__main__":
    mcp.run()