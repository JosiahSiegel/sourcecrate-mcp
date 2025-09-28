"""API clients for various academic databases."""

from .arxiv_client import search_arxiv
from .base_client import BaseAPIClient
from .generic_http_client import GenericHTTPClient
from .google_scholar_client import search_google_scholar_fallback, setup_scholarly_proxy
from .pubmed_client import search_pubmed, search_pubmed_central

# clinicaltrials_client removed - now config-based

__all__ = [
    "BaseAPIClient",
    "search_arxiv",
    "search_pubmed",
    "search_pubmed_central",
    # clinicaltrials functions removed - now config-based
    "search_google_scholar_fallback",
    "setup_scholarly_proxy",
    "GenericHTTPClient",
]
