"""
Comprehensive search engine that queries multiple academic databases.
"""

import logging
from typing import Any

from ..api_clients.arxiv_client import search_arxiv
from ..api_clients.google_scholar_client import search_google_scholar_fallback
from ..api_clients.pubmed_client import search_pubmed, search_pubmed_central
from ..config import api_status, get_search_service
from .pdf_processor import extract_pdf_text
from .source_health_monitor import health_monitor

logger = logging.getLogger(__name__)


# Placeholder functions for missing search clients
async def search_semantic_scholar(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Placeholder for semantic scholar search - to be implemented"""
    logger.warning("Semantic Scholar search not implemented yet")
    return []


async def search_clinicaltrials(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Placeholder for clinical trials search - to be implemented"""
    logger.warning("Clinical trials search not implemented yet")
    return []


async def comprehensive_search_internal(query: str, limit: int = 5, include_full_text: bool = False) -> dict[str, Any]:
    """
    Comprehensive search across multiple academic databases with fallback support.

    Args:
        query: Search query for publications
        limit: Maximum number of results to return (default: 5)
        include_full_text: Whether to attempt full text extraction (default: False)

    Returns:
        Dictionary with search results and metadata from multiple sources
    """
    all_results = []
    remaining_limit = limit

    # Get search functions from unified config system
    search_service = get_search_service()
    search_functions = search_service.get_search_functions()

    # Phase 1: CrossRef (most reliable, no blocking)
    if remaining_limit > 0 and api_status["crossref"] and "search_crossref" in search_functions:
        try:
            crossref_results = await health_monitor.monitor_request("crossref", search_functions["search_crossref"], query, remaining_limit)
            all_results.extend(crossref_results)
            remaining_limit = max(0, limit - len(all_results))
        except Exception as e:
            logger.warning(f"CrossRef failed: {e}")

    # Phase 2: Semantic Scholar
    if remaining_limit > 0 and api_status["semantic_scholar"]:
        try:
            semantic_results = await health_monitor.monitor_request("semantic_scholar", search_semantic_scholar, query, remaining_limit)
            all_results.extend(semantic_results)
            remaining_limit = max(0, limit - len(all_results))
        except Exception as e:
            logger.warning(f"Semantic Scholar failed: {e}")

    # Phase 3: arXiv (for technical papers)
    if remaining_limit > 0 and api_status["arxiv"]:
        try:
            arxiv_results = await health_monitor.monitor_request("arxiv", search_arxiv, query, remaining_limit)
            all_results.extend(arxiv_results)
            remaining_limit = max(0, limit - len(all_results))
        except Exception as e:
            logger.warning(f"arXiv failed: {e}")

    # Phase 4: Enhanced Medical Research - PubMed, PMC, and ClinicalTrials
    biomedical_terms = ['gene', 'protein', 'disease', 'medical', 'clinical', 'drug', 'therapy', 'patient', 'cancer', 'treatment', 'diabetes', 'immunotherapy', 'vaccine', 'trial', 'study', 'health', 'medicine', 'surgery', 'diagnosis']
    is_medical_query = any(term in query.lower() for term in biomedical_terms)

    if remaining_limit > 0 and is_medical_query:
        # Phase 4a: PubMed Central (full-text medical papers)
        if api_status["pubmed_central"]:
            try:
                pmc_results = await health_monitor.monitor_request("pubmed_central", search_pubmed_central, query, min(remaining_limit, 3))
                all_results.extend(pmc_results)
                remaining_limit = max(0, limit - len(all_results))
                logger.info(f"PMC search: {len(pmc_results)} results")
            except Exception as e:
                logger.warning(f"PubMed Central failed: {e}")

        # Phase 4b: PubMed (enhanced with PMC links)
        if remaining_limit > 0 and api_status["pubmed"]:
            try:
                pubmed_results = await health_monitor.monitor_request("pubmed", search_pubmed, query, remaining_limit)
                all_results.extend(pubmed_results)
                remaining_limit = max(0, limit - len(all_results))
                logger.info(f"PubMed search: {len(pubmed_results)} results")
            except Exception as e:
                logger.warning(f"PubMed failed: {e}")

        # Phase 4c: ClinicalTrials.gov (for clinical research)
        if remaining_limit > 0 and api_status["clinicaltrials"]:
            try:
                trial_results = await health_monitor.monitor_request("clinicaltrials", search_clinicaltrials, query, min(remaining_limit, 2))
                all_results.extend(trial_results)
                remaining_limit = max(0, limit - len(all_results))
                logger.info(f"ClinicalTrials search: {len(trial_results)} results")
            except Exception as e:
                logger.warning(f"ClinicalTrials.gov failed: {e}")
    elif remaining_limit > 0 and api_status["pubmed"]:
        # Fallback: Still search PubMed for non-medical queries that might have biomedical relevance
        try:
            pubmed_results = await health_monitor.monitor_request("pubmed", search_pubmed, query, min(remaining_limit, 2))
            all_results.extend(pubmed_results)
            remaining_limit = max(0, limit - len(all_results))
        except Exception as e:
            logger.warning(f"PubMed fallback failed: {e}")

    # Phase 5: Google Scholar (final fallback)
    if remaining_limit > 0 and api_status["google_scholar"]:
        try:
            scholar_results = await health_monitor.monitor_request("google_scholar", search_google_scholar_fallback, query, remaining_limit)
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

    return result_summary
