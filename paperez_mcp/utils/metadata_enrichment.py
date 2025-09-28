"""
Metadata Enrichment Service

Enhances paper metadata by filling missing fields from multiple sources.
Addresses Issue 4.2: Incomplete Metadata Across Sources from COMPREHENSIVE_ISSUE_RESOLUTION.md
"""

import logging
from typing import Any

from ..config import get_current_config

logger = logging.getLogger(__name__)


class MetadataEnrichmentService:
    """Service for enriching paper metadata from multiple sources using dynamic capability-based routing"""

    def __init__(self) -> None:
        # No hardcoded fields - discover dynamically from source configurations
        pass

    def _discover_available_fields(self) -> set[str]:
        """
        Dynamically discover all fields available across all configured sources

        Returns:
            Set of all field names that any source can provide
        """
        all_fields = set()

        try:
            config = get_current_config()
            for _source_name, source_config in config.sources.items():
                if not source_config.enabled:
                    continue

                # Get field mappings from configuration
                if source_config.config:
                    field_mappings = source_config.config.get("field_mappings", {})
                    all_fields.update(field_mappings.keys())

                # Add standard fields for builtin sources
                if source_config.type == "builtin":
                    all_fields.update(
                        {
                            "title",
                            "authors",
                            "abstract",
                            "journal",
                            "year",
                            "doi",
                            "url",
                            "pdf_url",
                            "citation_count",
                            "source",
                        }
                    )

        except Exception as e:
            logger.warning(f"Could not discover fields: {e}")

        return all_fields

    def _get_source_capabilities(self) -> dict[str, dict[str, Any]]:
        """
        Get dynamic source capabilities from configuration

        Returns:
            Dict mapping source names to their capabilities and characteristics
        """
        try:
            config = get_current_config()
            source_caps = {}

            for source_name, source_config in config.sources.items():
                if not source_config.enabled:
                    continue

                capabilities = source_config.capabilities
                if capabilities:
                    source_caps[source_name] = {
                        # Field specialization (higher score = more authoritative)
                        "medical_focus": getattr(capabilities, "medical_focus", False),
                        "stem_focus": getattr(capabilities, "stem_focus", False),
                        "humanities_focus": getattr(
                            capabilities, "humanities_focus", False
                        ),
                        "preprint_server": getattr(
                            capabilities, "preprint_server", False
                        ),
                        # PDF availability
                        "high_pdf_availability": getattr(
                            capabilities, "high_pdf_availability", False
                        ),
                        "open_access_only": getattr(
                            capabilities, "open_access_only", False
                        ),
                        # Data quality indicators
                        "field_search": capabilities.field_search,
                        "search_priority": capabilities.search_priority,
                        "average_response_time": capabilities.average_response_time,
                        # Available field mappings from config
                        "available_fields": (
                            set(source_config.config.get("field_mappings", {}).keys())
                            if source_config.config
                            else set()
                        ),
                        # Source type info
                        "source_type": source_config.type,
                    }
                else:
                    # Fallback for sources without capabilities
                    source_caps[source_name] = {
                        "search_priority": 5,  # Default priority
                        "available_fields": (
                            set(source_config.config.get("field_mappings", {}).keys())
                            if source_config.config
                            else set()
                        ),
                        "source_type": source_config.type,
                    }

            return source_caps

        except Exception as e:
            logger.warning(f"Could not load source capabilities: {e}")
            return {}

    def _calculate_field_quality(self, field_name: str, value: Any) -> float:
        """
        Calculate quality score for a field value (0.0 to 1.0)

        Args:
            field_name: Name of the field
            value: Field value to evaluate

        Returns:
            Quality score between 0.0 and 1.0
        """
        if not value:
            return 0.0

        # Field-specific quality scoring
        if field_name == "title":
            title_str = str(value)
            if len(title_str) < 10:
                return 0.3  # Very short titles are probably incomplete
            elif len(title_str) < 30:
                return 0.7  # Short titles might be incomplete
            else:
                return 1.0  # Good length titles

        elif field_name == "authors":
            if isinstance(value, list):
                if len(value) == 0:
                    return 0.0
                elif len(value) == 1 and len(str(value[0])) < 5:
                    return 0.3  # Single very short author name
                else:
                    return 1.0  # Multiple authors or good single author
            elif isinstance(value, str):
                if len(value) < 5:
                    return 0.3  # Very short author string
                elif "," in value or " and " in value:
                    return 0.8  # Multiple authors indicated
                else:
                    return 0.6  # Single author

        elif field_name == "abstract":
            abstract_str = str(value)
            if len(abstract_str) < 50:
                return 0.2  # Very short abstracts are probably incomplete
            elif len(abstract_str) < 200:
                return 0.6  # Short abstracts might be incomplete
            else:
                return 1.0  # Good length abstracts

        elif field_name == "year":
            try:
                year_int = int(value) if isinstance(value, (str, int)) else 0
                if 1900 <= year_int <= 2030:
                    return 1.0  # Valid year range
                else:
                    return 0.0  # Invalid year
            except (ValueError, TypeError):
                return 0.0

        elif field_name == "doi":
            doi_str = str(value)
            if doi_str.startswith("10.") and "/" in doi_str:
                return 1.0  # Valid DOI format
            else:
                return 0.3  # Questionable DOI format

        elif field_name == "citation_count":
            try:
                count = int(value) if value else 0
                return 1.0 if count >= 0 else 0.0  # Any valid count is good
            except (ValueError, TypeError):
                return 0.0

        # Default scoring for other fields
        return 1.0 if value else 0.0

    def _calculate_source_authority(
        self, source_name: str, field_name: str, capabilities: dict[str, Any]
    ) -> float:
        """
        Calculate source authority for a specific field based on capabilities

        Args:
            source_name: Name of the source
            field_name: Field being evaluated
            capabilities: Source capabilities dictionary

        Returns:
            Authority score (0.0 to 1.0)
        """
        # Base authority from search priority (1-10 scale)
        base_authority = capabilities.get("search_priority", 5) / 10.0

        # Field-specific authority bonuses
        field_bonus = 0.0

        if field_name in ["title", "abstract", "authors"]:
            # Peer-reviewed sources are more authoritative for academic metadata
            if capabilities.get("peer_reviewed", False):
                field_bonus += 0.2

        elif field_name == "doi":
            # CrossRef and PubMed are authoritative for DOIs
            if "crossref" in source_name.lower():
                field_bonus += 0.3
            elif capabilities.get("medical_focus", False):
                field_bonus += 0.2

        elif field_name in ["pdf_url", "open_access_pdf"]:
            # High PDF availability sources are more authoritative
            if capabilities.get("high_pdf_availability", False):
                field_bonus += 0.3
            if capabilities.get("preprint_server", False):
                field_bonus += 0.2

        elif field_name == "citation_count":
            # Academic search engines are more authoritative for citations
            if (
                "semantic_scholar" in source_name.lower()
                or "openalex" in source_name.lower()
            ):
                field_bonus += 0.3

        # Domain specialization bonuses
        if capabilities.get("medical_focus", False) and "medical" in field_name:
            field_bonus += 0.1
        if capabilities.get("stem_focus", False):
            field_bonus += 0.1

        return min(1.0, float(base_authority + field_bonus))

    def _extract_all_fields_from_paper(
        self, paper_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract all possible fields from a paper, including unknown/custom fields

        Args:
            paper_data: Raw paper data from any source

        Returns:
            Dictionary with all extractable fields, including unknown ones
        """
        extracted = {}

        # Get all top-level fields
        for key, value in paper_data.items():
            if value is not None and value != "":
                extracted[key] = value

        # For sources with nested structures, try to extract useful nested fields
        # This handles cases where sources return complex JSON structures
        for key, value in paper_data.items():
            if isinstance(value, dict):
                # Extract nested fields with dot notation
                for nested_key, nested_value in value.items():
                    if nested_value is not None and nested_value != "":
                        dot_key = f"{key}.{nested_key}"
                        extracted[dot_key] = nested_value

                        # Go one level deeper for very nested structures
                        if isinstance(nested_value, dict):
                            for deep_key, deep_value in nested_value.items():
                                if deep_value is not None and deep_value != "":
                                    deep_dot_key = f"{key}.{nested_key}.{deep_key}"
                                    extracted[deep_dot_key] = deep_value

            elif isinstance(value, list) and value:
                # Extract first item from lists (common in academic APIs)
                first_item = value[0]
                if first_item is not None:
                    list_key = f"{key}.0"
                    extracted[list_key] = first_item

                    # If list contains dicts, extract their fields too
                    if isinstance(first_item, dict):
                        for nested_key, nested_value in first_item.items():
                            if nested_value is not None and nested_value != "":
                                nested_list_key = f"{key}.0.{nested_key}"
                                extracted[nested_list_key] = nested_value

        return extracted

    def _calculate_field_quality_generic(
        self, field_name: str, value: Any, source_name: str = ""
    ) -> float:
        """
        Calculate quality score for any field value, even unknown ones

        Args:
            field_name: Name of the field
            value: Field value to evaluate
            source_name: Source name for context

        Returns:
            Quality score between 0.0 and 1.0
        """
        if not value:
            return 0.0

        # Known field quality patterns
        known_patterns = {
            "title": self._calculate_field_quality,
            "authors": self._calculate_field_quality,
            "abstract": self._calculate_field_quality,
            "year": self._calculate_field_quality,
            "doi": self._calculate_field_quality,
            "citation_count": self._calculate_field_quality,
        }

        # Use existing quality calculation for known fields
        for pattern, func in known_patterns.items():
            if pattern in field_name.lower():
                return func(pattern, value)

        # Generic quality scoring for unknown fields
        value_str = str(value)

        # URL-like fields
        if "url" in field_name.lower() or "link" in field_name.lower():
            if value_str.startswith(("http://", "https://")):
                return 1.0
            elif value_str.startswith("//"):
                return 0.8
            else:
                return 0.3

        # ID-like fields
        if "id" in field_name.lower():
            if len(value_str) > 3:  # IDs should have some length
                return 1.0
            else:
                return 0.3

        # Date-like fields
        if any(
            date_word in field_name.lower()
            for date_word in ["date", "time", "published", "created"]
        ):
            # Check for various date formats
            import re

            if re.search(r"\d{4}", value_str):  # Contains a year
                return 1.0
            else:
                return 0.3

        # Text-like fields
        if isinstance(value, str):
            if len(value_str) > 10:
                return 1.0
            elif len(value_str) > 3:
                return 0.7
            else:
                return 0.3

        # Numeric fields
        if isinstance(value, (int, float)):
            return 1.0

        # List fields
        if isinstance(value, list):
            return 1.0 if len(value) > 0 else 0.0

        # Default for other types
        return 0.8

    def _select_best_value(
        self, field_name: str, source_values: dict[str, Any]
    ) -> tuple[Any, str]:
        """
        Select the best value for a field from multiple sources using dynamic capabilities

        Args:
            field_name: Name of the field to select
            source_values: Dict mapping source names to field values

        Returns:
            Tuple of (best_value, source_name)
        """
        if not source_values:
            return None, ""

        # Get current source capabilities
        source_capabilities = self._get_source_capabilities()

        # Calculate quality scores for each value
        scored_values = []
        for source, value in source_values.items():
            # Base quality of the value itself
            value_quality = self._calculate_field_quality(field_name, value)

            # Source authority for this field
            source_caps = source_capabilities.get(source, {})
            source_authority = self._calculate_source_authority(
                source, field_name, source_caps
            )

            # Check if source actually provides this field
            available_fields = source_caps.get("available_fields", set())
            field_availability_bonus = 0.1 if field_name in available_fields else 0.0

            # Combine scores (value quality is most important, then source authority)
            total_score = (
                (value_quality * 0.7)
                + (source_authority * 0.2)
                + field_availability_bonus
            )

            scored_values.append(
                (total_score, source, value, value_quality, source_authority)
            )

        # Sort by score (highest first)
        scored_values.sort(reverse=True, key=lambda x: x[0])

        if scored_values:
            best_score, best_source, best_value, val_quality, src_authority = (
                scored_values[0]
            )
            logger.debug(
                f"Selected {field_name} from {best_source} (total: {best_score:.2f}, "
                f"value: {val_quality:.2f}, authority: {src_authority:.2f})"
            )
            return best_value, best_source

        return None, ""

    async def enrich_paper_metadata(
        self, primary_paper: dict[str, Any], alternative_papers: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Enrich paper metadata by filling missing or low-quality fields from alternatives

        Args:
            primary_paper: Main paper data to enrich
            alternative_papers: List of alternative paper data from other sources

        Returns:
            Enriched paper metadata with the best values from all sources
        """
        enriched = primary_paper.copy()

        # Combine all papers for field selection
        all_papers = [primary_paper] + alternative_papers

        # Identify sources for each paper
        source_names = []
        for i, paper in enumerate(all_papers):
            source = paper.get("source", f"source_{i}")
            source_names.append(source.lower().replace(" ", "_"))

        # Dynamically discover all available fields from configuration
        available_fields = self._discover_available_fields()

        # Enrich each field
        enrichment_log = {}

        for field_name in available_fields:
            # Collect values from all sources
            source_values = {}
            for source_name, paper in zip(source_names, all_papers, strict=True):
                value = paper.get(field_name)
                if value is not None and value != "":
                    source_values[source_name] = value

            if source_values:
                best_value, best_source = self._select_best_value(
                    field_name, source_values
                )

                # Check if we're improving the primary value
                primary_value = primary_paper.get(field_name)
                primary_quality = self._calculate_field_quality(
                    field_name, primary_value
                )
                best_quality = self._calculate_field_quality(field_name, best_value)

                if best_quality > primary_quality:
                    enriched[field_name] = best_value
                    enrichment_log[field_name] = {
                        "original_source": source_names[0],
                        "enriched_source": best_source,
                        "quality_improvement": best_quality - primary_quality,
                    }

        # Add enrichment metadata
        if enrichment_log:
            enriched["_enrichment_log"] = enrichment_log
            enriched["_enriched_fields"] = list(enrichment_log.keys())
            logger.info(
                f"Enriched {len(enrichment_log)} fields: {', '.join(enrichment_log.keys())}"
            )

        return enriched

    async def find_matching_papers(
        self, target_paper: dict[str, Any], max_sources: int = 3
    ) -> list[dict[str, Any]]:
        """
        Find matching papers from other sources for enrichment

        Args:
            target_paper: Paper to find matches for
            max_sources: Maximum number of alternative sources to search

        Returns:
            List of matching papers from other sources
        """
        # This would integrate with the search system to find matches
        # For now, return empty list as this requires search system integration
        # TODO: Implement cross-source paper matching

        logger.debug("Cross-source paper matching not yet implemented")
        return []

    def get_enrichment_stats(self, papers: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Get statistics about metadata enrichment across a set of papers

        Args:
            papers: List of papers to analyze

        Returns:
            Dictionary with enrichment statistics
        """
        if not papers:
            return {"total_papers": 0}

        enriched_count = 0
        field_improvements = {}
        total_fields_enriched = 0

        for paper in papers:
            enrichment_log = paper.get("_enrichment_log", {})
            if enrichment_log:
                enriched_count += 1
                total_fields_enriched += len(enrichment_log)

                for field_name, log_entry in enrichment_log.items():
                    if field_name not in field_improvements:
                        field_improvements[field_name] = {
                            "count": 0,
                            "total_improvement": 0.0,
                        }

                    field_improvements[field_name]["count"] += 1
                    field_improvements[field_name][
                        "total_improvement"
                    ] += log_entry.get("quality_improvement", 0.0)

        # Calculate averages
        for field_stats in field_improvements.values():
            field_stats["avg_improvement"] = (
                field_stats["total_improvement"] / field_stats["count"]
                if field_stats["count"] > 0
                else 0.0
            )

        return {
            "total_papers": len(papers),
            "enriched_papers": enriched_count,
            "enrichment_rate": enriched_count / len(papers) if papers else 0.0,
            "total_fields_enriched": total_fields_enriched,
            "avg_fields_per_paper": (
                total_fields_enriched / len(papers) if papers else 0.0
            ),
            "field_improvements": field_improvements,
        }


# Global instance for easy access
metadata_enrichment_service = MetadataEnrichmentService()
