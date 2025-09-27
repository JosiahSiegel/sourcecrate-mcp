"""API clients for various academic databases."""

from .base_client import BaseAPIClient
from .crossref_client import search_crossref
from .semantic_scholar_client import search_semantic_scholar
from .arxiv_client import search_arxiv
from .pubmed_client import search_pubmed, search_pubmed_central
from .clinicaltrials_client import search_clinicaltrials, search_clinicaltrials_interventional, search_clinicaltrials_completed
from .google_scholar_client import search_google_scholar_fallback, setup_scholarly_proxy
from .http_client import create_http_client

__all__ = [
    "BaseAPIClient",
    "search_crossref",
    "search_semantic_scholar",
    "search_arxiv",
    "search_pubmed",
    "search_pubmed_central",
    "search_clinicaltrials",
    "search_clinicaltrials_interventional",
    "search_clinicaltrials_completed",
    "search_google_scholar_fallback",
    "setup_scholarly_proxy",
    "create_http_client"
]