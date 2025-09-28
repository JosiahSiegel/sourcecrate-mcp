"""
Service registry for PaperezMCP - Dynamic source loading and category resolution.
Manages both built-in and plugin sources with configuration-driven registration.
"""

import importlib
import logging
from collections.abc import Callable
from typing import Any

from .manager import get_current_config
from .schemas import CategoryConfig, PaperezConfig, SourceProviderConfig

logger = logging.getLogger(__name__)


class SourceRegistry:
    """Registry for managing search source providers."""

    def __init__(self) -> None:
        self._sources: dict[str, Callable] = {}
        self._source_configs: dict[str, SourceProviderConfig] = {}
        self._plugin_instances: dict[str, Any] = {}

    def register_builtin_sources(self):
        """Register all built-in search sources."""
        from ..api_clients import (
            search_arxiv,
            search_google_scholar_fallback,
            search_pubmed,
            search_pubmed_central,
        )

        # Built-in source function mapping (only for sources not yet converted to config)
        builtin_sources = {
            'search_arxiv': search_arxiv,
            'search_pubmed': search_pubmed,
            'search_pubmed_central': search_pubmed_central,
            'search_google_scholar_fallback': search_google_scholar_fallback,
        }

        config = get_current_config()
        for source_name, source_config in config.sources.items():
            if source_config.type == 'builtin' and source_config.enabled:
                function_name = source_config.function_name
                if function_name in builtin_sources:
                    self._sources[source_name] = builtin_sources[function_name]
                    self._source_configs[source_name] = source_config
                    logger.info(f"Registered built-in source: {source_name}")
                else:
                    logger.warning(f"Built-in function not found: {function_name}")

    def register_plugin_source(self, source_name: str, source_config: SourceProviderConfig):
        """Register a plugin-based search source."""
        try:
            # Import the plugin module
            module = importlib.import_module(source_config.module_path)
            plugin_class = getattr(module, source_config.class_name)

            # Validate that it has the required search method
            if not hasattr(plugin_class, 'search'):
                raise ValueError(f"Plugin class {source_config.class_name} must have a 'search' method")

            # Create instance with configuration
            plugin_instance = plugin_class(**source_config.config)
            self._plugin_instances[source_name] = plugin_instance

            # Create wrapper function for compatibility (fix closure bug)
            async def plugin_wrapper(query: str, limit: int = 5, instance=plugin_instance, **kwargs):
                return await instance.search(query, limit, **kwargs)

            self._sources[source_name] = plugin_wrapper
            self._source_configs[source_name] = source_config
            logger.info(f"Registered plugin source: {source_name}")

        except Exception as e:
            logger.error(f"Failed to register plugin source {source_name}: {e}")

    def register_http_api_source(self, source_name: str, source_config: SourceProviderConfig):
        """Register an HTTP API-based search source using configuration only."""
        try:
            from ..api_clients.generic_http_client import GenericHTTPClient

            # Create instance with configuration
            api_instance = GenericHTTPClient(source_name, **source_config.config)
            self._plugin_instances[source_name] = api_instance

            # Create wrapper function for compatibility (fix closure bug)
            async def api_wrapper(query: str, limit: int = 5, instance=api_instance, **kwargs):
                return await instance.search(query, limit, **kwargs)

            self._sources[source_name] = api_wrapper
            self._source_configs[source_name] = source_config
            logger.info(f"Registered HTTP API source: {source_name}")

        except Exception as e:
            logger.error(f"Failed to register HTTP API source {source_name}: {e}")

    def register_all_sources(self):
        """Register all sources from current configuration."""
        self.clear()
        self.register_builtin_sources()

        config = get_current_config()
        for source_name, source_config in config.sources.items():
            if source_config.type == 'plugin' and source_config.enabled:
                self.register_plugin_source(source_name, source_config)
            elif source_config.type == 'http_api' and source_config.enabled:
                self.register_http_api_source(source_name, source_config)

    def get_source_function(self, source_name: str) -> Callable | None:
        """Get search function for a source."""
        return self._sources.get(source_name)

    def get_source_config(self, source_name: str) -> SourceProviderConfig | None:
        """Get configuration for a source."""
        return self._source_configs.get(source_name)

    def get_enabled_sources(self) -> list[str]:
        """Get list of enabled source names."""
        return list(self._sources.keys())

    def is_source_available(self, source_name: str) -> bool:
        """Check if a source is available and enabled."""
        return source_name in self._sources

    def clear(self):
        """Clear all registered sources."""
        self._sources.clear()
        self._source_configs.clear()
        self._plugin_instances.clear()


