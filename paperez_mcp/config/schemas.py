"""
Configuration schemas for PaperezMCP - Type-safe configuration validation.
Supports custom categories, source providers, and meta-categories.
"""

import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

# Temporarily disable validators for testing - will fix with proper Pydantic V2 syntax
# from pydantic import validator

logger = logging.getLogger(__name__)


class SourceProviderConfig(BaseModel):
    """Configuration for a search source provider."""

    name: str = Field(..., description="Unique identifier for the source")
    type: Literal["builtin", "plugin", "http_api"] = Field(..., description="Source type")
    enabled: bool = Field(True, description="Whether source is enabled")

    # For builtin sources
    function_name: str | None = Field(None, description="Function name for builtin sources")

    # For plugin sources
    module_path: str | None = Field(None, description="Python module path for plugin")
    class_name: str | None = Field(None, description="Class name for plugin")

    # Source configuration
    config: dict[str, Any] = Field(default_factory=dict, description="Source-specific configuration")

    # Performance settings
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    cache_expire: int = Field(3600, description="Cache expiration in seconds")

    # TODO: Fix validators for Pydantic V2
    # @validator('function_name')
    # def validate_builtin_function(cls, v, values):
    #     if values.get('type') == 'builtin' and not v:
    #         raise ValueError("function_name required for builtin sources")
    #     return v

    # @validator('module_path')
    # def validate_module_path(cls, v, values):
    #     if values.get('type') == 'plugin' and not v:
    #         raise ValueError("module_path required for plugin sources")
    #     return v

    # @validator('class_name')
    # def validate_class_name(cls, v, values):
    #     if values.get('type') == 'plugin' and not v:
    #         raise ValueError("class_name required for plugin sources")
    #     return v


class CategoryConfig(BaseModel):
    """Configuration for a search category."""

    name: str = Field(..., description="Category identifier")
    display_name: str = Field(..., description="Human-readable category name")
    description: str = Field("", description="Category description")

    # Category type
    type: Literal["standard", "meta"] = Field("standard", description="Category type")

    # For standard categories
    sources: list[str] = Field(default_factory=list, description="Source names to search")

    # For meta categories
    includes: list[str] = Field(default_factory=list, description="Categories to include in meta search")
    merge_strategy: Literal["union", "weighted_union", "intersection"] = Field("union", description="How to merge results")
    weights: dict[str, float] = Field(default_factory=dict, description="Category weights for weighted merge")

    # Search behavior
    max_results_per_source: int = Field(5, description="Max results per source")
    parallel_search: bool = Field(True, description="Search sources in parallel")

    # TODO: Fix validators for Pydantic V2
    # @validator('sources')
    # def validate_standard_sources(cls, v, values):
    #     if values.get('type') == 'standard' and not v:
    #         raise ValueError("sources required for standard categories")
    #     return v

    # @validator('includes')
    # def validate_meta_includes(cls, v, values):
    #     if values.get('type') == 'meta' and not v:
    #         raise ValueError("includes required for meta categories")
    #     return v


class QueryRoutingConfig(BaseModel):
    """Configuration for intelligent query routing."""

    enabled: bool = Field(True, description="Enable smart routing")
    fallback_enabled: bool = Field(True, description="Enable fallback to comprehensive sources")

    # Domain detection
    domain_keywords: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "medical": ["medical", "clinical", "patient", "treatment", "therapy", "disease", "diagnosis", "health"],
            "computer_science": ["algorithm", "machine learning", "artificial intelligence", "neural", "deep learning"],
            "physics": ["quantum", "physics", "engineering", "materials", "energy", "electromagnetic"]
        },
        description="Keywords for domain detection"
    )

    # Category mapping for domains
    domain_categories: dict[str, str | None] = Field(
        default_factory=lambda: {
            "medical": "medical",
            "computer_science": "preprints",
            "physics": "preprints",
            "general": None  # Use intelligent routing for general queries
        },
        description="Default categories for detected domains"
    )


class PaperezConfig(BaseModel):
    """Main PaperezMCP configuration."""

    version: str = Field("1.0", description="Configuration schema version")

    # Source providers
    sources: dict[str, SourceProviderConfig] = Field(
        default_factory=dict,
        description="Available source providers"
    )

    # Categories
    categories: dict[str, CategoryConfig] = Field(
        default_factory=dict,
        description="Search categories"
    )

    # Query routing
    routing: QueryRoutingConfig = Field(
        default_factory=QueryRoutingConfig,
        description="Query routing configuration"
    )

    # Global settings
    default_category: str | None = Field(None, description="Default category when none specified (null = intelligent routing)")
    max_concurrent_searches: int = Field(10, description="Maximum concurrent source searches")

    # Cache settings
    global_cache_enabled: bool = Field(True, description="Enable global caching")
    global_cache_expire: int = Field(3600, description="Default cache expiration")

    # File management
    default_output_dir: str = Field(".paperez", description="Default output directory")
    cleanup_temp_files: bool = Field(True, description="Clean up temporary files")

    # User control options
    use_default_sources: bool = Field(True, description="Enable built-in default sources")

    # TODO: Fix validators for Pydantic V2
    # @validator('default_category')
    # def validate_default_category(cls, v, values):
    #     categories = values.get('categories', {})
    #     if categories and v not in categories:
    #         logger.warning(f"Default category '{v}' not found in categories")
    #     return v

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
                        warnings.append(f"Category '{cat_name}' references unknown source '{source_name}'")
                    elif not self.sources[source_name].enabled:
                        warnings.append(f"Category '{cat_name}' references disabled source '{source_name}'")
            elif category.type == "meta":
                for included_cat in category.includes:
                    if included_cat not in self.categories:
                        warnings.append(f"Meta-category '{cat_name}' includes unknown category '{included_cat}'")

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
                        warnings.append(f"Circular reference detected in meta-category '{cat_name}'")
                        return True
            return False

        for cat_name in self.categories:
            check_circular(cat_name)

        return warnings
