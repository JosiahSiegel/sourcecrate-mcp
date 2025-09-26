"""
Comprehensive search engine that queries multiple academic databases.
"""

import logging
from typing import Any, Dict, List

from ..api_clients import (
    search_crossref,
    search_semantic_scholar,
    search_arxiv,
    search_pubmed,
    search_google_scholar_fallback
)
from ..api_clients.core_client import search_core
from ..api_clients.doaj_client import search_doaj
from ..api_clients.socarxiv_client import search_socarxiv, search_osf_preprints_general
from ..config import api_status
from .pdf_processor import extract_pdf_text

logger = logging.getLogger(__name__)


async def comprehensive_search_internal(query: str, limit: int = 5, include_full_text: bool = False) -> Dict[str, Any]:
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

    return result_summary