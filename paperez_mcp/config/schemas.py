"""
Configuration schemas for PaperezMCP - Type-safe configuration validation.
Supports custom categories, source providers, and meta-categories.
"""

import logging
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class SourceCapabilities(BaseModel):
    """Defines capabilities and characteristics of a search source."""

    # Content domains
    medical_focus: bool = Field(
        False, description="Source specializes in medical/health content"
    )
    stem_focus: bool = Field(False, description="Source specializes in STEM fields")
    humanities_focus: bool = Field(
        False, description="Source specializes in humanities"
    )
    social_science_focus: bool = Field(
        False, description="Source specializes in social sciences"
    )
    preprint_server: bool = Field(
        False, description="Source primarily contains preprints"
    )

    # Technical capabilities
    field_search: bool = Field(
        False, description="Supports field-specific search (title, abstract, etc)"
    )
    phrase_search: bool = Field(True, description="Supports quoted phrase searching")
    boolean_search: bool = Field(
        False, description="Supports advanced boolean operators"
    )
    wildcard_search: bool = Field(
        False, description="Supports wildcard pattern matching"
    )

    # Content availability
    high_pdf_availability: bool = Field(
        False, description="Most papers have accessible PDFs"
    )
    open_access_only: bool = Field(False, description="Only open access content")
    subscription_content: bool = Field(
        True, description="May include subscription-only content"
    )

    # Query optimization preferences
    prefers_simple_queries: bool = Field(
        False, description="Works better with simple keyword queries"
    )
    prefers_natural_language: bool = Field(
        False, description="Works better with natural language queries"
    )
    prefers_quoted_phrases: bool = Field(
        False, description="Works better with quoted multi-word queries"
    )

    # Content characteristics
    historical_depth: Literal["low", "medium", "high", "very_high"] = Field(
        "medium", description="How much historical content is available"
    )
    update_frequency: Literal["daily", "weekly", "monthly"] = Field(
        "weekly", description="How often content is updated"
    )
    average_response_time: float = Field(
        2.0, description="Typical response time in seconds"
    )

    # PDF-specific capabilities
    pdf_url_patterns: list[str] = Field(
        default_factory=list, description="Regex patterns for extracting PDF URLs"
    )
    pdf_validation_required: bool = Field(
        True, description="PDF URLs should be validated"
    )

    # Priority and routing
    search_priority: int = Field(
        5, description="Search priority (1-10, higher = more important)"
    )
    topic_routing_weight: float = Field(
        1.0, description="Weight for topic-based routing"
    )


class SourceProviderConfig(BaseModel):
    """Configuration for a search source provider."""

    name: str = Field(..., description="Unique identifier for the source")
    type: Literal["builtin", "plugin", "http_api"] = Field(
        ..., description="Source type"
    )
    enabled: bool = Field(True, description="Whether source is enabled")
    disabled_reason: str | None = Field(
        None, description="Reason why source is disabled (shown in warnings)"
    )

    # For builtin sources
    function_name: str | None = Field(
        None, description="Function name for builtin sources"
    )

    # For plugin sources
    module_path: str | None = Field(None, description="Python module path for plugin")
    class_name: str | None = Field(None, description="Class name for plugin")

    # Source configuration
    config: dict[str, Any] = Field(
        default_factory=dict, description="Source-specific configuration"
    )

    # Performance settings
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    cache_expire: int = Field(3600, description="Cache expiration in seconds")

    # Source capabilities and characteristics
    capabilities: SourceCapabilities | None = None

    @model_validator(mode="after")
    def validate_source_config(self) -> "SourceProviderConfig":
        """Validate source configuration based on type."""
        if self.type == "builtin" and not self.function_name:
            raise ValueError("function_name required for builtin sources")

        if self.type == "plugin":
            if not self.module_path:
                raise ValueError("module_path required for plugin sources")
            if not self.class_name:
                raise ValueError("class_name required for plugin sources")

        return self


class CategoryConfig(BaseModel):
    """Configuration for a search category."""

    name: str = Field(..., description="Category identifier")
    display_name: str = Field(..., description="Human-readable category name")
    description: str = Field("", description="Category description")

    # Category type
    type: Literal["standard", "meta"] = Field("standard", description="Category type")

    # For standard categories
    sources: list[str] = Field(
        default_factory=list, description="Source names to search"
    )

    # For meta categories
    includes: list[str] = Field(
        default_factory=list, description="Categories to include in meta search"
    )
    merge_strategy: Literal["union", "weighted_union", "intersection"] = Field(
        "union", description="How to merge results"
    )
    weights: dict[str, float] = Field(
        default_factory=dict, description="Category weights for weighted merge"
    )

    # Search behavior
    max_results_per_source: int = Field(5, description="Max results per source")
    parallel_search: bool = Field(True, description="Search sources in parallel")

    @model_validator(mode="after")
    def validate_category_config(self) -> "CategoryConfig":
        """Validate category configuration based on type."""
        if self.type == "standard" and not self.sources:
            raise ValueError("sources required for standard categories")

        if self.type == "meta" and not self.includes:
            raise ValueError("includes required for meta categories")

        return self


