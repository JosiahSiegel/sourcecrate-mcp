"""
Search orchestration service - handles intelligent source routing and search coordination.
Extracts complex search logic from the main server file.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SearchOrchestrationService:
    """
    Coordinates search across multiple academic databases with intelligent routing.

    Handles:
    - Smart source selection based on query analysis
    - BM25 ranking for optimal source routing
    - Fallback strategies when primary sources fail
    - Search result aggregation and deduplication
    """

    def __init__(self, search_funcs: dict[str, Any], utils: dict[str, Any]):
        """
        Initialize search service.

        Args:
            search_funcs: Dictionary of search functions for each source
            utils: Dictionary of utility functions
        """
        self.search_funcs = search_funcs
        self.utils = utils
        self.logger = logging.getLogger(f"{__name__}.SearchOrchestration")

    async def smart_downloadable_search(
        self,
        query: str,
        limit: int,
        api_status: dict[str, bool],
        force_category: str | None = None,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Perform smart search with downloadable papers prioritization.

        Args:
            query: Search query
            limit: Maximum results to return
            api_status: API status tracking
            force_category: Force specific source category

        Returns:
            Tuple of (papers_list, search_log)
        """
        # Use existing smart_downloadable_search utility
        result = await self.utils["smart_downloadable_search"](
            query, limit, self.search_funcs, self.utils, api_status, force_category
        )
        return result  # type: ignore[no-any-return]

    async def comprehensive_search(
        self,
        query: str,
        limit: int,
        api_status: dict[str, bool],
        force_category: str | None = None,
        metadata_only: bool = False,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Perform comprehensive search across all available sources.

        Args:
            query: Search query
            limit: Maximum results to return
            api_status: API status tracking
            force_category: Force specific source category
            metadata_only: If True, don't require downloadable PDFs

        Returns:
            Tuple of (papers_list, search_log)
        """
        search_log: dict[str, Any] = {
            "query": query,
            "sources_attempted": [],
            "sources_successful": [],
            "total_found": 0,
        }

        all_papers = []
        sources_to_try = self._get_sources_for_category(force_category, api_status)

        for source_name in sources_to_try:
            if source_name in self.search_funcs and api_status.get(source_name, True):
                try:
                    self.logger.info(f"Searching {source_name} for '{query}'...")
                    search_log["sources_attempted"].append(source_name)

                    # Determine limit per source (distribute across sources)
                    per_source_limit = max(1, limit // len(sources_to_try))

                    results = await self.search_funcs[source_name](
                        query, per_source_limit
                    )

                    if results:
                        search_log["sources_successful"].append(source_name)

                        # Filter for downloadable papers if not metadata_only
                        if not metadata_only:
                            downloadable_results = [
                                paper
                                for paper in results
                                if paper.get("pdf_url") or paper.get("open_access_pdf")
                            ]
                            all_papers.extend(downloadable_results)
                        else:
                            all_papers.extend(results)

                        self.logger.info(
                            f"✅ {source_name}: Found {len(results)} results"
                        )
                    else:
                        self.logger.info(f"🔍 {source_name}: No results found")

                except Exception as e:
                    self.logger.warning(f"❌ {source_name} search failed: {e}")
                    api_status[source_name] = False

        # Deduplicate results by DOI and title
        deduplicated_papers = self._deduplicate_papers(all_papers)

        # Limit final results
        final_papers = deduplicated_papers[:limit]

        search_log["total_found"] = len(final_papers)
        search_log["deduplication"] = {
            "before": len(all_papers),
            "after": len(deduplicated_papers),
        }

        return final_papers, search_log

    def _get_sources_for_category(
        self, force_category: str | None, api_status: dict[str, bool]
    ) -> list[str]:
        """Get list of sources to search based on category using dynamic configuration."""
        if not force_category:
            # Default comprehensive search
            available_sources = [
                name
                for name, status in api_status.items()
                if status and f"search_{name}" in self.search_funcs
            ]
            return [f"search_{name}" for name in available_sources]

        # Load configuration to get category definitions
        try:
            from ..config.manager import get_current_config

            config = get_current_config()

            # Check if the force_category exists in configuration
            if force_category in config.categories:
                category_config = config.categories[force_category]
                if hasattr(category_config, "sources") and category_config.sources:
                    # Filter sources by availability and enabled status
                    available_sources = []
                    for source_name in category_config.sources:
                        # Check if source is available and enabled
                        if (
                            source_name in api_status
                            and api_status[source_name]
                            and f"search_{source_name}" in self.search_funcs
                            and source_name in config.sources
                            and config.sources[source_name].enabled
                        ):
                            available_sources.append(f"search_{source_name}")

                    if available_sources:
                        return available_sources

            # Fallback to capability-based selection for special categories
            return self._get_sources_by_capabilities(force_category, api_status)

        except Exception as e:
            # Fallback to capability-based selection if configuration loading fails
            logger.warning(f"Failed to load category configuration: {e}")
            return self._get_sources_by_capabilities(force_category, api_status)

    def _get_sources_by_capabilities(
        self, force_category: str, api_status: dict[str, bool]
    ) -> list[str]:
        """Get sources based on capabilities when category not found in config."""
        try:
            from ..config.manager import get_current_config

            config = get_current_config()

            # Map force_category to source capabilities
            capability_filters = {
                "preprints": lambda caps: getattr(caps, "preprint_focus", False)
                or getattr(caps, "stem_focus", False),
                "journals": lambda caps: getattr(caps, "peer_reviewed", False),
                "open_access": lambda caps: getattr(caps, "open_access_focus", False)
                or getattr(caps, "high_pdf_availability", False),
                "medical": lambda caps: getattr(caps, "medical_focus", False),
                "recent": lambda caps: getattr(caps, "recent_focus", False)
                or getattr(caps, "preprint_focus", False),
            }

            if force_category in capability_filters:
                filter_func = capability_filters[force_category]
                available_sources = []

                for source_name, source_config in config.sources.items():
                    if (
                        source_config.enabled
                        and source_name in api_status
                        and api_status[source_name]
                        and f"search_{source_name}" in self.search_funcs
                        and hasattr(source_config, "capabilities")
                        and source_config.capabilities
                        and filter_func(source_config.capabilities)
                    ):
                        available_sources.append(f"search_{source_name}")

                if available_sources:
                    return available_sources

        except Exception as e:
            logger.warning(f"Failed to filter sources by capabilities: {e}")

        # Final fallback to all available sources
        available_sources = [
            name
            for name, status in api_status.items()
            if status and f"search_{name}" in self.search_funcs
        ]
        return [f"search_{name}" for name in available_sources]

    def _deduplicate_papers(self, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Remove duplicate papers based on DOI and title similarity.

        Args:
            papers: List of paper dictionaries

        Returns:
            Deduplicated list of papers
        """
        seen_dois: set[str] = set()
        seen_titles: set[str] = set()
        deduplicated = []

        for paper in papers:
            # Check DOI duplication
            doi = paper.get("doi", "").strip()
            if doi and doi in seen_dois:
                continue

            # Check title duplication (case-insensitive, normalized)
            title = paper.get("title", "").strip().lower()
            title_normalized = " ".join(title.split())  # Normalize whitespace

            if title_normalized and title_normalized in seen_titles:
                continue

            # Add to seen sets
            if doi:
                seen_dois.add(doi)
            if title_normalized:
                seen_titles.add(title_normalized)

            deduplicated.append(paper)

        return deduplicated

    def analyze_query_domain(self, query: str) -> dict[str, Any]:
        """
        Analyze query to determine likely domain and suggest optimal sources using configuration.

        Args:
            query: Search query string

        Returns:
            Dictionary with domain analysis and source recommendations
        """
        try:
            from ..config.manager import get_current_config

            config = get_current_config()

            query_lower = query.lower()
            domain_scores = {}
            domain_keywords = {}

            # Get domain keywords from configuration
            if hasattr(config, "routing") and hasattr(
                config.routing, "domain_keywords"
            ):
                domain_keywords = config.routing.domain_keywords
            else:
                # Fallback to basic keywords if not in config
                domain_keywords = {
                    "medical": [
                        "medical",
                        "clinical",
                        "patient",
                        "treatment",
                        "therapy",
                        "disease",
                    ],
                    "computer_science": [
                        "algorithm",
                        "machine learning",
                        "artificial intelligence",
                        "computer",
                        "software",
                    ],
                    "physics": [
                        "quantum",
                        "physics",
                        "engineering",
                        "materials",
                        "energy",
                    ],
                }

            # Count domain-specific terms
            for domain, keywords in domain_keywords.items():
                score = sum(1 for keyword in keywords if keyword in query_lower)
                domain_scores[domain] = score

            # Determine primary domain
            max_score = max(domain_scores.values()) if domain_scores else 0
            domain = "general"
            if max_score > 0:
                domain = max(domain_scores, key=lambda x: domain_scores[x])

            # Get source recommendations based on capabilities
            recommended_sources = self._get_domain_source_recommendations(
                domain, config
            )

            # Get suggested category from configuration
            suggested_category = None
            if (
                hasattr(config, "routing")
                and hasattr(config.routing, "domain_categories")
                and domain in config.routing.domain_categories
            ):
                suggested_category = config.routing.domain_categories[domain]

            return {
                "domain": domain,
                "confidence_scores": domain_scores,
                "recommended_sources": recommended_sources,
                "suggested_category": suggested_category,
            }

        except Exception as e:
            logger.warning(f"Failed to analyze query domain: {e}")
            # Fallback to general recommendations
            return {
                "domain": "general",
                "confidence_scores": {},
                "recommended_sources": [
                    "search_crossref",
                    "search_semantic_scholar",
                    "search_arxiv",
                ],
                "suggested_category": None,
            }

    def _get_domain_source_recommendations(self, domain: str, config: Any) -> list[str]:
        """Get source recommendations for a domain based on capabilities."""
        try:
            # Map domains to capability filters
            domain_capability_map = {
                "medical": lambda caps: getattr(caps, "medical_focus", False),
                "computer_science": lambda caps: getattr(caps, "stem_focus", False)
                or getattr(caps, "preprint_focus", False),
                "physics": lambda caps: getattr(caps, "stem_focus", False)
                or getattr(caps, "preprint_focus", False),
                "business": lambda caps: getattr(caps, "business_focus", False),
                "humanities": lambda caps: getattr(caps, "humanities_focus", False),
                "social_sciences": lambda caps: getattr(
                    caps, "social_science_focus", False
                ),
                "legal": lambda caps: getattr(caps, "legal_focus", False),
                "historical": lambda caps: getattr(caps, "historical_focus", False),
            }

            recommended_sources = []

            if domain in domain_capability_map:
                filter_func = domain_capability_map[domain]

                # Find sources with matching capabilities
                for source_name, source_config in config.sources.items():
                    if (
                        source_config.enabled
                        and hasattr(source_config, "capabilities")
                        and source_config.capabilities
                        and filter_func(source_config.capabilities)
                    ):
                        recommended_sources.append(f"search_{source_name}")

                # Add high-quality general sources as backup
                general_sources = []
                for source_name, source_config in config.sources.items():
                    if (
                        source_config.enabled
                        and hasattr(source_config, "capabilities")
                        and source_config.capabilities
                        and getattr(source_config.capabilities, "peer_reviewed", False)
                        and f"search_{source_name}" not in recommended_sources
                    ):
                        general_sources.append(f"search_{source_name}")

                # Combine domain-specific and general sources
                recommended_sources.extend(
                    general_sources[:2]
                )  # Limit to avoid too many sources

            else:
                # For general or unknown domains, recommend high-quality sources
                for source_name, source_config in config.sources.items():
                    if (
                        source_config.enabled
                        and hasattr(source_config, "capabilities")
                        and source_config.capabilities
                        and getattr(source_config.capabilities, "peer_reviewed", False)
                    ):
                        recommended_sources.append(f"search_{source_name}")

            return recommended_sources[:5]  # Limit to 5 sources

        except Exception as e:
            logger.warning(f"Failed to get domain source recommendations: {e}")
            return ["search_crossref", "search_semantic_scholar", "search_arxiv"]
