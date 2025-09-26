"""
Smart search functionality that prioritizes downloadable papers.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any

from ..config import config
from .topic_classifier import get_recommended_sources, should_skip_source_for_topic, get_topic_explanation
from .query_processor import generate_alternative_queries, optimize_query_for_source

logger = logging.getLogger(__name__)


async def smart_downloadable_search(
    query: str,
    limit: int,
    search_funcs: Dict[str, Any],
    utils: Dict[str, Any],
    api_status: Dict[str, bool]
) -> List[Dict[str, Any]]:
    """
    Smart search that prioritizes sources with downloadable PDFs and only counts
    successfully downloadable papers toward the limit.

    Args:
        query: Search query
        limit: Number of downloadable papers to find
        search_funcs: Dictionary of search functions by source
        utils: Dictionary of utility functions
        api_status: API availability status

    Returns:
        List of papers that were successfully downloaded
    """
    downloadable_papers = []
    all_candidates = []

    # Topic analysis for intelligent source selection
    topic_analysis = None
    if config.enable_topic_detection:
        topic_analysis = get_topic_explanation(query)
        logger.info(f"🧠 Topic Analysis: {json.dumps(topic_analysis, indent=2)}")

    # Initialize comprehensive search logging
    search_log = {
        "query": query,
        "limit": limit,
        "timestamp": datetime.now().isoformat(),
        "sources_searched": [],
        "results_per_source": {},
        "api_status": api_status.copy(),
        "search_strategy": "smart_downloadable",
        "topic_analysis": topic_analysis,
        "total_candidates": 0,
        "unique_candidates": 0,
        "download_attempts": 0,
        "successful_downloads": 0
    }

    # Strategy: Use topic-aware source prioritization
    if config.enable_topic_detection and topic_analysis:
        recommended_sources = get_recommended_sources(query)
        source_priority = []

        # Map recommended sources to descriptions
        source_descriptions = {
            'arxiv': 'arXiv has highest PDF availability',
            'semantic_scholar': 'Semantic Scholar often has open access PDFs',
            'crossref': 'CrossRef comprehensive but mostly paywalled',
            'pubmed': 'PubMed for biomedical open access',
            'google_scholar': 'Google Scholar fallback',
            'core': 'CORE open access repository',
            'doaj': 'DOAJ open access journals',
            'socarxiv': 'SocArXiv social science preprints',
            'osf_preprints': 'OSF preprints across disciplines'
        }

        for source in recommended_sources:
            if source in source_descriptions:
                source_priority.append((source, source_descriptions[source]))

        # Add any remaining sources not in recommendations
        all_sources = ['arxiv', 'semantic_scholar', 'crossref', 'pubmed', 'google_scholar', 'core', 'doaj', 'socarxiv', 'osf_preprints']
        for source in all_sources:
            if source not in recommended_sources and source in source_descriptions:
                source_priority.append((source, f"{source_descriptions[source]} (lower priority)"))

        logger.info(f"🎯 Topic-based source priority: {[s[0] for s in source_priority]}")
    else:
        # Fallback to default strategy
        source_priority = [
            ('arxiv', 'arXiv has highest PDF availability'),
            ('semantic_scholar', 'Semantic Scholar often has open access PDFs'),
            ('core', 'CORE open access repository'),
            ('crossref', 'CrossRef comprehensive but mostly paywalled'),
            ('doaj', 'DOAJ open access journals'),
            ('socarxiv', 'SocArXiv social science preprints'),
            ('pubmed', 'PubMed for biomedical open access'),
            ('google_scholar', 'Google Scholar fallback')
        ]

    # Search each source for more papers than we need
    search_limit_per_source = max(10, limit * 3)  # Search more to find downloadable ones
    search_log["search_limit_per_source"] = search_limit_per_source

    logger.info(f"🔍 Starting smart search for '{query}' (limit: {limit})")
    logger.info(f"📊 API Status: {json.dumps(api_status, indent=2)}")

    for source_name, description in source_priority:
        if api_status.get(source_name, False):
            try:
                # Smart source skipping based on topic analysis
                if config.enable_topic_detection and should_skip_source_for_topic(source_name, query):
                    search_log["results_per_source"][source_name] = {
                        "skipped": True,
                        "reason": "Topic-based skip (not relevant for this query type)"
                    }
                    logger.info(f"⏭️ Skipping {source_name}: Not relevant for this topic")
                    continue

                # Legacy PubMed biomedical check (now enhanced by topic detection)
                if source_name == 'pubmed' and not config.enable_topic_detection:
                    biomedical_terms = ['gene', 'protein', 'disease', 'medical', 'clinical', 'drug', 'therapy', 'patient', 'cancer', 'treatment']
                    if not any(term in query.lower() for term in biomedical_terms):
                        search_log["results_per_source"][source_name] = {
                            "skipped": True,
                            "reason": "Not a biomedical query (legacy check)"
                        }
                        logger.info(f"⏭️ Skipping {source_name}: Not a biomedical query")
                        continue

                search_func = search_funcs.get(source_name)
                if search_func:
                    # Optimize query for this specific source
                    optimized_query = query
                    if config.enable_query_reformulation:
                        optimized_query = optimize_query_for_source(query, source_name)
                        if optimized_query != query:
                            logger.info(f"🔧 Optimized query for {source_name}: '{optimized_query}'")

                    logger.info(f"🔎 Searching {source_name}: {description}")
                    results = await search_func(optimized_query, search_limit_per_source)
                    all_candidates.extend(results)

                    # Count papers with PDFs
                    has_pdfs = sum(1 for r in results if r.get("pdf_url") or r.get("open_access_pdf"))

                    search_log["sources_searched"].append(source_name)
                    search_log["results_per_source"][source_name] = {
                        "count": len(results),
                        "has_pdfs": has_pdfs,
                        "sample_title": results[0].get("title") if results else None,
                        "pdf_ratio": f"{has_pdfs}/{len(results)}" if results else "0/0",
                        "optimized_query": optimized_query if optimized_query != query else None
                    }

                    logger.info(f"✅ {source_name}: Found {len(results)} papers ({has_pdfs} with PDFs)")
                else:
                    search_log["results_per_source"][source_name] = {
                        "error": "Search function not available"
                    }
                    logger.warning(f"❌ {source_name}: Search function not available")

            except Exception as e:
                search_log["results_per_source"][source_name] = {
                    "error": str(e),
                    "count": 0
                }
                logger.warning(f"❌ {source_name} search failed: {e}")
        else:
            search_log["results_per_source"][source_name] = {
                "skipped": True,
                "reason": "API not available"
            }
            logger.info(f"⏭️ Skipping {source_name}: API not available")

    search_log["total_candidates"] = len(all_candidates)
    logger.info(f"📊 Total candidates from all sources: {len(all_candidates)}")

    # Sort by PDF availability first, then citation count
    def pdf_priority_score(paper):
        has_pdf = bool(paper.get("pdf_url") or paper.get("open_access_pdf"))
        is_arxiv = paper.get("source") == "arXiv"
        citation_count = paper.get("citation_count", 0)

        # High priority: arXiv papers (almost always downloadable)
        if is_arxiv:
            return (3, citation_count)
        # Medium priority: papers with PDF URLs
        elif has_pdf:
            return (2, citation_count)
        # Low priority: papers without PDF URLs
        else:
            return (1, citation_count)

    all_candidates.sort(key=pdf_priority_score, reverse=True)

    # Remove duplicates by DOI/title
    seen_papers = set()
    unique_candidates = []
    for paper in all_candidates:
        # Create identifier from DOI or title
        identifier = paper.get("doi") or paper.get("title", "").lower().strip()
        if identifier and identifier not in seen_papers:
            seen_papers.add(identifier)
            unique_candidates.append(paper)

    search_log["unique_candidates"] = len(unique_candidates)
    logger.info(f"📄 After deduplication: {len(unique_candidates)} unique papers")

    # Log top candidates for debugging
    if unique_candidates:
        logger.info("🔝 Top candidates by priority:")
        for i, paper in enumerate(unique_candidates[:5]):
            has_pdf = bool(paper.get("pdf_url") or paper.get("open_access_pdf"))
            logger.info(f"  {i+1}. [{paper.get('source', 'Unknown')}] {paper.get('title', 'No title')[:50]}... (PDF: {'✓' if has_pdf else '✗'})")

    # Now try to download papers until we reach the limit
    attempted_downloads = 0
    max_attempts = min(50, len(unique_candidates))  # Cap attempts to avoid infinite loops

    logger.info(f"📥 Starting download attempts (max: {max_attempts})")

    for paper in unique_candidates[:max_attempts]:
        if len(downloadable_papers) >= limit:
            break

        pdf_url = paper.get("pdf_url") or paper.get("open_access_pdf")
        if pdf_url:
            attempted_downloads += 1
            try:
                # Test if PDF is actually downloadable
                download_result = await utils['download_pdf'](pdf_url)
                if download_result.get("success"):
                    paper["download_success"] = True
                    downloadable_papers.append(paper)
                    logger.info(f"✅ Downloaded paper {len(downloadable_papers)}: {paper.get('title', '')[:50]}")
                else:
                    paper["download_error"] = download_result.get("error", "PDF content unavailable")
                    logger.debug(f"❌ Failed to download: {paper.get('title', '')[:50]} - {download_result.get('error', 'Unknown error')}")
            except Exception as e:
                paper["download_error"] = str(e)
                logger.debug(f"❌ Download exception: {e}")
        else:
            paper["download_error"] = "No PDF URL available"

    # Final search summary
    search_log["download_attempts"] = attempted_downloads
    search_log["successful_downloads"] = len(downloadable_papers)
    search_log["success_rate"] = f"{len(downloadable_papers)}/{attempted_downloads}" if attempted_downloads > 0 else "0/0"

    logger.info(f"🎯 SEARCH COMPLETE: Found {len(downloadable_papers)} downloadable papers out of {attempted_downloads} attempts")
    logger.info(f"📈 Search Summary: {json.dumps(search_log, indent=2)}")

    return downloadable_papers