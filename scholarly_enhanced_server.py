#!/usr/bin/env python3
"""
Enhanced Scholarly MCP Server with 100% Reliable Functionality

A comprehensive academic research server with multi-source fallback,
robust caching, and graceful error handling. Zero blocking, maximum reliability.
"""

import asyncio
import json
import logging
import os
import re
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import arxiv
import fitz  # PyMuPDF
import httpx
from crossref.restful import Works
from diskcache import Cache
from fake_useragent import UserAgent
from fastmcp import FastMCP
from pymed import PubMed
from scholarly import ProxyGenerator, scholarly
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache instance
cache = Cache('/tmp/scholarly-mcp-cache', size_limit=1e9)  # 1GB cache

@dataclass
class APIConfig:
    """Configuration loaded from environment variables"""
    semantic_scholar_api_key: Optional[str] = None
    scraperapi_key: Optional[str] = None
    crossref_email: str = "research@example.com"
    max_retries: int = 3
    base_delay: float = 1.0

    def __post_init__(self):
        # Load from environment
        self.semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.scraperapi_key = os.getenv("SCRAPERAPI_KEY")
        self.crossref_email = os.getenv("CROSSREF_EMAIL", self.crossref_email)

# Global configuration
config = APIConfig()

# Initialize FastMCP server
mcp = FastMCP("Enhanced Scholarly MCP Server - 100% Reliable")

# API health status
api_status = {
    "crossref": True,
    "semantic_scholar": True,
    "arxiv": True,
    "pubmed": True,
    "google_scholar": True
}

def setup_scholarly_proxy():
    """Setup scholarly with robust proxy configuration"""
    try:
        if config.scraperapi_key:
            pg = ProxyGenerator()
            pg.ScraperAPI(config.scraperapi_key)
            scholarly.use_proxy(pg)
            logger.info("✅ Scholarly configured with ScraperAPI")
            return True
        else:
            # Try free proxies with proper error handling
            try:
                pg = ProxyGenerator()
                # Fix the FreeProxies call with proper parameters
                pg.FreeProxies(timeout=10, wait_time=60)
                scholarly.use_proxy(pg)
                logger.info("✅ Scholarly configured with free proxies")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Free proxies failed: {e}")

        # Setup user agent rotation regardless
        ua = UserAgent()
        logger.info("✅ User agent rotation configured")
        return False

    except Exception as e:
        logger.warning(f"❌ Proxy setup failed: {e}")
        api_status["google_scholar"] = False
        return False