class QueryRoutingConfig(BaseModel):
    """Configuration for intelligent query routing."""

    enabled: bool = Field(True, description="Enable smart routing")
    fallback_enabled: bool = Field(
        True, description="Enable fallback to comprehensive sources"
    )

    # Domain detection
    domain_keywords: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "medical": [
                "medical",
                "clinical",
                "patient",
                "treatment",
                "therapy",
                "disease",
                "diagnosis",
                "health",
            ],
            "computer_science": [
                "algorithm",
                "machine learning",
                "artificial intelligence",
                "neural",
                "deep learning",
            ],
            "physics": [
                "quantum",
                "physics",
                "engineering",
                "materials",
                "energy",
                "electromagnetic",
            ],
        },
        description="Keywords for domain detection",
    )

    # Category mapping for domains
    domain_categories: dict[str, str | None] = Field(
        default_factory=lambda: {
            "medical": "medical",
            "computer_science": "preprints",
            "physics": "preprints",
            "general": None,  # Use intelligent routing for general queries
        },
        description="Default categories for detected domains",
    )


class PaperezConfig(BaseModel):
    """Main PaperezMCP configuration."""

    version: str = Field("1.0", description="Configuration schema version")

    # Source providers
    sources: dict[str, SourceProviderConfig] = Field(
        default_factory=dict, description="Available source providers"
    )

    # Categories
    categories: dict[str, CategoryConfig] = Field(
        default_factory=dict, description="Search categories"
    )

    # Query routing
    routing: QueryRoutingConfig = Field(
        default_factory=lambda: QueryRoutingConfig(enabled=True, fallback_enabled=True),
        description="Query routing configuration",
    )

    # Global settings
    default_category: str | None = Field(
        None,
        description="Default category when none specified (null = intelligent routing)",
    )
    max_concurrent_searches: int = Field(
        10, description="Maximum concurrent source searches"
    )

    # Cache settings
    global_cache_enabled: bool = Field(True, description="Enable global caching")
    global_cache_expire: int = Field(3600, description="Default cache expiration")

    # File management
    default_output_dir: str = Field(".paperez", description="Default output directory")
    cleanup_temp_files: bool = Field(True, description="Clean up temporary files")

    # User control options
    use_default_sources: bool = Field(
        True, description="Enable built-in default sources"
    )

    @model_validator(mode="after")
    def validate_paperez_config(self) -> "PaperezConfig":
        """Validate configuration consistency."""
        if self.default_category and self.default_category not in self.categories:
            logger.warning(
                f"Default category '{self.default_category}' not found in categories"
            )

        return self

    def get_category_sources(self, category_name: str) -> list[str]:
        """Get source names for a category, resolving meta-categories."""
        if category_name not in self.categories:
            logger.warning(f"Category '{category_name}' not found")
            return []

        category = self.categories[category_name]

        if category.type == "standard":
            return category.sources
        elif category.type == "meta":
            # Resolve meta-category by collecting sources from included categories
            all_sources = []
            for included_category in category.includes:
                all_sources.extend(self.get_category_sources(included_category))
            return list(set(all_sources))  # Remove duplicates

        return []

    def get_enabled_sources(self) -> list[str]:
        """Get list of enabled source names."""
        return [name for name, config in self.sources.items() if config.enabled]

    def validate_configuration(self) -> list[str]:
        """Validate the complete configuration and return any warnings."""
        warnings = []

        # Check that all category sources exist and are enabled
        for cat_name, category in self.categories.items():
            if category.type == "standard":
                for source_name in category.sources:
                    if source_name not in self.sources:
                        warnings.append(
                            f"Category '{cat_name}' references unknown source '{source_name}'"
                        )
                    elif not self.sources[source_name].enabled:
                        source_config = self.sources[source_name]
                        reason = getattr(
                            source_config, "disabled_reason", "Unknown reason"
                        )
                        warnings.append(
                            f"Category '{cat_name}' references disabled source '{source_name}' - "
                            f"Reason: {reason}. To enable, set 'enabled: true' in the source configuration "
                            f"and ensure required credentials are configured."
                        )
            elif category.type == "meta":
                for included_cat in category.includes:
                    if included_cat not in self.categories:
                        warnings.append(
                            f"Meta-category '{cat_name}' includes unknown category '{included_cat}'"
                        )

        # Check for circular meta-category references
        def check_circular(cat_name: str, visited: set[Any] | None = None) -> bool:
            if visited is None:
                visited = set()
            if cat_name in visited:
                return True
            if cat_name not in self.categories:
                return False

            category = self.categories[cat_name]
            if category.type == "meta":
                visited.add(cat_name)
                for included in category.includes:
                    if check_circular(included, visited.copy()):
                        warnings.append(
                            f"Circular reference detected in meta-category '{cat_name}'"
                        )
                        return True
            return False

        for cat_name in self.categories:
            check_circular(cat_name)

        return warnings
