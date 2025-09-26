#!/usr/bin/env python3
"""
Enhanced Scholarly MCP Server with Full-Text Retrieval Capabilities

This server extends the basic scholarly functionality with comprehensive
full-text retrieval from multiple open access sources.
"""

from fastmcp import FastMCP
from scholarly import scholarly, ProxyGenerator
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
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from fake_useragent import UserAgent
import arxiv
import semanticscholar as sch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration management
@dataclass
class APIConfig:
    """Configuration for API keys and settings"""
    semantic_scholar_api_key: Optional[str] = None
    scraperapi_key: Optional[str] = None
    core_api_key: Optional[str] = None
    use_free_proxies: bool = True
    enable_proxy_rotation: bool = True
    max_retries: int = 3
    base_delay: float = 1.0

# Global configuration instance
config = APIConfig()

# Initialize scholarly with proxy support
def setup_scholarly_proxy():
    """Initialize scholarly with appropriate proxy configuration"""
    try:
        if config.scraperapi_key:
            pg = ProxyGenerator()
            pg.ScraperAPI(config.scraperapi_key)
            scholarly.use_proxy(pg)
            logger.info("Scholarly configured with ScraperAPI proxy")
        elif config.use_free_proxies:
            pg = ProxyGenerator()
            pg.FreeProxies()
            scholarly.use_proxy(pg)
            logger.info("Scholarly configured with free proxies")

        # Update fake-useragent for better compatibility
        from fake_useragent import UserAgent
        ua = UserAgent()
        logger.info("User agent updated for better compatibility")

    except Exception as e:
        logger.warning(f"Failed to setup proxy: {e}. Continuing without proxy.")

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

# Enhanced retry decorators
def scholarly_retry():
    """Retry decorator for Google Scholar operations"""
    return retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(multiplier=config.base_delay, min=1, max=30),
        retry=retry_if_exception_type((Exception,)),
        reraise=True
    )

def api_retry():
    """Retry decorator for external API calls"""
    return retry(
        stop=stop_after_attempt(config.max_retries),
        wait=wait_exponential(multiplier=config.base_delay, min=1, max=10),
        retry=retry_if_exception_type((httpx.HTTPStatusError, aiohttp.ClientError, requests.RequestException)),
        reraise=True
    )

async def rate_limit_async(api_name: str):
    """Async rate limiting function"""
    global last_api_call
    if api_name in last_api_call:
        elapsed = time.time() - last_api_call[api_name]
        if elapsed < RATE_LIMIT_DELAY:
            await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)
    last_api_call[api_name] = time.time()

def rate_limit(api_name: str):
    """Simple rate limiting function for sync operations"""
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

