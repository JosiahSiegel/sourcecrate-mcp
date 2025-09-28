"""
Smart search functionality that prioritizes downloadable papers.
"""

import json
import logging
from datetime import datetime
from typing import Any

from .bm25_ranker import BM25SourceRanker
from .enhanced_classifier import EnhancedTopicClassifier
from .intelligent_error_handler import error_handler
from .query_intent import QueryIntentDetector

logger = logging.getLogger(__name__)


async def smart_downloadable_search(
    query: str,
    limit: int,
    search_funcs: dict[str, Any],
    utils: dict[str, Any],
    api_status: dict[str, bool],
    force_category: str | None = None,
    metadata_only: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Smart search that prioritizes sources with downloadable PDFs and only counts
    successfully downloadable papers toward the limit.

    Args:
        query: Search query
        limit: Number of downloadable papers to find
        search_funcs: Dictionary of search functions by source
        utils: Dictionary of utility functions
        api_status: API availability status
        force_category: Optional category to force routing (preprints, journals, open_access, historical)
        metadata_only: If True, skip PDF download testing and return metadata regardless of download success

    Returns:
        List of papers that were successfully downloaded (or metadata if metadata_only=True)
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
        logger.info(
            f"🎯 Query Intent: {intent_analysis.intent.value} (confidence: {intent_analysis.confidence:.2f})"
        )
        logger.info(
            f"⏰ Temporal Preference: {intent_analysis.temporal_preference.value}"
        )
        logger.info(f"🏆 Top Sources: {[s[0] for s in source_rankings[:5]]}")
    except Exception as e:
        logger.warning(f"❌ Enhanced routing failed, falling back to legacy: {e}")
        # Set defaults for fallback
        if topic_classification is None:
            topic_classification = {"primary_topic": "Unknown", "confidence": 0.0}  # type: ignore
        source_rankings = [("arxiv", 0.8), ("semantic_scholar", 0.7), ("crossref", 0.5)]

    # Enhanced routing has replaced legacy topic detection

    # Initialize comprehensive search logging with enhanced analytics
    search_log: dict[str, Any] = {
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
            "temporal_preference": (
                intent_analysis.temporal_preference.value
                if intent_analysis
                else "neutral"
            ),
            "confidence": intent_analysis.confidence if intent_analysis else 0.0,
            "complexity": intent_analysis.complexity if intent_analysis else "simple",
        },
        "routing_recommendations": routing_recommendations,
        "source_rankings": source_rankings[:5],  # Top 5 sources
        "total_candidates": 0,
        "unique_candidates": 0,
        "download_attempts": 0,
        "successful_downloads": 0,
    }

    # Enhanced strategy using new classification system
    source_descriptions = {
        "arxiv": "arXiv has highest PDF availability",
        "semantic_scholar": "Semantic Scholar often has open access PDFs",
        "crossref": "CrossRef comprehensive but mostly paywalled",
        "pubmed": "PubMed for biomedical literature",
        "pubmed_central": "PMC for full-text medical papers",
        "clinicaltrials": "ClinicalTrials.gov for trial data",
        "google_scholar": "Google Scholar fallback",
        "core": "CORE open access repository",
        "doaj": "DOAJ open access journals",
        "socarxiv": "SocArXiv social science preprints",
        "osf_preprints": "OSF preprints across disciplines",
        "europe_pmc": "Europe PMC biomedical database",
        "internet_archive": "Internet Archive historical documents",
    }

    # Get ALL available sources from the configuration
    all_available_sources = [
        name for name in search_funcs.keys() if api_status.get(name, True)
    ]

    # Create comprehensive source priority list ensuring ALL sources are included
    source_priority_dict = {}

    # First: Process BM25 rankings for sources that exist in both BM25 and config
    for source_name, score in source_rankings:
        if source_name in all_available_sources:
            description = source_descriptions.get(source_name, f"Source: {source_name}")
            source_priority_dict[source_name] = (
                f"{description} (BM25: {score:.3f})",
                score,
            )

    # Second: Add all remaining configured sources with default priority
    for source_name in all_available_sources:
        if source_name not in source_priority_dict:
            description = source_descriptions.get(
                source_name, f"Custom source: {source_name}"
            )
            # Give default sources a neutral score so they're included but ranked lower
            source_priority_dict[source_name] = (f"{description} (configured)", 0.1)

    # Apply intent-based preferences and create final priority list
    intent_preferences = intent_analysis.source_preferences if intent_analysis else {}
    adjusted_priority = []

    for source_name, (description, base_score) in source_priority_dict.items():
        preference_score = intent_preferences.get(source_name, 0.5)
        # Combine BM25 score with intent preference
        final_score = base_score * 0.7 + preference_score * 0.3
        adjusted_priority.append((source_name, description, final_score))

    # Sort by final combined scores (highest first)
    adjusted_priority.sort(key=lambda x: x[2], reverse=True)
    source_priority = [(name, desc) for name, desc, _ in adjusted_priority]

    # Force category routing if specified
    if force_category:
        category_sources = {
            "preprints": ["arxiv", "socarxiv", "osf_preprints"],
            "journals": ["crossref", "pubmed", "doaj", "europe_pmc"],
            "open_access": [
                "core",
                "doaj",
                "arxiv",
                "pubmed_central",
                "socarxiv",
                "osf_preprints",
                "europe_pmc",
            ],
            "historical": ["core", "crossref", "internet_archive"],
            "recent": [
                "arxiv",
                "semantic_scholar",
                "pubmed_central",
                "clinicaltrials",
                "osf_preprints",
                "europe_pmc",
            ],
            "medical": ["pubmed", "pubmed_central", "clinicaltrials", "europe_pmc"],
        }

        if force_category in category_sources:
            # Filter to available sources in this category
            forced_sources = [
                s for s in category_sources[force_category] if api_status.get(s, False)
            ]
            if forced_sources:
                source_priority = [
                    (s, f"{source_descriptions[s]} (FORCED: {force_category})")
                    for s in forced_sources
                ]
                logger.info(
                    f"🎯 FORCED CATEGORY '{force_category}': Using sources {forced_sources}"
                )
            else:
                logger.warning(
                    f"❌ No available sources for category '{force_category}'"
                )
        else:
            available_categories = list(category_sources.keys())
            logger.warning(
                f"❌ Unknown category '{force_category}'. Available: {available_categories}"
            )
            # Continue with normal routing

    logger.info(f"🚀 Source priority: {[s[0] for s in source_priority]}")

    # Search each source for more papers than we need
    search_limit_per_source = max(
        10, limit * 3
    )  # Search more to find downloadable ones
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
                source_score = next(
                    (score for name, score in source_rankings if name == source_name),
                    0.0,
                )
                if source_score < 0.1:  # Very low relevance threshold
                    skip_source = True
                    skip_reason = f"Very low BM25 relevance score ({source_score:.3f})"

                # Check intent-based source preferences
                intent_preference = intent_preferences.get(source_name, 0.5)
                if intent_preference < 0.3:  # Low intent-based preference
                    skip_source = True
                    skip_reason = (
                        f"Low intent-based preference ({intent_preference:.3f})"
                    )

                # Domain-specific skipping logic
                if (
                    topic_classification
                    and topic_classification.get("primary_topic") == "Computer Science"
                ):
                    if (
                        source_name == "pubmed"
                        and topic_classification.get("confidence", 0) > 0.7
                    ):
                        skip_source = True
                        skip_reason = "Computer Science query, PubMed not relevant"
                elif topic_classification and topic_classification.get(
                    "primary_topic"
                ) in ["Medicine", "Biology"]:
                    if (
                        source_name in ["socarxiv"]
                        and topic_classification.get("confidence", 0) > 0.7
                    ):
                        skip_source = True
                        skip_reason = f"Biomedical query, {source_name} not relevant"

                # Enhanced routing handles all source selection intelligently

                if skip_source:
                    search_log["results_per_source"][source_name] = {
                        "skipped": True,
                        "reason": skip_reason,
                        "bm25_score": source_score,
                        "intent_preference": intent_preference,
                    }
                    logger.info(f"⏭️ Skipping {source_name}: {skip_reason}")
                    continue

                search_func = search_funcs.get(source_name)
                if search_func:
                    # Enhanced query optimization using routing recommendations
                    optimized_query = query

                    # Use query expansions from intent analysis
                    if routing_recommendations and routing_recommendations.get(
                        "query_expansions"
                    ):
                        # Select best expansion for this source based on intent and temporal preference
                        expansions = routing_recommendations["query_expansions"]
                        if (
                            expansions
                            and intent_analysis
                            and intent_analysis.temporal_preference.value == "recent"
                        ):
                            # For recent queries, try temporal expansions first
                            temporal_expansions = [
                                exp
                                for exp in expansions
                                if any(
                                    term in exp.lower()
                                    for term in ["recent", "latest", "2024", "2025"]
                                )
                            ]
                            if temporal_expansions:
                                optimized_query = temporal_expansions[0]
                        elif (
                            expansions
                            and intent_analysis
                            and intent_analysis.intent.value == "survey_review"
                        ):
                            # For review queries, try review-focused expansions
                            review_expansions = [
                                exp
                                for exp in expansions
                                if any(
                                    term in exp.lower()
                                    for term in ["review", "survey", "state of the art"]
                                )
                            ]
                            if review_expansions:
                                optimized_query = review_expansions[0]
                        elif expansions:
                            # Use first expansion as fallback
                            optimized_query = expansions[0]

                    # Enhanced routing provides intelligent query optimization

                    if optimized_query != query:
                        logger.info(
                            f"🔧 Enhanced query optimization for {source_name}: '{optimized_query}'"
                        )

                    logger.info(f"🔎 Searching {source_name}: {description}")
                    results = await search_func(
                        optimized_query, search_limit_per_source
                    )
                    all_candidates.extend(results)

                    # Count papers with PDFs
                    has_pdfs = sum(
                        1
                        for r in results
                        if r.get("pdf_url") or r.get("open_access_pdf")
                    )

                    search_log["sources_searched"].append(source_name)
                    search_log["results_per_source"][source_name] = {
                        "count": len(results),
                        "has_pdfs": has_pdfs,
                        "sample_title": results[0].get("title") if results else None,
                        "pdf_ratio": f"{has_pdfs}/{len(results)}" if results else "0/0",
                        "optimized_query": (
                            optimized_query if optimized_query != query else None
                        ),
                    }

                    logger.info(
                        f"✅ {source_name}: Found {len(results)} papers ({has_pdfs} with PDFs)"
                    )
                else:
                    search_log["results_per_source"][source_name] = {
                        "error": "Search function not available"
                    }
                    logger.warning(f"❌ {source_name}: Search function not available")

            except Exception as e:
                search_log["results_per_source"][source_name] = {
                    "error": str(e),
                    "count": 0,
                }
                logger.warning(f"❌ {source_name} search failed: {e}")
        else:
            search_log["results_per_source"][source_name] = {
                "skipped": True,
                "reason": "API not available",
            }
            logger.info(f"⏭️ Skipping {source_name}: API not available")

    search_log["total_candidates"] = len(all_candidates)
    logger.info(f"📊 Total candidates from all sources: {len(all_candidates)}")

    # Sort by PDF availability first, then citation count
    def pdf_priority_score(paper: dict[str, Any]) -> tuple[int, int]:
        has_pdf = bool(paper.get("pdf_url") or paper.get("open_access_pdf"))
        is_arxiv = paper.get("source") == "arXiv"

        # Safely convert citation_count to integer
        citation_count = paper.get("citation_count", 0)
        try:
            citation_count = int(citation_count) if citation_count is not None else 0
        except (ValueError, TypeError):
            citation_count = 0

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
            logger.info(
                f"  {i+1}. [{paper.get('source', 'Unknown')}] {paper.get('title', 'No title')[:50]}... (PDF: {'✓' if has_pdf else '✗'})"
            )

    # Handle metadata-only mode vs download testing
    if metadata_only:
        # For metadata-only mode (browse_papers), return papers without download testing
        logger.info(
            f"📄 Metadata-only mode: Returning top {limit} papers without download testing"
        )
        downloadable_papers = unique_candidates[:limit]
        attempted_downloads = 0

        # Mark metadata-only papers for distinction
        for paper in downloadable_papers:
            paper["metadata_only"] = True
    else:
        # Original download testing logic for get_papers/download_papers
        attempted_downloads = 0
        max_attempts = min(
            50, len(unique_candidates)
        )  # Cap attempts to avoid infinite loops

        logger.info(f"📥 Starting download attempts (max: {max_attempts})")

        for paper in unique_candidates[:max_attempts]:
            if len(downloadable_papers) >= limit:
                break

            pdf_url = paper.get("pdf_url") or paper.get("open_access_pdf")
            if pdf_url:
                attempted_downloads += 1
                try:
                    # Test if PDF is actually downloadable using HEAD request (no download)
                    import httpx

                    async with httpx.AsyncClient(
                        timeout=30.0, follow_redirects=True
                    ) as client:
                        response = await client.head(pdf_url)
                        if response.status_code == 200:
                            paper["download_success"] = True
                            downloadable_papers.append(paper)
                            logger.info(
                                f"✅ Verified downloadable paper {len(downloadable_papers)}: {paper.get('title', '')[:50]}"
                            )
                        else:
                            paper["download_error"] = (
                                f"PDF not accessible: HTTP {response.status_code}"
                            )
                            logger.debug(
                                f"❌ PDF not accessible: {paper.get('title', '')[:50]} - HTTP {response.status_code}"
                            )
                except Exception as e:
                    paper["download_error"] = str(e)
                    logger.debug(f"❌ Download exception: {e}")
            else:
                paper["download_error"] = "No PDF URL available"

    # Final search summary
    search_log["download_attempts"] = attempted_downloads
    search_log["successful_downloads"] = len(downloadable_papers)
    search_log["success_rate"] = (
        f"{len(downloadable_papers)}/{attempted_downloads}"
        if attempted_downloads > 0
        else "0/0"
    )

    # Intelligent Fallback Strategy: If no results found, try all sources without category restriction
    if len(downloadable_papers) == 0 and force_category is not None:
        logger.info(
            "🔄 INTELLIGENT FALLBACK: No papers found, retrying with all available sources..."
        )
        search_log["fallback_triggered"] = True
        search_log["fallback_reason"] = "Primary search returned 0 results"

        try:
            # Recursive call without category restriction (fallback to all sources)
            fallback_results, fallback_log = await smart_downloadable_search(
                query=query,
                limit=limit,
                search_funcs=search_funcs,
                utils=utils,
                api_status=api_status,
                force_category=None,
            )

            if len(fallback_results) > 0:
                search_log["fallback_success"] = True
                search_log["fallback_results_count"] = len(fallback_results)
                logger.info(
                    f"✅ FALLBACK SUCCESS: Found {len(fallback_results)} papers using all available sources"
                )

                # Add fallback metadata to each result
                for paper in fallback_results:
                    paper["_fallback_used"] = True
                    paper["_original_category"] = force_category or "smart_routing"

                downloadable_papers = fallback_results
            else:
                search_log["fallback_success"] = False
                logger.info(
                    "❌ FALLBACK FAILED: No papers found even with all available sources"
                )

                # Generate intelligent error suggestions when even fallback fails
                error_info = error_handler.generate_error_message(
                    query=query,
                    sources_searched=search_log["sources_searched"],
                    fallback_used=True,
                )
                search_log["intelligent_error_suggestions"] = error_info
                logger.info(
                    f"💡 Generated {len(error_info['suggestions'])} intelligent suggestions for failed search"
                )

        except Exception as e:
            search_log["fallback_error"] = str(e)
            logger.warning(f"❌ FALLBACK ERROR: {e}")
    elif len(downloadable_papers) == 0:
        # No fallback used but still no results - generate suggestions
        error_info = error_handler.generate_error_message(
            query=query,
            sources_searched=search_log["sources_searched"],
            fallback_used=False,
        )
        search_log["intelligent_error_suggestions"] = error_info
        logger.info(
            f"💡 Generated {len(error_info['suggestions'])} intelligent suggestions for failed search"
        )

    logger.info(
        f"🎯 SEARCH COMPLETE: Found {len(downloadable_papers)} downloadable papers out of {attempted_downloads} attempts"
    )
    logger.info(f"📈 Search Summary: {json.dumps(search_log, indent=2)}")

    # Return both papers and search metadata (including error suggestions)
    return downloadable_papers, search_log
