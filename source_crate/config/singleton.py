"""
Configuration singleton manager for PaperezMCP.

This module implements a thread-safe singleton pattern for configuration management,
following industry best practices to ensure reliable initialization across all environments.
"""

import logging
import threading
from typing import Any, Optional

from source_crate.config.manager import get_current_config
from source_crate.config.schemas import PaperezConfig

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Thread-safe singleton for configuration management.

    This class ensures configuration is loaded exactly once and cached properly,
    avoiding the timing issues that occur with module-level initialization.
    """

    _instance: Optional["ConfigurationManager"] = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls) -> "ConfigurationManager":
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

            self._config: PaperezConfig | None = None
            self._search_service: Any | None = None
            self._api_status: dict[str, bool] = {}
            self._search_functions: dict[str, Any] = {}
            self._initialization_error: str | None = None
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

                # Get configuration
                self._config = get_current_config()

                # Initialize search service
                from source_crate.config.registry import get_search_service

                self._search_service = get_search_service()

                if not self._config or not self._config.sources:
                    raise ValueError("Configuration loaded but no sources found")

                # Build API status
                self._api_status = {
                    source: cfg.enabled for source, cfg in self._config.sources.items()
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
        """Import builtin search functions as a fallback."""
        try:
            # Import only the minimal builtin functions
            # Everything else should be handled by generic HTTP client via YAML config
            from source_crate.builtin_functions import (
                search_arxiv,
                search_pubmed,
                search_pubmed_central,
            )

            self._search_functions = {
                "arxiv": search_arxiv,
                "pubmed": search_pubmed,
                "pubmed_central": search_pubmed_central,
            }

            logger.info(
                f"Imported {len(self._search_functions)} builtin search functions"
            )

        except Exception as e:
            logger.error(f"Failed to import builtin search functions: {e}")

    def _set_minimal_defaults(self) -> None:
        """Set defaults by importing search functions directly and building minimal config."""
        logger.info("Setting defaults using direct imports")

        # First, import all available search functions
        self._import_search_functions_directly()

        # Set API status based on available functions and YAML config
        # Start with builtin functions
        self._api_status = {
            "arxiv": "arxiv" in self._search_functions,
            "pubmed": "pubmed" in self._search_functions,
            "pubmed_central": "pubmed_central" in self._search_functions,
        }

        # Add other sources from config if available
        if self._config and self._config.sources:
            for source_name, source_config in self._config.sources.items():
                if source_name not in self._api_status:
                    self._api_status[source_name] = source_config.enabled

        # If config is not set, try to load it from YAML files
        if not self._config:
            try:
                # Force configuration reload
                from source_crate.config import get_current_config

                self._config = get_current_config()
                if self._config:
                    logger.info("Loaded configuration from YAML files")
            except Exception as e:
                logger.error(f"Could not load configuration: {e}")

        logger.info(f"Set defaults with {len(self._search_functions)} search functions")

    @property
    def config(self) -> PaperezConfig | None:
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
    def search_service(self) -> Any | None:
        """Get search service, initializing if needed."""
        if self._search_service is None:
            self.initialize()
        return self._search_service

    @property
    def is_initialized(self) -> bool:
        """Check if configuration is initialized."""
        return self._config is not None

    @property
    def initialization_error(self) -> str | None:
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
_config_manager: ConfigurationManager | None = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager singleton.

    Returns:
        The ConfigurationManager singleton instance.
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager
