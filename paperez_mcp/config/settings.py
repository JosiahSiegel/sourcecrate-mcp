"""
Configuration and settings for the Scholarly MCP server.
"""

import os
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from diskcache import Cache  # type: ignore[import-untyped]

# Global cache instance
cache = Cache("/tmp/scholarly-mcp-cache", size_limit=1e9)  # 1GB cache


@dataclass
class APIConfig:
    """Configuration loaded from environment variables"""

    semantic_scholar_api_key: str | None = None
    scraperapi_key: str | None = None
    crossref_email: str = "research@example.com"
    max_retries: int = 3
    base_delay: float = 1.0

    # New API keys for additional sources
    core_api_key: str | None = None

    # Feature flags
    enable_fallback_search: bool = True
    enable_topic_detection: bool = True
    enable_query_reformulation: bool = True
    enable_enhanced_logging: bool = True

    # Performance settings
    max_concurrent_sources: int = 5  # Maximum sources to search in parallel
    enable_parallel_search: bool = True  # Enable/disable parallel search

    def __post_init__(self) -> None:
        # Load from environment
        self.semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.scraperapi_key = os.getenv("SCRAPERAPI_KEY")
        self.crossref_email = os.getenv("CROSSREF_EMAIL", self.crossref_email)

        # New API keys
        self.core_api_key = os.getenv("CORE_API_KEY")

        # Feature flags from environment (default to True for new features)
        self.enable_fallback_search = (
            os.getenv("ENABLE_FALLBACK_SEARCH", "true").lower() == "true"
        )
        self.enable_topic_detection = (
            os.getenv("ENABLE_TOPIC_DETECTION", "true").lower() == "true"
        )
        self.enable_query_reformulation = (
            os.getenv("ENABLE_QUERY_REFORMULATION", "true").lower() == "true"
        )
        self.enable_enhanced_logging = (
            os.getenv("ENABLE_ENHANCED_LOGGING", "true").lower() == "true"
        )

        # Performance settings from environment
        self.max_concurrent_sources = int(os.getenv("MAX_CONCURRENT_SOURCES", "5"))
        self.enable_parallel_search = (
            os.getenv("ENABLE_PARALLEL_SEARCH", "true").lower() == "true"
        )


# Global configuration
config = APIConfig()


# Dynamic API health status - populated from configuration
class DynamicAPIStatus(dict):
    """Dynamic API status tracking that supports infinite custom sources."""

    def __init__(self) -> None:
        super().__init__()
        self._status: dict[str, bool] = {}
        self._initialize_from_config()
        # Sync the dict contents with our internal status
        self.clear()
        self.update(self._status)

    def _initialize_from_config(self) -> None:
        """Initialize API status from current configuration."""
        try:
            from . import get_current_config

            config = get_current_config()
            if config and config.sources:
                # Initialize all configured sources as available
                for source_name, source_config in config.sources.items():
                    if getattr(source_config, "enabled", False):
                        self._status[source_name] = True
                    else:
                        self._status[source_name] = False
            else:
                # Fallback - initialize with basic sources
                default_sources = [
                    "crossref",
                    "semantic_scholar",
                    "arxiv",
                    "pubmed",
                    "pubmed_central",
                    "clinicaltrials",
                    "core",
                    "doaj",
                    "socarxiv",
                    "osf_preprints",
                ]
                for source in default_sources:
                    self._status[source] = True
        except Exception:
            # Fallback if config not available
            default_sources = [
                "crossref",
                "semantic_scholar",
                "arxiv",
                "pubmed",
                "pubmed_central",
                "clinicaltrials",
                "core",
                "doaj",
                "socarxiv",
                "osf_preprints",
            ]
            for source in default_sources:
                self._status[source] = True

    def get(self, source_name: str, default: bool = True) -> bool:  # type: ignore[override]
        """Get API status for a source with dynamic fallback for unknown sources."""
        if source_name in self._status:
            return self._status[source_name]

        # For unknown sources, check if they exist in current config
        try:
            from . import get_current_config

            config = get_current_config()
            if config and source_name in config.sources:
                source_config = config.sources[source_name]
                status = getattr(source_config, "enabled", default)
                self._status[source_name] = status  # Cache it
                super().__setitem__(source_name, status)
                return status
        except Exception:
            pass

        # Ultimate fallback
        self._status[source_name] = default
        super().__setitem__(source_name, default)
        return default

    def __getitem__(self, source_name: str) -> bool:
        """Dictionary-style access for backward compatibility."""
        return self.get(source_name, True)

    def __setitem__(self, source_name: str, status: bool) -> None:
        """Set API status for a source."""
        self._status[source_name] = status
        super().__setitem__(source_name, status)

    def copy(self) -> dict[str, bool]:
        """Return a copy of current status for compatibility."""
        return self._status.copy()

    def keys(self) -> Any:
        """Return source names."""
        return self._status.keys()

    def items(self) -> Any:
        """Return status items."""
        return self._status.items()

    def values(self) -> Any:
        """Return status values."""
        return self._status.values()

    def __json__(self) -> dict[str, bool]:
        """Make the object JSON serializable by returning the underlying dict."""
        return self._status.copy()

    def __iter__(self) -> Iterator[str]:
        """Make the object iterable like a dict."""
        return iter(self._status)

    def __len__(self) -> int:
        """Return the number of sources."""
        return len(self._status)


# Create dynamic API status instance
api_status = DynamicAPIStatus()
