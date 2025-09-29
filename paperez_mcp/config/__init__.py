"""
Configuration system for PaperezMCP - Comprehensive configuration management.

This module provides the YAML-based configuration system:
- Type-safe configuration schemas with Pydantic validation
- Multi-tier configuration loading (builtin → user → project → environment)
- Hot-reloading with file system watching
- Dynamic source registration for both builtin and plugin sources
- Meta-category support for searching across multiple categories

Usage:
    from paperez_mcp.config import get_current_config, get_search_service
    config = get_current_config()
    search_service = get_search_service()
"""

from .manager import ConfigManager, get_config_manager, get_current_config

# Default config now loaded from YAML - no utility functions needed
from .registry import (
    CategoryResolver,
    ConfigurableSearchService,
    SourceRegistry,
    get_search_service,
)

# Configurable system schemas
from .schemas import (
    CategoryConfig,
    PaperezConfig,
    QueryRoutingConfig,
    SourceProviderConfig,
)

__all__ = [
    # Configuration schemas
    "PaperezConfig",
    "SourceProviderConfig",
    "CategoryConfig",
    "QueryRoutingConfig",
    # Configuration manager
    "ConfigManager",
    "get_config_manager",
    "get_current_config",
    # Service registry
    "SourceRegistry",
    "CategoryResolver",
    "ConfigurableSearchService",
    "get_search_service",
    # Utility functions
    "initialize_configuration_system",
    "create_example_config_file",
    "validate_current_configuration",
]


def initialize_configuration_system(
    enable_hot_reload: bool = True,
) -> ConfigurableSearchService:
    """
    Initialize the complete configuration system.

    Args:
        enable_hot_reload: Whether to enable configuration hot-reloading

    Returns:
        Configured search service ready for use
    """
    # Initialize configuration manager
    get_config_manager(enable_hot_reload=enable_hot_reload)

    # Initialize search service (automatically registers with config manager)
    search_service = get_search_service()

    return search_service


def create_example_config_file(
    output_path: str = "paperez.config.example.yaml",
) -> None:
    """Create an example configuration file for users."""
    from pathlib import Path

    config_manager = get_config_manager()
    config_manager.create_example_config(Path(output_path))


def validate_current_configuration() -> dict:
    """Validate the current configuration and return status."""
    try:
        config = get_current_config()
        search_service = get_search_service()

        warnings = config.validate_configuration()
        status = search_service.get_service_status()

        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "service_status": status,
            "configuration_summary": {
                "version": config.version,
                "total_sources": len(config.sources),
                "enabled_sources": len(
                    [s for s in config.sources.values() if s.enabled]
                ),
                "total_categories": len(config.categories),
                "default_category": config.default_category,
                "smart_routing": config.routing.enabled,
            },
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}
