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

    def __post_init__(self):
        # Load from environment
        self.semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.scraperapi_key = os.getenv("SCRAPERAPI_KEY")
        self.crossref_email = os.getenv("CROSSREF_EMAIL", self.crossref_email)

# Global configuration
config = APIConfig()

# API health status
api_status = {
    "crossref": True,
    "semantic_scholar": True,
    "arxiv": True,
    "pubmed": True,
    "google_scholar": True
}