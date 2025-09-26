"""
Smart search functionality that prioritizes downloadable papers.
"""

import logging
from typing import Dict, List, Any

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

    # Strategy: Search ALL sources in parallel to maximize PDF availability
    source_priority = [
        ('arxiv', 'arXiv has highest PDF availability'),
        ('semantic_scholar', 'Semantic Scholar often has open access PDFs'),
        ('crossref', 'CrossRef comprehensive but mostly paywalled'),
        ('pubmed', 'PubMed for biomedical open access'),
        ('google_scholar', 'Google Scholar fallback')
    ]

    # Search each source for more papers than we need
    search_limit_per_source = max(10, limit * 3)  # Search more to find downloadable ones

    for source_name, description in source_priority:
        if api_status.get(source_name, False):
            try:
                if source_name == 'pubmed':
                    # Only search PubMed for biomedical queries
                    biomedical_terms = ['gene', 'protein', 'disease', 'medical', 'clinical', 'drug', 'therapy', 'patient', 'cancer', 'treatment']
                    if not any(term in query.lower() for term in biomedical_terms):
                        continue

                search_func = search_funcs.get(source_name)
                if search_func:
                    results = await search_func(query, search_limit_per_source)
                    all_candidates.extend(results)
                    logger.info(f"Found {len(results)} papers from {source_name}")
            except Exception as e:
                logger.warning(f"{source_name} search failed: {e}")

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

    logger.info(f"After deduplication: {len(unique_candidates)} unique papers")

    # Now try to download papers until we reach the limit
    attempted_downloads = 0
    max_attempts = min(50, len(unique_candidates))  # Cap attempts to avoid infinite loops

    for paper in unique_candidates[:max_attempts]:
        if len(downloadable_papers) >= limit:
            break

        pdf_url = paper.get("pdf_url") or paper.get("open_access_pdf")
        if pdf_url:
            attempted_downloads += 1
            try:
                # Test if PDF is actually downloadable
                pdf_content = await utils['download_pdf'](pdf_url)
                if pdf_content:
                    paper["download_success"] = True
                    downloadable_papers.append(paper)
                    logger.info(f"✓ Downloaded paper {len(downloadable_papers)}: {paper.get('title', '')[:50]}")
                else:
                    paper["download_error"] = "PDF content unavailable"
                    logger.debug(f"✗ Failed to download: {paper.get('title', '')[:50]}")
            except Exception as e:
                paper["download_error"] = str(e)
                logger.debug(f"✗ Download error: {e}")
        else:
            paper["download_error"] = "No PDF URL available"

    logger.info(f"Successfully found {len(downloadable_papers)} downloadable papers out of {attempted_downloads} attempts")

    return downloadable_papers