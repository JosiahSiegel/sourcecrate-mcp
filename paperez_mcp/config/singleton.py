"""
Configuration singleton manager for PaperezMCP.

This module implements a thread-safe singleton pattern for configuration management,
following industry best practices to ensure reliable initialization across all environments.
"""

import logging
import threading
from typing import Any, Optional

from paperez_mcp.config import get_current_config, initialize_configuration_system
from paperez_mcp.config.schemas import PaperezConfig

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Thread-safe singleton for configuration management.

    This class ensures configuration is loaded exactly once and cached properly,
    avoiding the timing issues that occur with module-level initialization.
    """

    _instance: Optional['ConfigurationManager'] = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls) -> 'ConfigurationManager':
        """Ensure only one instance exists."""
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the configuration manager."""
        # Prevent re-initialization
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            self._config: Optional[PaperezConfig] = None
            self._search_service: Optional[Any] = None
            self._api_status: dict[str, bool] = {}
            self._search_functions: dict[str, Any] = {}
            self._initialization_error: Optional[str] = None
            self._initialized = True

    def initialize(self) -> bool:
        """Initialize configuration and services.

        Returns:
            True if initialization succeeded, False otherwise.
        """
        if self._config is not None:
            # Already initialized successfully
            return True

        with self._lock:
            # Check again inside lock
            if self._config is not None:
                return True

            try:
                logger.info("Initializing PaperezMCP configuration system...")

                # Initialize configuration system
                self._search_service = initialize_configuration_system(enable_hot_reload=False)

                # Get configuration
                self._config = get_current_config()

                if not self._config or not self._config.sources:
                    raise ValueError("Configuration loaded but no sources found")

                # Build API status
                self._api_status = {
                    source: cfg.enabled
                    for source, cfg in self._config.sources.items()
                }

                # Get search functions
                if self._search_service:
                    self._search_functions = self._search_service.get_search_functions()

                if not self._search_functions:
                    # Try direct import as fallback
                    self._import_search_functions_directly()

                logger.info(
                    f"✓ Configuration initialized: "
                    f"{len(self._api_status)} sources, "
                    f"{len(self._search_functions)} search functions"
                )

                self._initialization_error = None
                return True

            except Exception as e:
                error_msg = f"Configuration initialization failed: {e}"
                logger.error(error_msg)
                self._initialization_error = str(e)

                # Set minimal defaults to prevent complete failure
                self._set_minimal_defaults()
                return False

    def _import_search_functions_directly(self) -> None:
        """Import search functions directly as a fallback."""
        try:
            import importlib

            # Essential search functions to import
            imports = [
                ("arxiv", "paperez_mcp.api_clients.arxiv_client", "search_arxiv"),
                ("pubmed", "paperez_mcp.api_clients.pubmed_client", "search_pubmed"),
                ("pubmed_central", "paperez_mcp.api_clients.pubmed_client", "search_pubmed_central"),
                ("crossref", "paperez_mcp.api_clients.crossref_client", "search_crossref"),
                ("semantic_scholar", "paperez_mcp.api_clients.semantic_scholar_client", "search_semantic_scholar"),
            ]

            for name, module_path, func_name in imports:
                try:
                    module = importlib.import_module(module_path)
                    self._search_functions[name] = getattr(module, func_name)
                except Exception as e:
                    logger.warning(f"Could not import {name}: {e}")

        except Exception as e:
            logger.error(f"Failed to import search functions directly: {e}")

    def _set_minimal_defaults(self) -> None:
        """Set minimal defaults to prevent complete failure."""
        logger.info("Setting minimal defaults for basic operation")

        # Minimal API status
        self._api_status = {
            "arxiv": True,
            "pubmed": True,
            "pubmed_central": True,
            "crossref": True,
            "semantic_scholar": True,
        }

        # Try to import at least arxiv and pubmed
        try:
            from paperez_mcp.api_clients.arxiv_client import search_arxiv
            from paperez_mcp.api_clients.pubmed_client import search_pubmed, search_pubmed_central

            self._search_functions = {
                "arxiv": search_arxiv,
                "pubmed": search_pubmed,
                "pubmed_central": search_pubmed_central,
            }
        except Exception as e:
            logger.error(f"Could not import even minimal search functions: {e}")
            self._search_functions = {}

    @property
    def config(self) -> Optional[PaperezConfig]:
        """Get configuration, initializing if needed."""
        if self._config is None:
            self.initialize()
        return self._config

    @property
    def api_status(self) -> dict[str, bool]:
        """Get API status, initializing if needed."""
        if not self._api_status:
            self.initialize()
        return self._api_status

    @property
    def search_functions(self) -> dict[str, Any]:
        """Get search functions, initializing if needed."""
        if not self._search_functions:
            self.initialize()
        return self._search_functions

    @property
    def search_service(self) -> Optional[Any]:
        """Get search service, initializing if needed."""
        if self._search_service is None:
            self.initialize()
        return self._search_service

    @property
    def is_initialized(self) -> bool:
        """Check if configuration is initialized."""
        return self._config is not None

    @property
    def initialization_error(self) -> Optional[str]:
        """Get initialization error if any."""
        return self._initialization_error

    def get_status(self) -> dict[str, Any]:
        """Get current configuration status."""
        return {
            "initialized": self.is_initialized,
            "sources_count": len(self._api_status),
            "search_functions_count": len(self._search_functions),
            "has_config": self._config is not None,
            "has_search_service": self._search_service is not None,
            "initialization_error": self._initialization_error,
        }


# Global singleton instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager singleton.

    Returns:
        The ConfigurationManager singleton instance.
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager