"""
Configuration and settings for the Scholarly MCP server.
"""

import os
from dataclasses import dataclass
from typing import Optional
from diskcache import Cache

# Global cache instance
cache = Cache('/tmp/scholarly-mcp-cache', size_limit=1e9)  # 1GB cache

@dataclass
class APIConfig:
    """Configuration loaded from environment variables"""
    semantic_scholar_api_key: Optional[str] = None
    scraperapi_key: Optional[str] = None
    crossref_email: str = "research@example.com"
    max_retries: int = 3
    base_delay: float = 1.0

    # New API keys for additional sources
    core_api_key: Optional[str] = None

    # Feature flags
    enable_fallback_search: bool = True
    enable_topic_detection: bool = True
    enable_query_reformulation: bool = True
    enable_enhanced_logging: bool = True

    def __post_init__(self):
        # Load from environment
        self.semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.scraperapi_key = os.getenv("SCRAPERAPI_KEY")
        self.crossref_email = os.getenv("CROSSREF_EMAIL", self.crossref_email)

        # New API keys
        self.core_api_key = os.getenv("CORE_API_KEY")

        # Feature flags from environment (default to True for new features)
        self.enable_fallback_search = os.getenv("ENABLE_FALLBACK_SEARCH", "true").lower() == "true"
        self.enable_topic_detection = os.getenv("ENABLE_TOPIC_DETECTION", "true").lower() == "true"
        self.enable_query_reformulation = os.getenv("ENABLE_QUERY_REFORMULATION", "true").lower() == "true"
        self.enable_enhanced_logging = os.getenv("ENABLE_ENHANCED_LOGGING", "true").lower() == "true"

# Global configuration
config = APIConfig()

# API health status
api_status = {
    "crossref": True,
    "semantic_scholar": True,
    "arxiv": True,
    "pubmed": True,
    "google_scholar": True,
    "core": True,
    "doaj": True,
    "socarxiv": True,
    "osf_preprints": True
}