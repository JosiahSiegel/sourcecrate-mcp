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
from .enhanced_classifier import EnhancedTopicClassifier
from .query_intent import QueryIntentDetector
from .bm25_ranker import BM25SourceRanker

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

    # Enhanced analysis using new classification system
    topic_classification = None
    intent_analysis = None
    routing_recommendations = None
    source_rankings = []

    try:
        enhanced_classifier = EnhancedTopicClassifier()
        intent_detector = QueryIntentDetector()
        bm25_ranker = BM25SourceRanker()

        # Perform comprehensive query analysis
        topic_classification = enhanced_classifier.classify_query_enhanced(query)
        intent_analysis = intent_detector.analyze_query(query)
        routing_recommendations = intent_detector.get_routing_recommendations(query)
        source_rankings = bm25_ranker.rank_sources(query)

        logger.info(f"🧠 Enhanced Topic Classification: {topic_classification}")
        logger.info(f"🎯 Query Intent: {intent_analysis.intent.value} (confidence: {intent_analysis.confidence:.2f})")
        logger.info(f"⏰ Temporal Preference: {intent_analysis.temporal_preference.value}")
        logger.info(f"🏆 Top Sources: {[s[0] for s in source_rankings[:5]]}")
    except Exception as e:
        logger.warning(f"❌ Enhanced routing failed, falling back to legacy: {e}")
        # Set defaults for fallback
        topic_classification = {"primary_topic": "Unknown", "confidence": 0.0}
        source_rankings = [('arxiv', 0.8), ('semantic_scholar', 0.7), ('crossref', 0.5)]

    # Legacy topic analysis for backward compatibility
    topic_analysis = None
    if config.enable_topic_detection:
        topic_analysis = get_topic_explanation(query)

    # Initialize comprehensive search logging with enhanced analytics
    search_log = {
        "query": query,
        "limit": limit,
        "timestamp": datetime.now().isoformat(),
        "sources_searched": [],
        "results_per_source": {},
        "api_status": api_status.copy(),
        "search_strategy": "enhanced_smart_downloadable",
        "topic_classification": topic_classification,
        "intent_analysis": {
            "intent": intent_analysis.intent.value if intent_analysis else "unknown",
            "temporal_preference": intent_analysis.temporal_preference.value if intent_analysis else "neutral",
            "confidence": intent_analysis.confidence if intent_analysis else 0.0,
            "complexity": intent_analysis.complexity if intent_analysis else "simple"
        },
        "routing_recommendations": routing_recommendations,
        "source_rankings": source_rankings[:5],  # Top 5 sources
        "legacy_topic_analysis": topic_analysis,
        "total_candidates": 0,
        "unique_candidates": 0,
        "download_attempts": 0,
        "successful_downloads": 0
    }


    # Enhanced strategy using new classification system
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

    # Use BM25 source rankings as primary strategy
    source_priority = []
    for source_name, score in source_rankings:
        if source_name in source_descriptions:
            source_priority.append((source_name, f"{source_descriptions[source_name]} (score: {score:.3f})"))

    # Apply intent-based source preferences as secondary weighting
    intent_preferences = intent_analysis.source_preferences if intent_analysis else {}
    adjusted_priority = []
    for source_name, description in source_priority:
        preference_score = intent_preferences.get(source_name, 0.5)
        adjusted_priority.append((source_name, description, preference_score))

    # Sort by combined BM25 + intent preference scores
    adjusted_priority.sort(key=lambda x: x[2], reverse=True)
    source_priority = [(name, desc) for name, desc, _ in adjusted_priority]

    # Fallback to legacy system if no enhanced rankings available
    if not source_priority:
        if config.enable_topic_detection and topic_analysis:
            recommended_sources = get_recommended_sources(query)
            for source in recommended_sources:
                if source in source_descriptions:
                    source_priority.append((source, source_descriptions[source]))

            all_sources = ['arxiv', 'semantic_scholar', 'crossref', 'pubmed', 'google_scholar', 'core', 'doaj', 'socarxiv', 'osf_preprints']
            for source in all_sources:
                if source not in recommended_sources and source in source_descriptions:
                    source_priority.append((source, f"{source_descriptions[source]} (lower priority)"))
        else:
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

    logger.info(f"🚀 Enhanced source priority: {[s[0] for s in source_priority]}")

    # Search each source for more papers than we need
    search_limit_per_source = max(10, limit * 3)  # Search more to find downloadable ones
    search_log["search_limit_per_source"] = search_limit_per_source

    logger.info(f"🔍 Starting smart search for '{query}' (limit: {limit})")
    logger.info(f"📊 API Status: {json.dumps(api_status, indent=2)}")

    for source_name, description in source_priority:
        if api_status.get(source_name, False):
            try:
                # Enhanced source skipping using new classification system
                skip_source = False
                skip_reason = None

                # Check BM25 score threshold for skipping very low-relevance sources
                source_score = next((score for name, score in source_rankings if name == source_name), 0.0)
                if source_score < 0.1:  # Very low relevance threshold
                    skip_source = True
                    skip_reason = f"Very low BM25 relevance score ({source_score:.3f})"

                # Check intent-based source preferences
                intent_preference = intent_preferences.get(source_name, 0.5)
                if intent_preference < 0.3:  # Low intent-based preference
                    skip_source = True
                    skip_reason = f"Low intent-based preference ({intent_preference:.3f})"

                # Domain-specific skipping logic
                if topic_classification and topic_classification.get('primary_topic') == 'Computer Science':
                    if source_name == 'pubmed' and topic_classification.get('confidence', 0) > 0.7:
                        skip_source = True
                        skip_reason = "Computer Science query, PubMed not relevant"
                elif topic_classification and topic_classification.get('primary_topic') in ['Medicine', 'Biology']:
                    if source_name in ['socarxiv'] and topic_classification.get('confidence', 0) > 0.7:
                        skip_source = True
                        skip_reason = f"Biomedical query, {source_name} not relevant"

                # Legacy topic-based skipping (fallback)
                if config.enable_topic_detection and should_skip_source_for_topic(source_name, query):
                    skip_source = True
                    skip_reason = "Legacy topic-based skip"

                # Legacy PubMed biomedical check (for backward compatibility)
                if source_name == 'pubmed' and not config.enable_topic_detection:
                    biomedical_terms = ['gene', 'protein', 'disease', 'medical', 'clinical', 'drug', 'therapy', 'patient', 'cancer', 'treatment']
                    if not any(term in query.lower() for term in biomedical_terms):
                        skip_source = True
                        skip_reason = "Legacy biomedical check failed"

                if skip_source:
                    search_log["results_per_source"][source_name] = {
                        "skipped": True,
                        "reason": skip_reason,
                        "bm25_score": source_score,
                        "intent_preference": intent_preference
                    }
                    logger.info(f"⏭️ Skipping {source_name}: {skip_reason}")
                    continue

                search_func = search_funcs.get(source_name)
                if search_func:
                    # Enhanced query optimization using routing recommendations
                    optimized_query = query

                    # Use query expansions from intent analysis
                    if routing_recommendations and routing_recommendations.get('query_expansions'):
                        # Select best expansion for this source based on intent and temporal preference
                        expansions = routing_recommendations['query_expansions']
                        if expansions and intent_analysis and intent_analysis.temporal_preference.value == 'recent':
                            # For recent queries, try temporal expansions first
                            temporal_expansions = [exp for exp in expansions if any(term in exp.lower() for term in ['recent', 'latest', '2024', '2025'])]
                            if temporal_expansions:
                                optimized_query = temporal_expansions[0]
                        elif expansions and intent_analysis and intent_analysis.intent.value == 'survey_review':
                            # For review queries, try review-focused expansions
                            review_expansions = [exp for exp in expansions if any(term in exp.lower() for term in ['review', 'survey', 'state of the art'])]
                            if review_expansions:
                                optimized_query = review_expansions[0]
                        elif expansions:
                            # Use first expansion as fallback
                            optimized_query = expansions[0]

                    # Legacy query optimization (fallback)
                    if config.enable_query_reformulation and optimized_query == query:
                        optimized_query = optimize_query_for_source(query, source_name)

                    if optimized_query != query:
                        logger.info(f"🔧 Enhanced query optimization for {source_name}: '{optimized_query}'")

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