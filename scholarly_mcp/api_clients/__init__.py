"""API clients for various academic databases."""

from .crossref_client import search_crossref
from .semantic_scholar_client import search_semantic_scholar
from .arxiv_client import search_arxiv
from .pubmed_client import search_pubmed
from .google_scholar_client import search_google_scholar_fallback, setup_scholarly_proxy
from .http_client import create_http_client

__all__ = [
    "search_crossref",
    "search_semantic_scholar",
    "search_arxiv",
    "search_pubmed",
    "search_google_scholar_fallback",
    "setup_scholarly_proxy",
    "create_http_client"
]