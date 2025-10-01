"""
Smart search functionality that prioritizes downloadable papers.
"""

import json
import logging
from datetime import datetime
from typing import Any

from ..config import get_search_service
from .bm25_ranker import BM25SourceRanker
from .enhanced_classifier import EnhancedTopicClassifier
from .intelligent_error_handler import error_handler
from .query_intent import QueryIntentDetector
from .relevance_scorer import relevance_scorer

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
    downloadable_papers: list[dict] = []
    all_candidates = []

    # Check for empty search functions using shared utility
    from paperez_mcp.utils.search_helpers import check_empty_search_functions

    if check_empty_search_functions(search_funcs, "downloadable search"):
        return [], {
            "query": query,
            "error": "No search functions available",
            "total_candidates": 0,
        }

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
        "core": "CORE open access repository",
        "doaj": "DOAJ open access journals",
        "socarxiv": "SocArXiv social science preprints",
        "osf_preprints": "OSF preprints across disciplines",
        "europe_pmc": "Europe PMC biomedical database",
        "internet_archive": "Internet Archive historical documents",
        "openalex": "OpenAlex comprehensive multidisciplinary catalog",
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

    # Track priority and additional sources for conditional cascade
    priority_sources_list = []
    additional_sources_list = []

    # When NOT using force_category, split sources by relevance score for cascade
    # This ensures lower-relevance sources can serve as fallback
    if not force_category:
        # Split sources based on final relevance scores
        relevance_threshold = 0.3  # Sources below this go to fallback list

        for source_name, _description, final_score in adjusted_priority:
            if final_score >= relevance_threshold:
                # High relevance - search first
                priority_sources_list.append(source_name)
            else:
                # Lower relevance - use as fallback for cascade
                additional_sources_list.append(source_name)

        logger.info(
            f"📊 Relevance-based split: {len(priority_sources_list)} priority sources "
            f"(score ≥ {relevance_threshold}), {len(additional_sources_list)} fallback sources"
        )
        logger.debug(f"  Priority: {priority_sources_list[:5]}")
        logger.debug(f"  Fallback: {additional_sources_list[:5]}")

    # Priority-based category routing if specified (using shared utility)
    if force_category:
        from paperez_mcp.utils.category_filter import resolve_category_sources

        category_source_list = resolve_category_sources(force_category)

        if category_source_list:
            # Get priority sources that are available
            priority_sources = [
                s for s in category_source_list if api_status.get(s, False)
            ]

            # Get remaining sources not in the priority category
            remaining_sources = [
                s
                for s in all_available_sources
                if s not in priority_sources and api_status.get(s, False)
            ]

            if priority_sources:
                # Create priority list: category sources first, then others
                source_priority = []

                # Add priority sources with high priority descriptions
                for s in priority_sources:
                    description = source_descriptions.get(s, f"Source: {s}")
                    source_priority.append(
                        (s, f"{description} (PRIORITY: {force_category})")
                    )
                    priority_sources_list.append(s)  # Track for conditional cascade

                # Add remaining sources as backup (BUT WON'T SEARCH UNLESS NEEDED)
                for s in remaining_sources:
                    description = source_descriptions.get(s, f"Source: {s}")
                    source_priority.append((s, f"{description} (additional)"))
                    additional_sources_list.append(s)  # Track for conditional cascade

                logger.info(
                    f"🎯 Category '{force_category}': Prioritizing {priority_sources}, additional sources available if needed: {remaining_sources[:5]}..."
                )
            else:
                logger.warning(
                    f"❌ No available sources for category '{force_category}', using all sources"
                )
                # Continue with normal routing if no priority sources available
        else:
            # Category has no sources - return empty results with error
            # Do NOT fall back to all sources (this would violate force_category intent)
            logger.error(
                f"❌ Category '{force_category}' has no sources configured. "
                f"Cannot search with empty category. Returning 0 results."
            )
            # Set source_priority to empty list to cause 0 results
            source_priority = []

    logger.info(f"🚀 Source priority: {[s[0] for s in source_priority]}")

    # Search each source for more papers than we need
    search_limit_per_source = max(
        10, limit * 3
    )  # Search more to find downloadable ones
    search_log["search_limit_per_source"] = search_limit_per_source

    logger.info(f"🔍 Starting smart search for '{query}' (limit: {limit})")
    logger.info(f"📊 API Status: {json.dumps(api_status.copy(), indent=2)}")

    # Validate and normalize api_status using shared utility
    from paperez_mcp.utils.search_helpers import validate_api_status

    api_status = validate_api_status(api_status, search_funcs)

    # First pass: Check which sources would be skipped by BM25 and other criteria
    available_sources = [
        (name, desc) for name, desc in source_priority if api_status.get(name, False)
    ]
    sources_to_skip = []
    sources_to_search = []

    for source_name, description in available_sources:
        # When force_category is set, skip BM25/intent filtering for category sources
        # This ensures category sources are always searched without scoring-based skipping
        if force_category and source_name in priority_sources_list:
            # Category source - always search, no filtering
            sources_to_search.append((source_name, description))
            logger.debug(
                f"🎯 Force category: {source_name} will be searched (category source, skipping BM25/intent filters)"
            )
            continue

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
            skip_reason = f"Low intent-based preference ({intent_preference:.3f})"

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
        elif topic_classification and topic_classification.get("primary_topic") in [
            "Medicine",
            "Biology",
        ]:
            if (
                source_name in ["socarxiv"]
                and topic_classification.get("confidence", 0) > 0.7
            ):
                skip_source = True
                skip_reason = f"Biomedical query, {source_name} not relevant"

        if skip_source:
            sources_to_skip.append(
                (source_name, skip_reason, source_score, intent_preference)
            )
        else:
            sources_to_search.append((source_name, description))

    # Fallback mechanism using shared utility
    from paperez_mcp.utils.search_helpers import apply_source_fallback

    # When force_category is set, fallback should ONLY use category sources
    # Otherwise, fallback can use all available sources
    fallback_pool = available_sources
    if force_category and priority_sources_list:
        # Restrict fallback to category sources only
        fallback_pool = [
            (name, desc)
            for name, desc in available_sources
            if name in priority_sources_list
        ]
        logger.debug(
            f"🎯 Force category: restricting fallback pool to {len(fallback_pool)} category sources"
        )

    sources_to_search = apply_source_fallback(
        sources_to_search,
        fallback_pool,
        fallback_count=3,
        reason="BM25/intent filtering excluded all sources",
    )

    # Update skip list to remove sources that were added via fallback
    if len(sources_to_search) > 0 and len(available_sources) > 0:
        sources_to_search_names = {name for name, _ in sources_to_search}
        sources_to_skip = [
            (name, reason, score, pref)
            for name, reason, score, pref in sources_to_skip
            if name not in sources_to_search_names
        ]

    # Log skipped sources
    for source_name, skip_reason, source_score, intent_preference in sources_to_skip:
        search_log["results_per_source"][source_name] = {
            "skipped": True,
            "reason": skip_reason,
            "bm25_score": source_score,
            "intent_preference": intent_preference,
        }
        logger.info(f"⏭️ Skipping {source_name}: {skip_reason}")

    # Split sources into priority and additional for conditional cascade
    priority_sources_to_search = []
    additional_sources_to_search = []

    for source_name, description in sources_to_search:
        if source_name in priority_sources_list:
            priority_sources_to_search.append((source_name, description))
        elif source_name in additional_sources_list:
            additional_sources_to_search.append((source_name, description))
        else:
            # Edge case: Source not in either list (should be rare now)
            # This can happen if a source was added after BM25 ranking
            logger.warning(
                f"⚠️ Source {source_name} not in priority or additional lists, defaulting to priority"
            )
            priority_sources_to_search.append((source_name, description))

    # Phase 1: Search priority sources first
    logger.info(
        f"🎯 Phase 1: Searching {len(priority_sources_to_search)} priority sources"
    )
    for source_name, description in priority_sources_to_search:
        try:
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

                # Apply source-specific query transformations for author searches
                if intent_analysis and intent_analysis.is_author_search:
                    try:
                        search_service = get_search_service()
                        source_config = (
                            search_service.source_registry.get_source_config(
                                source_name
                            )
                        )
                        if (
                            source_config
                            and source_config.capabilities
                            and source_config.capabilities.author_search_transform
                        ):
                            # Apply author search transformation
                            transformed_query = source_config.capabilities.author_search_transform.format(
                                query=optimized_query
                            )
                            logger.info(
                                f"👤 Author search transformation for {source_name}: '{optimized_query}' → '{transformed_query}'"
                            )
                            optimized_query = transformed_query
                    except Exception as e:
                        logger.debug(
                            f"Could not apply author search transformation for {source_name}: {e}"
                        )

                if optimized_query != query:
                    logger.info(
                        f"🔧 Enhanced query optimization for {source_name}: '{optimized_query}'"
                    )

                logger.info(f"🔎 Searching {source_name}: {description}")
                results = await search_func(optimized_query, search_limit_per_source)
                all_candidates.extend(results)

                # Count papers with PDFs
                has_pdfs = sum(
                    1 for r in results if r.get("pdf_url") or r.get("open_access_pdf")
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

    # Cascade through additional sources for comprehensive coverage
    # Special handling for force_category:
    # - If category sources found results: respect explicit restriction, skip cascade
    # - If category sources found 0 results: cascade to all sources for comprehensive coverage
    used_fallback = False
    if additional_sources_to_search and not force_category:
        logger.info(
            f"🔄 Cascading to {len(additional_sources_to_search)} additional sources "
            f"(relevance-based cascade) to ensure comprehensive coverage..."
        )
        used_fallback = True
    elif additional_sources_to_search and force_category and len(all_candidates) == 0:
        # Category sources returned 0 results - cascade to all sources
        logger.warning(
            f"⚠️  Category '{force_category}' returned 0 results from {len(priority_sources_to_search)} sources. "
            f"Cascading to {len(additional_sources_to_search)} additional sources for comprehensive coverage..."
        )
        used_fallback = True
    elif additional_sources_to_search and force_category:
        logger.info(
            f"⏭️  Skipping {len(additional_sources_to_search)} non-category sources "
            f"(force_category='{force_category}' found {len(all_candidates)} results - respecting explicit category restriction)"
        )

    # Phase 2: Search all additional sources exhaustively (only if cascading)
    # Stopping happens naturally at download loop when limit is reached
    if used_fallback:
        for source_name, description in additional_sources_to_search:
            try:
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

                    logger.info(f"🔎 [Fallback] Searching {source_name}: {description}")
                    results = await search_func(
                        optimized_query, search_limit_per_source
                    )

                    # Mark papers as coming from fallback expansion
                    for paper in results:
                        paper["_fallback_used"] = True
                        paper["_original_category"] = force_category

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
                        "fallback": True,
                    }

                    logger.info(
                        f"✅ [Fallback] {source_name}: Found {len(results)} papers ({has_pdfs} with PDFs)"
                    )
                else:
                    search_log["results_per_source"][source_name] = {
                        "error": "Search function not available",
                        "fallback": True,
                    }
                    logger.warning(
                        f"❌ [Fallback] {source_name}: Search function not available"
                    )

            except Exception as e:
                search_log["results_per_source"][source_name] = {
                    "error": str(e),
                    "count": 0,
                    "fallback": True,
                }
                logger.warning(f"❌ [Fallback] {source_name} search failed: {e}")

    search_log["total_candidates"] = len(all_candidates)
    search_log["used_fallback"] = used_fallback
    logger.info(f"📊 Total candidates from all sources: {len(all_candidates)}")

    # Sort by PDF availability using capability-based priority
    def pdf_priority_score(paper: dict[str, Any]) -> tuple[int, int]:
        has_pdf = bool(paper.get("pdf_url") or paper.get("open_access_pdf"))

        # Get source capabilities for priority determination
        source_name = paper.get("source", "")
        try:
            from paperez_mcp.config import get_current_config

            config = get_current_config()
            source_config = config.sources.get(source_name)
        except Exception:
            # If config unavailable, use basic priority
            source_config = None

        # Safely convert citation_count to integer
        citation_count = paper.get("citation_count", 0)
        try:
            citation_count = int(citation_count) if citation_count is not None else 0
        except (ValueError, TypeError):
            citation_count = 0

        # Determine priority based on source capabilities
        if source_config and source_config.enabled and source_config.capabilities:
            capabilities = source_config.capabilities

            # Highest priority: Sources with high PDF availability (like arXiv, PMC)
            if capabilities.high_pdf_availability:
                return (3, citation_count)
            # Medium priority: Papers with confirmed PDF URLs
            elif has_pdf:
                return (2, citation_count)
            # Lower priority: Papers without PDF URLs
            else:
                return (1, citation_count)
        else:
            # Unknown source - prioritize only if has PDF
            return (2 if has_pdf else 1, citation_count)

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

    # Apply relevance scoring and re-rank papers
    if unique_candidates:
        logger.info("🧠 Applying relevance scoring to improve result ranking...")
        # Use author search field weights if this is an author query
        field_weights_profile = (
            intent_analysis.field_weights_profile if intent_analysis else "default"
        )
        if field_weights_profile == "author_search":
            logger.info(
                "👤 Using author-focused relevance scoring (authors: 70%, title: 15%)"
            )
        ranked_candidates = relevance_scorer.rank_papers(
            query, unique_candidates, field_weights_profile
        )

        # Filter out very low relevance papers (optional)
        # Only apply aggressive filtering if we have plenty of results
        if len(ranked_candidates) >= limit * 3:
            filtered_candidates = relevance_scorer.filter_low_relevance(
                ranked_candidates, min_threshold=0.05
            )
            logger.info(
                f"📊 Relevance filtering: {len(ranked_candidates)} → {len(filtered_candidates)} papers"
            )
        else:
            # Keep all results when we have few candidates
            filtered_candidates = ranked_candidates
            logger.info(
                f"⚠️  Few candidates ({len(ranked_candidates)}), skipping relevance filter to avoid 0 results"
            )

        # Update the candidates list
        unique_candidates = filtered_candidates

        # Log top candidates after relevance ranking
        logger.info("🔝 Top candidates by relevance score:")
        for i, paper in enumerate(unique_candidates[:5]):
            has_pdf = bool(paper.get("pdf_url") or paper.get("open_access_pdf"))
            relevance = paper.get("relevance_score", 0.0)
            logger.info(
                f"  {i+1}. [{paper.get('source', 'Unknown')}] {paper.get('title', 'No title')[:50]}... (PDF: {'✓' if has_pdf else '✗'}, Relevance: {relevance:.3f})"
            )

    # Handle metadata-only mode vs download testing
    if metadata_only:
        # For metadata-only mode (browse_papers), filter to only include papers with PDF URLs
        # This ensures consistency with download_papers behavior
        papers_with_pdfs = [
            p for p in unique_candidates if p.get("pdf_url") or p.get("open_access_pdf")
        ]

        papers_without_pdfs = len(unique_candidates) - len(papers_with_pdfs)
        logger.info(
            f"📄 Metadata-only mode: Filtered {len(unique_candidates)} candidates → {len(papers_with_pdfs)} with PDFs (filtered out {papers_without_pdfs} without PDFs)"
        )

        downloadable_papers = papers_with_pdfs[:limit]
        logger.info(
            f"📄 Returning top {len(downloadable_papers)} papers with PDF URLs (limit: {limit})"
        )
        attempted_downloads = 0

        # Mark metadata-only papers for distinction
        for paper in downloadable_papers:
            paper["metadata_only"] = True
    else:
        # Original download testing logic for get_papers/download_papers
        attempted_downloads = 0
        # Over-fetch with buffer to account for download failures (403/404 errors common)
        buffer_multiplier = (
            2.5  # Search for 2.5x limit to account for ~60% download failure rate
        )
        buffered_limit = int(limit * buffer_multiplier)
        max_attempts = min(
            100, len(unique_candidates)
        )  # Increased cap to support buffer strategy

        logger.info(
            f"📥 Starting download attempts with buffer strategy (target: {limit}, buffer: {buffered_limit}, max attempts: {max_attempts})"
        )
        logger.info(
            "💡 Over-fetching to account for potential 403/404 errors and access restrictions"
        )

        for paper in unique_candidates[:max_attempts]:
            # Over-fetch with buffer to handle download failures
            if len(downloadable_papers) >= buffered_limit:
                logger.info(
                    f"📦 Reached buffer limit ({buffered_limit}), stopping search phase"
                )
                break

            pdf_url = paper.get("pdf_url") or paper.get("open_access_pdf")
            if pdf_url:
                attempted_downloads += 1
                try:
                    # Accept all PDF URLs returned by search sources
                    # download_success will be set by paper_processor after actual download
                    paper["download_note"] = (
                        "PDF URL from trusted search source - skipping HEAD verification"
                    )
                    downloadable_papers.append(paper)
                    logger.info(
                        f"✅ Accepted paper {len(downloadable_papers)}: {paper.get('title', '')[:50]}"
                    )

                except Exception as e:
                    paper["download_error"] = str(e)
                    logger.debug(f"❌ Download verification outer exception: {e}")
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

    # Generate intelligent error suggestions if no results found
    if len(downloadable_papers) == 0:
        error_info = error_handler.generate_error_message(
            query=query,
            sources_searched=search_log["sources_searched"],
            fallback_used=False,  # No separate fallback needed since we already search all sources
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
