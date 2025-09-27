"""API clients for various academic databases."""

from .base_client import BaseAPIClient
from .arxiv_client import search_arxiv
from .pubmed_client import search_pubmed, search_pubmed_central
# clinicaltrials_client removed - now config-based
from .google_scholar_client import search_google_scholar_fallback, setup_scholarly_proxy
from .generic_http_client import GenericHTTPClient

__all__ = [
    "BaseAPIClient",
    "search_arxiv",
    "search_pubmed",
    "search_pubmed_central",
    # clinicaltrials functions removed - now config-based
    "search_google_scholar_fallback",
    "setup_scholarly_proxy",
    "GenericHTTPClient"
]