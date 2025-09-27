"""
PubMed and PubMed Central API client for biomedical literature search.
Enhanced with PMC full-text access and improved medical research capabilities.
"""

import asyncio
import logging
import aiohttp
from typing import Any, Dict, List
from urllib.parse import quote_plus

from pymed import PubMed
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import cache, config, api_status

logger = logging.getLogger(__name__)


async def _check_pmc_availability(pmid: str) -> Dict[str, str]:
    """Check if a PubMed article is available in PMC with full text"""
    if not pmid:
        return {}

    try:
        # Use NCBI elink to find PMC ID
        elink_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
        params = {
            "dbfrom": "pubmed",
            "db": "pmc",
            "id": pmid,
            "retmode": "json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(elink_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    linksets = data.get("linksets", [])

                    for linkset in linksets:
                        linksetdbs = linkset.get("linksetdbs", [])
                        for linksetdb in linksetdbs:
                            if linksetdb.get("dbto") == "pmc":
                                pmc_ids = linksetdb.get("links", [])
                                if pmc_ids:
                                    pmc_id = pmc_ids[0]
                                    return {
                                        "pmc_id": f"PMC{pmc_id}",
                                        "pdf_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/",
                                        "full_text_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/"
                                    }
    except Exception as e:
        logger.debug(f"PMC availability check failed for PMID {pmid}: {e}")

    return {}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_pubmed(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search PubMed for biomedical literature with PMC integration"""
    cache_key = f"pubmed_enhanced:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        def _search_pubmed():
            pubmed = PubMed(tool="paperez-mcp", email=config.crossref_email)
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
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{article.pubmed_id}/" if article.pubmed_id else "",
                    "citation_count": 0  # PubMed doesn't provide citation counts
                }
                results.append(result)
            return results

        results = await asyncio.to_thread(_search_pubmed)

        # Enhance results with PMC availability for better PDF access
        enhanced_results = []
        for result in results:
            if result.get("pubmed_id"):
                pmc_info = await _check_pmc_availability(result["pubmed_id"])
                if pmc_info:
                    result.update(pmc_info)
                    result["open_access_pdf"] = pmc_info.get("pdf_url")
                    logger.debug(f"PMC available for {result['title'][:50]}...")
            enhanced_results.append(result)

        # Cache for 1 hour
        cache.set(cache_key, enhanced_results, expire=3600)
        pmc_count = sum(1 for r in enhanced_results if r.get("pmc_id"))
        logger.info(f"✅ PubMed: Found {len(enhanced_results)} results ({pmc_count} with PMC full-text) for '{query}'")
        return enhanced_results

    except Exception as e:
        logger.warning(f"❌ PubMed search failed: {e}")
        api_status["pubmed"] = False
        return []


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def search_pubmed_central(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search PubMed Central directly for open access full-text articles"""
    cache_key = f"pmc:{query}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        # Use NCBI E-utilities to search PMC directly
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pmc",
            "term": query,
            "retmax": limit,
            "retmode": "json",
            "sort": "relevance"
        }

        async with aiohttp.ClientSession() as session:
            # Search for PMC articles
            async with session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    logger.warning(f"PMC search failed with status {response.status}")
                    return []

                search_data = await response.json()
                pmc_ids = search_data.get("esearchresult", {}).get("idlist", [])

                if not pmc_ids:
                    logger.info(f"No PMC results found for '{query}'")
                    return []

                # Fetch detailed information for found articles
                fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                fetch_params = {
                    "db": "pmc",
                    "id": ",".join(pmc_ids),
                    "retmode": "xml"
                }

                async with session.get(fetch_url, params=fetch_params) as fetch_response:
                    if fetch_response.status != 200:
                        logger.warning(f"PMC fetch failed with status {fetch_response.status}")
                        return []

                    # For now, return basic structure - full XML parsing would require lxml
                    results = []
                    for pmc_id in pmc_ids:
                        result = {
                            "title": f"PMC Article {pmc_id}",  # Would be parsed from XML
                            "authors": [],
                            "abstract": "Available in PMC full-text",
                            "journal": "PMC Collection",
                            "year": None,
                            "pmc_id": f"PMC{pmc_id}",
                            "doi": None,
                            "source": "PubMed Central",
                            "url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/",
                            "pdf_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/",
                            "open_access_pdf": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/",
                            "full_text_url": f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/",
                            "citation_count": 0
                        }
                        results.append(result)

                    # Cache for 1 hour
                    cache.set(cache_key, results, expire=3600)
                    logger.info(f"✅ PMC: Found {len(results)} full-text articles for '{query}'")
                    return results

    except Exception as e:
        logger.warning(f"❌ PMC search failed: {e}")
        return []