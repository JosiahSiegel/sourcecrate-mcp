"""API clients for academic databases - all configuration-driven.

This module contains only generic clients. All source-specific behavior
is determined by YAML configuration files in paperez_mcp/default_configs/.

No provider-specific client files should exist here.
"""

from .base_client import BaseAPIClient
from .generic_http_client import GenericHTTPClient

__all__ = [
    "BaseAPIClient",
    "GenericHTTPClient",
]