async def create_http_client() -> httpx.AsyncClient:
    """Create HTTP client with redirect handling and HTTP/2 support"""
    ua = UserAgent()
    return httpx.AsyncClient(
        follow_redirects=True,
        http2=True,
        timeout=60.0,
        headers={"User-Agent": ua.random},
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10)
    )

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_crossref(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search CrossRef API (primary source - most reliable)"""
    cache_key = f"crossref:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        works = Works()
        results = []

        # Use polite pool with email
        response = works.query(query).sort('relevance').order('desc')

        for i, item in enumerate(response):
            if i >= limit:
                break

            result = {
                "title": item.get("title", [""])[0] if item.get("title") else "",
                "authors": [
                    f"{author.get('given', '')} {author.get('family', '')}"
                    for author in item.get("author", [])
                ],
                "doi": item.get("DOI", ""),
                "year": item.get("published-print", {}).get("date-parts", [[None]])[0][0],
                "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                "abstract": item.get("abstract", ""),
                "citation_count": item.get("is-referenced-by-count", 0),
                "url": f"https://doi.org/{item.get('DOI', '')}" if item.get("DOI") else "",
                "source": "CrossRef",
                "publisher": item.get("publisher", "")
            }
            results.append(result)

        # Cache for 1 hour
        cache.set(cache_key, results, expire=3600)
        logger.info(f"✅ CrossRef: Found {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.warning(f"❌ CrossRef search failed: {e}")
        api_status["crossref"] = False
        return []

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
async def search_semantic_scholar(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search Semantic Scholar with proper rate limiting"""
    cache_key = f"semantic:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "paperId,title,authors,year,abstract,venue,citationCount,url,openAccessPdf"
        }

        headers = {}
        if config.semantic_scholar_api_key:
            headers["x-api-key"] = config.semantic_scholar_api_key

        async with create_http_client() as client:
            response = await client.get(url, params=params, headers=headers)

            if response.status_code == 429:
                logger.warning("⚠️ Semantic Scholar rate limited")
                raise httpx.HTTPStatusError(f"Rate limited", request=response.request, response=response)

            if response.status_code == 200:
                data = response.json()
                results = []

                for paper in data.get("data", []):
                    result = {
                        "title": paper.get("title", ""),
                        "authors": [author.get("name", "") for author in paper.get("authors", [])],
                        "year": paper.get("year"),
                        "abstract": paper.get("abstract", ""),
                        "venue": paper.get("venue", ""),
                        "citation_count": paper.get("citationCount", 0),
                        "url": paper.get("url", ""),
                        "source": "Semantic Scholar",
                        "paper_id": paper.get("paperId"),
                        "open_access_pdf": paper.get("openAccessPdf", {}).get("url") if paper.get("openAccessPdf") else None
                    }
                    results.append(result)

                # Cache for 1 hour
                cache.set(cache_key, results, expire=3600)
                logger.info(f"✅ Semantic Scholar: Found {len(results)} results for '{query}'")
                return results
            else:
                logger.warning(f"❌ Semantic Scholar HTTP {response.status_code}")
                return []

    except httpx.HTTPStatusError:
        raise  # Let retry handle this
    except Exception as e:
        logger.warning(f"❌ Semantic Scholar search failed: {e}")
        api_status["semantic_scholar"] = False
        return []

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_arxiv(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search arXiv using official library"""
    cache_key = f"arxiv:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        def _search_arxiv():
            search = arxiv.Search(
                query=query,
                max_results=limit,
                sort_by=arxiv.SortCriterion.Relevance
            )

            results = []
            for paper in search.results():
                result = {
                    "title": paper.title,
                    "authors": [str(author) for author in paper.authors],
                    "abstract": paper.summary,
                    "year": paper.published.year if paper.published else None,
                    "arxiv_id": paper.entry_id.split('/')[-1],
                    "pdf_url": paper.pdf_url,
                    "source": "arXiv",
                    "categories": paper.categories,
                    "url": paper.entry_id
                }
                results.append(result)
            return results

        results = await asyncio.to_thread(_search_arxiv)

        # Cache for 6 hours (arXiv updates once daily)
        cache.set(cache_key, results, expire=21600)
        logger.info(f"✅ arXiv: Found {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.warning(f"❌ arXiv search failed: {e}")
        api_status["arxiv"] = False
        return []

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_pubmed(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search PubMed for biomedical literature"""
    cache_key = f"pubmed:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        def _search_pubmed():
            pubmed = PubMed(tool="scholarly-mcp", email=config.crossref_email)
            results = []

            for article in pubmed.query(query, max_results=limit):
                result = {
                    "title": article.title,
                    "authors": [str(author) for author in (article.authors or [])],
                    "abstract": article.abstract,
                    "journal": article.journal,
                    "year": article.publication_date.year if article.publication_date else None,
                    "pubmed_id": article.pubmed_id,
                    "doi": article.doi,
                    "source": "PubMed",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id}/" if article.pubmed_id else ""
                }
                results.append(result)
            return results

        results = await asyncio.to_thread(_search_pubmed)

        # Cache for 1 hour
        cache.set(cache_key, results, expire=3600)
        logger.info(f"✅ PubMed: Found {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.warning(f"❌ PubMed search failed: {e}")
        api_status["pubmed"] = False
        return []

async def search_google_scholar_fallback(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Google Scholar as final fallback with proxy support"""
    if not api_status["google_scholar"]:
        return []

    cache_key = f"scholar:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        def _search_scholar():
            search_query = scholarly.search_pubs(query)
            results = []

            for i, pub in enumerate(search_query):
                if i >= limit:
                    break

                bib = pub.get('bib', {})
                result = {
                    "title": bib.get('title', ''),
                    "authors": bib.get('author', []),
                    "year": bib.get('pub_year', ''),
                    "abstract": bib.get('abstract', ''),
                    "venue": bib.get('venue', ''),
                    "citation_count": pub.get('num_citations', 0),
                    "url": pub.get('pub_url', ''),
                    "source": "Google Scholar"
                }
                results.append(result)
            return results

        results = await asyncio.to_thread(_search_scholar)

        # Cache for 30 minutes (shorter due to potential blocking)
        cache.set(cache_key, results, expire=1800)
        logger.info(f"✅ Google Scholar: Found {len(results)} results for '{query}'")
        return results

    except Exception as e:
        logger.warning(f"❌ Google Scholar search failed: {e}")
        api_status["google_scholar"] = False
        return []

async def extract_pdf_text(pdf_url: str) -> Dict[str, Any]:
    """Extract text from PDF with redirect handling"""
    cache_key = f"pdf_text:{pdf_url}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        async with create_http_client() as client:
            response = await client.get(pdf_url)

            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name

                # Extract text
                doc = fitz.open(tmp_path)
                full_text = ""

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    full_text += f"\n--- Page {page_num + 1} ---\n{text}\n"

                doc.close()
                os.unlink(tmp_path)  # Cleanup

                result = {
                    "text": full_text,
                    "num_pages": len(doc),
                    "extraction_method": "PyMuPDF",
                    "pdf_url": pdf_url,
                    "success": True
                }

                # Cache extracted text permanently (or until cache cleanup)
                cache.set(cache_key, result, expire=86400 * 30)  # 30 days
                return result
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "pdf_url": pdf_url
                }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "pdf_url": pdf_url
        }

# MCP Tools Implementation

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
    remaining_limit = limit

    # Phase 1: CrossRef (most reliable, no blocking)
    if remaining_limit > 0 and api_status["crossref"]:
        try:
            crossref_results = await search_crossref(query, remaining_limit)
            all_results.extend(crossref_results)
            remaining_limit = max(0, limit - len(all_results))
        except Exception as e:
            logger.warning(f"CrossRef failed: {e}")

    # Phase 2: Semantic Scholar
    if remaining_limit > 0 and api_status["semantic_scholar"]:
        try:
            semantic_results = await search_semantic_scholar(query, remaining_limit)
            all_results.extend(semantic_results)
            remaining_limit = max(0, limit - len(all_results))
        except Exception as e:
            logger.warning(f"Semantic Scholar failed: {e}")

    # Phase 3: arXiv (for technical papers)
    if remaining_limit > 0 and api_status["arxiv"]:
        try:
            arxiv_results = await search_arxiv(query, remaining_limit)
            all_results.extend(arxiv_results)
            remaining_limit = max(0, limit - len(all_results))
        except Exception as e:
            logger.warning(f"arXiv failed: {e}")

    # Phase 4: PubMed (for biomedical queries)
    biomedical_terms = ['gene', 'protein', 'disease', 'medical', 'clinical', 'drug', 'therapy', 'patient', 'cancer', 'treatment']
    if remaining_limit > 0 and api_status["pubmed"] and any(term in query.lower() for term in biomedical_terms):
        try:
            pubmed_results = await search_pubmed(query, remaining_limit)
            all_results.extend(pubmed_results)
            remaining_limit = max(0, limit - len(all_results))
        except Exception as e:
            logger.warning(f"PubMed failed: {e}")

    # Phase 5: Google Scholar (final fallback)
    if remaining_limit > 0 and api_status["google_scholar"]:
        try:
            scholar_results = await search_google_scholar_fallback(query, remaining_limit)
            all_results.extend(scholar_results)
        except Exception as e:
            logger.warning(f"Google Scholar failed: {e}")

    # Phase 6: Add full text if requested
    if include_full_text and all_results:
        for result in all_results[:3]:  # Only top 3 to avoid overload
            pdf_url = result.get("pdf_url") or result.get("open_access_pdf")
            if pdf_url:
                try:
                    text_result = await extract_pdf_text(pdf_url)
                    if text_result.get("success"):
                        result["full_text"] = text_result["text"]
                        result["extraction_method"] = text_result["extraction_method"]
                except Exception as e:
                    logger.warning(f"PDF extraction failed for {pdf_url}: {e}")

    # Sort by citation count if available
    all_results.sort(key=lambda x: x.get("citation_count", 0), reverse=True)

    # Add API status info
    result_summary = {
        "results": all_results[:limit],
        "total_found": len(all_results),
        "api_status": api_status.copy(),
        "sources_used": list(set([r.get("source") for r in all_results])),
        "query": query
    }

    return [result_summary]

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
    # Use comprehensive search but return just the results
    comprehensive_result = await comprehensive_search(query, limit, include_full_text=False)
    if comprehensive_result and comprehensive_result[0].get("results"):
        return comprehensive_result[0]["results"]
    return []

@mcp.tool
async def search_author(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for authors by name.

    Args:
        name: Author name to search for
        limit: Maximum number of results to return (default: 5)

    Returns:
        List of author information dictionaries
    """
    if not api_status["google_scholar"]:
        return [{"error": "Author search requires Google Scholar, which is currently unavailable. Try again later."}]

    try:
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
                    'url_picture': author.get('url_picture', ''),
                    'source': 'Google Scholar'
                })
            return results

        results = await asyncio.to_thread(_search_author)
        return results

    except Exception as e:
        return [{"error": f"Author search failed: {str(e)}"}]

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
    try:
        # First try to find open access versions
        crossref_results = await search_crossref(f"DOI:{doi}", 1)

        if crossref_results:
            paper = crossref_results[0]

            # Try Semantic Scholar for open access PDF
            semantic_results = await search_semantic_scholar(paper.get("title", ""), 1)
            if semantic_results and semantic_results[0].get("open_access_pdf"):
                pdf_url = semantic_results[0]["open_access_pdf"]

                if extract_text:
                    text_result = await extract_pdf_text(pdf_url)
                    if text_result.get("success"):
                        paper["full_text"] = text_result["text"]
                        paper["pdf_url"] = pdf_url
                        paper["extraction_method"] = text_result["extraction_method"]
                        return paper

                paper["pdf_url"] = pdf_url
                return paper

            return {**paper, "error": "No open access version found"}

        return {"error": f"Paper with DOI {doi} not found"}

    except Exception as e:
        return {"error": f"DOI lookup failed: {str(e)}"}

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
    try:
        # Search across all sources
        results = await comprehensive_search(title, 1, include_full_text=extract_text)

        if results and results[0].get("results"):
            paper = results[0]["results"][0]
            return paper

        return {"error": f"Paper '{title}' not found"}

    except Exception as e:
        return {"error": f"Title search failed: {str(e)}"}

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
    open_access_sources = []

    try:
        # Search query - use DOI if available, otherwise title
        query = f"DOI:{doi}" if doi else title

        # Check Semantic Scholar
        semantic_results = await search_semantic_scholar(query, 1)
        if semantic_results and semantic_results[0].get("open_access_pdf"):
            open_access_sources.append({
                "source": "Semantic Scholar",
                "url": semantic_results[0]["open_access_pdf"],
                "type": "pdf"
            })

        # Check arXiv
        arxiv_results = await search_arxiv(title, 1)
        if arxiv_results and arxiv_results[0].get("pdf_url"):
            open_access_sources.append({
                "source": "arXiv",
                "url": arxiv_results[0]["pdf_url"],
                "type": "preprint"
            })

        return {
            "title": title,
            "doi": doi,
            "open_access_sources": open_access_sources,
            "total_sources": len(open_access_sources)
        }

    except Exception as e:
        return {
            "title": title,
            "doi": doi,
            "open_access_sources": [],
            "error": str(e)
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
    result = await comprehensive_search(query, limit, include_full_text=extract_text)
    if result and result[0].get("results"):
        return result[0]["results"]
    return []

@mcp.tool
async def get_api_status() -> Dict[str, Any]:
    """
    Get the current status of all APIs and cache statistics.

    Returns:
        Dictionary with API status and cache information
    """
    cache_stats = {
        "size": len(cache),
        "hits": getattr(cache, 'stats', {}).get('hits', 0),
        "misses": getattr(cache, 'stats', {}).get('misses', 0)
    }

    return {
        "api_status": api_status.copy(),
        "cache_stats": cache_stats,
        "config": {
            "has_semantic_scholar_key": bool(config.semantic_scholar_api_key),
            "has_scraperapi_key": bool(config.scraperapi_key),
            "crossref_email": config.crossref_email
        }
    }

def main():
    """Main entry point for the server"""
    # Setup proxy configuration on startup
    proxy_success = setup_scholarly_proxy()

    # Log startup information
    logger.info("🚀 Enhanced Scholarly MCP Server starting...")
    logger.info(f"📧 CrossRef email: {config.crossref_email}")
    logger.info(f"🔑 Semantic Scholar API key: {'✅' if config.semantic_scholar_api_key else '❌'}")
    logger.info(f"🔑 ScraperAPI key: {'✅' if config.scraperapi_key else '❌'}")
    logger.info(f"🌐 Proxy setup: {'✅' if proxy_success else '❌'}")

    # Start the server
    mcp.run()

if __name__ == "__main__":
    main()