class CategoryResolver:
    """Resolves categories to source lists, handling meta-categories."""

    def __init__(self, source_registry: SourceRegistry):
        self.source_registry = source_registry

    def resolve_category(self, category_name: str, visited: set[str] | None = None) -> list[str]:
        """
        Resolve a category to a list of source names.
        Handles meta-categories recursively with circular reference detection.
        """
        if visited is None:
            visited = set()

        if category_name in visited:
            logger.warning(f"Circular reference detected in category resolution: {category_name}")
            return []

        config = get_current_config()
        if category_name not in config.categories:
            logger.warning(f"Category not found: {category_name}")
            return []

        category = config.categories[category_name]
        visited.add(category_name)

        if category.type == 'standard':
            # Filter to only available sources
            available_sources = [
                source for source in category.sources
                if self.source_registry.is_source_available(source)
            ]
            return available_sources

        elif category.type == 'meta':
            # Recursively resolve included categories
            all_sources = []
            for included_category in category.includes:
                resolved_sources = self.resolve_category(included_category, visited.copy())
                all_sources.extend(resolved_sources)

            # Remove duplicates while preserving order
            unique_sources = []
            seen = set()
            for source in all_sources:
                if source not in seen:
                    unique_sources.append(source)
                    seen.add(source)

            return unique_sources

        return []

    def get_category_config(self, category_name: str) -> CategoryConfig | None:
        """Get configuration for a category."""
        config = get_current_config()
        return config.categories.get(category_name)

    def get_available_categories(self) -> list[str]:
        """Get list of available category names."""
        config = get_current_config()
        return list(config.categories.keys())

    def get_category_info(self, category_name: str) -> dict[str, Any]:
        """Get detailed information about a category."""
        category_config = self.get_category_config(category_name)
        if not category_config:
            return {}

        sources = self.resolve_category(category_name)
        return {
            'name': category_config.name,
            'display_name': category_config.display_name,
            'description': category_config.description,
            'type': category_config.type,
            'sources': sources,
            'available_sources': len(sources),
            'total_configured_sources': (
                len(category_config.sources) if category_config.type == 'standard'
                else len(category_config.includes)
            )
        }


class ConfigurableSearchService:
    """Enhanced search service with configuration-driven source and category management."""

    def __init__(self):
        self.source_registry = SourceRegistry()
        self.category_resolver = CategoryResolver(self.source_registry)
        self._initialize()

        # Register for configuration changes
        from .manager import get_config_manager
        config_manager = get_config_manager()
        config_manager.add_reload_callback(self._on_config_reload)

    def _initialize(self):
        """Initialize the service with current configuration."""
        self.source_registry.register_all_sources()
        logger.info("Configurable search service initialized")

    def _on_config_reload(self, new_config: PaperezConfig):
        """Handle configuration reload."""
        logger.info("Reloading search service configuration...")
        self.source_registry.register_all_sources()
        logger.info("Search service configuration reloaded")

    def get_search_functions(self) -> dict[str, Callable]:
        """Get dictionary of search functions for compatibility with existing code."""
        search_funcs = {}
        for source_name in self.source_registry.get_enabled_sources():
            search_func = self.source_registry.get_source_function(source_name)
            if search_func:
                # Use source name directly (not prefixed with "search_")
                # This matches what smart_search.py expects
                search_funcs[source_name] = search_func
        return search_funcs

    def resolve_category_sources(self, category_name: str) -> list[str]:
        """Resolve category to list of available source names."""
        return self.category_resolver.resolve_category(category_name)

    def get_smart_category_for_query(self, query: str) -> str:
        """Get smart category suggestion for a query based on domain detection."""
        config = get_current_config()
        if not config.routing.enabled:
            return config.default_category

        query_lower = query.lower()

        # Domain detection based on keywords
        for domain, keywords in config.routing.domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                suggested_category = config.routing.domain_categories.get(domain, config.default_category)
                logger.info(f"Smart routing: '{query}' → domain '{domain}' → category '{suggested_category}'")
                return suggested_category

        return config.default_category

    def get_service_status(self) -> dict[str, Any]:
        """Get comprehensive service status."""
        config = get_current_config()
        enabled_sources = self.source_registry.get_enabled_sources()

        return {
            'configuration_version': config.version,
            'total_sources': len(config.sources),
            'enabled_sources': len(enabled_sources),
            'enabled_source_names': enabled_sources,
            'total_categories': len(config.categories),
            'category_names': list(config.categories.keys()),
            'default_category': config.default_category,
            'smart_routing_enabled': config.routing.enabled,
            'fallback_enabled': config.routing.fallback_enabled
        }

    def validate_category(self, category_name: str) -> dict[str, Any]:
        """Validate a category and return detailed status."""
        if category_name not in get_current_config().categories:
            return {
                'valid': False,
                'error': f"Category '{category_name}' not found"
            }

        sources = self.category_resolver.resolve_category(category_name)
        category_info = self.category_resolver.get_category_info(category_name)

        return {
            'valid': True,
            'category_info': category_info,
            'resolved_sources': sources,
            'available_source_count': len(sources)
        }


# Global service instance
_search_service: ConfigurableSearchService | None = None


def get_search_service() -> ConfigurableSearchService:
    """Get or create the global configurable search service."""
    global _search_service
    if _search_service is None:
        _search_service = ConfigurableSearchService()
    return _search_service