@api_retry()
async def search_semantic_scholar(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search Semantic Scholar API with enhanced error handling"""
    await rate_limit_async("semantic_scholar")

    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": "paperId,title,authors,year,abstract,venue,citationCount,url,openAccessPdf"
    }

    headers = {}
    if config.semantic_scholar_api_key:
        headers["x-api-key"] = config.semantic_scholar_api_key

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limit hit - the retry decorator will handle this
                raise httpx.HTTPStatusError(f"Rate limited", request=response.request, response=response)
            else:
                return {"data": [], "error": f"HTTP {response.status_code}: {response.text}"}

    except httpx.HTTPStatusError:
        raise  # Let retry decorator handle this
    except Exception as e:
        return {"data": [], "error": str(e)}

@api_retry()
async def get_arxiv_paper(arxiv_id: str) -> Dict[str, Any]:
    """Get paper from arXiv using official arxiv library"""
    await rate_limit_async("arxiv")

    try:
        import asyncio

        def _fetch_arxiv():
            # Use the official arxiv library for better results
            search = arxiv.Search(id_list=[arxiv_id])
            papers = list(search.results())

            if papers:
                paper = papers[0]
                return {
                    "title": paper.title,
                    "authors": [str(author) for author in paper.authors],
                    "abstract": paper.summary,
                    "published": paper.published.isoformat() if paper.published else None,
                    "pdf_url": paper.pdf_url,
                    "entry_id": paper.entry_id,
                    "source": "arXiv"
                }
            else:
                return {"error": "Paper not found on arXiv"}

        return await asyncio.to_thread(_fetch_arxiv)

    except Exception as e:
        return {"error": f"arXiv search failed: {str(e)}"}

@api_retry()
async def search_pubmed(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search PubMed for biomedical literature"""
    await rate_limit_async("pubmed")

    try:
        import asyncio
        from pymed import PubMed

        def _search_pubmed():
            pubmed = PubMed(tool="scholarly-mcp", email="research@example.com")
            results = pubmed.query(query, max_results=limit)
            papers = []

            for article in results:
                paper_data = {
                    "title": article.title,
                    "authors": [str(author) for author in (article.authors or [])],
                    "abstract": article.abstract,
                    "journal": article.journal,
                    "publication_date": str(article.publication_date) if article.publication_date else None,
                    "pubmed_id": article.pubmed_id,
                    "doi": article.doi,
                    "source": "PubMed"
                }
                papers.append(paper_data)

            return {"data": papers, "total": len(papers)}

        return await asyncio.to_thread(_search_pubmed)

    except Exception as e:
        return {"data": [], "error": f"PubMed search failed: {str(e)}"}

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
async def search_author(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for authors by name on Google Scholar.

    Args:
        name: The author's name to search for
        limit: Maximum number of results to return (default: 5)

    Returns:
        List of author information dictionaries
    """
    try:
        import asyncio

        # Run scholarly operations in thread pool to avoid blocking
        @scholarly_retry()
        def _search_author():
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

        results = await asyncio.to_thread(_search_author)
        return results
    except Exception as e:
        return [{"error": f"Failed to search for author: {str(e)}"}]

@mcp.tool
async def search_publications(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for publications by keywords or title.

    Args:
        query: Search query for publications
        limit: Maximum number of results to return (default: 5)

    Returns:
        List of publication information dictionaries
    """
    try:
        import asyncio
        import time
        import random

        # Run scholarly operations in thread pool to avoid blocking
        @scholarly_retry()
        def _search_publications():
            # Add some randomization to avoid detection
            time.sleep(random.uniform(1, 3))

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

        results = await asyncio.to_thread(_search_publications)
        return results
    except Exception as e:
        # If Google Scholar fails, try to provide a meaningful fallback
        error_msg = str(e)
        if "Cannot Fetch from Google Scholar" in error_msg or "Timeout" in error_msg:
            return [{
                "error": f"Google Scholar access temporarily blocked. This is common due to rate limiting. Please try again in a few minutes or use specific DOI/title search functions instead.",
                "suggestion": "Try using get_full_text_by_title() or get_full_text_by_doi() for specific papers"
            }]
        return [{"error": f"Failed to search for publications: {error_msg}"}]

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
    scholarly_results = await search_publications(title, limit=1)

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
    papers = await search_publications(query, limit)

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
async def extract_pdf_text_from_url(pdf_url: str) -> Dict[str, Any]:
    """
    Extract text from a PDF URL.

    Args:
        pdf_url: Direct URL to a PDF file

    Returns:
        Dictionary with extracted text and metadata
    """
    try:
        # Download and extract using async httpx
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

                result["pdf_url"] = pdf_url
                return result
            else:
                return {"error": f"Failed to download PDF: HTTP {response.status_code}"}

    except Exception as e:
        return {"error": f"PDF extraction failed: {str(e)}"}

@mcp.tool
async def comprehensive_search(query: str, limit: int = 5, include_full_text: bool = False) -> List[Dict[str, Any]]:
    """
    Comprehensive search across multiple academic databases with fallback support.

    Args:
        query: Search query for publications
        limit: Maximum number of results to return (default: 5)
        include_full_text: Whether to attempt full text extraction (default: False)

    Returns:
        List of papers with metadata from multiple sources
    """
    all_results = []

    # Try Google Scholar first
    try:
        logger.info(f"Searching Google Scholar for: {query}")
        scholar_results = await search_publications(query, limit)
        if scholar_results and not scholar_results[0].get("error"):
            for result in scholar_results:
                result["source"] = "Google Scholar"
                all_results.append(result)
            logger.info(f"Found {len(scholar_results)} results from Google Scholar")
    except Exception as e:
        logger.warning(f"Google Scholar search failed: {e}")

    # If we don't have enough results, try Semantic Scholar
    if len(all_results) < limit:
        try:
            logger.info(f"Searching Semantic Scholar for: {query}")
            semantic_results = await search_semantic_scholar(query, limit - len(all_results))
            if semantic_results.get("data"):
                for paper in semantic_results["data"]:
                    result = {
                        "title": paper.get("title", ""),
                        "authors": [author.get("name", "") for author in paper.get("authors", [])],
                        "year": paper.get("year"),
                        "abstract": paper.get("abstract", ""),
                        "venue": paper.get("venue", ""),
                        "citation_count": paper.get("citationCount", 0),
                        "url": paper.get("url", ""),
                        "source": "Semantic Scholar",
                        "paper_id": paper.get("paperId")
                    }
                    all_results.append(result)
                logger.info(f"Found {len(semantic_results['data'])} additional results from Semantic Scholar")
        except Exception as e:
            logger.warning(f"Semantic Scholar search failed: {e}")

    # If we still don't have enough and the query looks biomedical, try PubMed
    if len(all_results) < limit and any(term in query.lower() for term in ['gene', 'protein', 'disease', 'medical', 'clinical', 'drug', 'therapy', 'patient']):
        try:
            logger.info(f"Searching PubMed for biomedical query: {query}")
            pubmed_results = await search_pubmed(query, limit - len(all_results))
            if pubmed_results.get("data"):
                for paper in pubmed_results["data"]:
                    result = {
                        "title": paper.get("title", ""),
                        "authors": paper.get("authors", []),
                        "abstract": paper.get("abstract", ""),
                        "journal": paper.get("journal", ""),
                        "publication_date": paper.get("publication_date"),
                        "pubmed_id": paper.get("pubmed_id"),
                        "doi": paper.get("doi"),
                        "source": "PubMed"
                    }
                    all_results.append(result)
                logger.info(f"Found {len(pubmed_results['data'])} additional results from PubMed")
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")

    # If requested, try to get full text for top results
    if include_full_text and all_results:
        logger.info("Attempting to retrieve full text for top results...")
        for i, result in enumerate(all_results[:3]):  # Only try for top 3 to avoid too many requests
            try:
                title = result.get("title", "")
                if title:
                    full_text_result = await get_full_text_by_title(title, extract_text=False)
                    if full_text_result.get("open_access_sources"):
                        result["open_access_urls"] = [src.get("url") for src in full_text_result["open_access_sources"]]
            except Exception as e:
                logger.warning(f"Full text retrieval failed for result {i}: {e}")

    # Sort by relevance (citation count if available)
    all_results.sort(key=lambda x: x.get("citation_count", x.get("num_citations", 0)), reverse=True)

    return all_results[:limit]

# Run the server
def main():
    """Main entry point for the server"""
    # Setup proxy configuration on startup
    setup_scholarly_proxy()
    logger.info("Enhanced Scholarly MCP Server starting...")
    mcp.run()

if __name__ == "__main__":
    main()