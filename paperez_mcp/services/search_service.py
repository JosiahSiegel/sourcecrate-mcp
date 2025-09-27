"""
Search orchestration service - handles intelligent source routing and search coordination.
Extracts complex search logic from the main server file.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

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

    def __init__(self, search_funcs: Dict[str, Any], utils: Dict[str, Any]):
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
        api_status: Dict[str, bool],
        force_category: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
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
        return await self.utils['smart_downloadable_search'](
            query, limit, self.search_funcs, self.utils, api_status, force_category
        )

    async def comprehensive_search(
        self,
        query: str,
        limit: int,
        api_status: Dict[str, bool],
        force_category: Optional[str] = None,
        metadata_only: bool = False
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
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
        search_log = {
            "query": query,
            "sources_attempted": [],
            "sources_successful": [],
            "total_found": 0
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

                    results = await self.search_funcs[source_name](query, per_source_limit)

                    if results:
                        search_log["sources_successful"].append(source_name)

                        # Filter for downloadable papers if not metadata_only
                        if not metadata_only:
                            downloadable_results = [
                                paper for paper in results
                                if paper.get("pdf_url") or paper.get("open_access_pdf")
                            ]
                            all_papers.extend(downloadable_results)
                        else:
                            all_papers.extend(results)

                        self.logger.info(f"✅ {source_name}: Found {len(results)} results")
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
            "after": len(deduplicated_papers)
        }

        return final_papers, search_log

    def _get_sources_for_category(
        self,
        force_category: Optional[str],
        api_status: Dict[str, bool]
    ) -> List[str]:
        """Get list of sources to search based on category."""
        if force_category == "preprints":
            return ["search_arxiv", "search_biorxiv"]
        elif force_category == "journals":
            return ["search_crossref", "search_pubmed"]
        elif force_category == "open_access":
            return ["search_arxiv", "search_pubmed_central", "search_crossref"]
        elif force_category == "medical":
            return ["search_pubmed", "search_pubmed_central", "search_clinicaltrials"]
        elif force_category == "recent":
            return ["search_arxiv", "search_semantic_scholar"]
        else:
            # Default comprehensive search
            available_sources = [
                name for name, status in api_status.items()
                if status and f"search_{name}" in self.search_funcs
            ]
            return [f"search_{name}" for name in available_sources]

    def _deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate papers based on DOI and title similarity.

        Args:
            papers: List of paper dictionaries

        Returns:
            Deduplicated list of papers
        """
        seen_dois: Set[str] = set()
        seen_titles: Set[str] = set()
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

    def analyze_query_domain(self, query: str) -> Dict[str, Any]:
        """
        Analyze query to determine likely domain and suggest optimal sources.

        Args:
            query: Search query string

        Returns:
            Dictionary with domain analysis and source recommendations
        """
        query_lower = query.lower()

        # Medical/biomedical terms
        medical_terms = ["medical", "clinical", "patient", "treatment", "therapy",
                        "disease", "diagnosis", "health", "medicine", "pharmaceutical"]

        # Computer science terms
        cs_terms = ["algorithm", "machine learning", "artificial intelligence",
                   "computer", "software", "programming", "neural", "deep learning"]

        # Physics/engineering terms
        physics_terms = ["quantum", "physics", "engineering", "materials",
                        "energy", "electromagnetic", "mechanics"]

        # Count domain-specific terms
        medical_score = sum(1 for term in medical_terms if term in query_lower)
        cs_score = sum(1 for term in cs_terms if term in query_lower)
        physics_score = sum(1 for term in physics_terms if term in query_lower)

        # Determine primary domain
        domain = "general"
        if medical_score > 0:
            domain = "medical"
        elif cs_score > 0:
            domain = "computer_science"
        elif physics_score > 0:
            domain = "physics"

        # Suggest optimal sources
        source_recommendations = {
            "medical": ["search_pubmed", "search_pubmed_central", "search_clinicaltrials"],
            "computer_science": ["search_arxiv", "search_semantic_scholar", "search_crossref"],
            "physics": ["search_arxiv", "search_crossref", "search_semantic_scholar"],
            "general": ["search_crossref", "search_semantic_scholar", "search_arxiv"]
        }

        return {
            "domain": domain,
            "confidence_scores": {
                "medical": medical_score,
                "computer_science": cs_score,
                "physics": physics_score
            },
            "recommended_sources": source_recommendations.get(domain, []),
            "suggested_category": domain if domain != "general" else None
        }