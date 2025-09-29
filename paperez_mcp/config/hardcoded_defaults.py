"""
Hardcoded default configuration for PaperezMCP.

This module provides a complete working configuration in Python code
as the ultimate fallback when YAML files cannot be loaded. This ensures
the MCP server works in all invocation scenarios, including when invoked
from external paths where package data may not be accessible.

This configuration mirrors the YAML defaults but is maintained in Python
to guarantee availability regardless of packaging or path issues.
"""

def get_hardcoded_config() -> dict:
    """
    Return a complete hardcoded configuration dictionary.

    This provides the same configuration as the default YAML files but
    in Python code, ensuring the server always has a working config.
    """
    return {
        "version": "1.0",
        "default_category": None,  # Use intelligent routing
        "max_concurrent_searches": 15,
        "global_cache_enabled": True,
        "global_cache_expire": 7200,
        "default_output_dir": ".paperez",
        "cleanup_temp_files": True,
        "use_default_sources": True,

        # Complete sources configuration
        "sources": {
            # Academic databases
            "arxiv": {
                "name": "arxiv",
                "enabled": True,
                "base_url": "https://export.arxiv.org/api",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 0.33},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
            },
            "pubmed": {
                "name": "pubmed",
                "enabled": True,
                "base_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 3},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
                "email": "research@example.com",
            },
            "pubmed_central": {
                "name": "pubmed_central",
                "enabled": True,
                "base_url": "https://www.ncbi.nlm.nih.gov/pmc",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 3},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
            },
            "semantic_scholar": {
                "name": "semantic_scholar",
                "enabled": True,
                "base_url": "https://api.semanticscholar.org/graph/v1",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 1},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
            },
            "crossref": {
                "name": "crossref",
                "enabled": True,
                "base_url": "https://api.crossref.org",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 50},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
                "mailto": "research@example.com",
            },
            "europe_pmc": {
                "name": "europe_pmc",
                "enabled": True,
                "base_url": "https://www.ebi.ac.uk/europepmc/webservices/rest",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 10},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
            },
            "doaj": {
                "name": "doaj",
                "enabled": True,
                "base_url": "https://doaj.org/api/v3",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 2},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
            },
            "clinicaltrials": {
                "name": "clinicaltrials",
                "enabled": True,
                "base_url": "https://clinicaltrials.gov/api",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 1},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
            },
            "openalex": {
                "name": "openalex",
                "enabled": True,
                "base_url": "https://api.openalex.org",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 10},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
                "mailto": "research@example.com",
            },
            "openlibrary": {
                "name": "openlibrary",
                "enabled": True,
                "base_url": "https://openlibrary.org",
                "timeout": 30,
                "max_results_per_page": 100,
                "rate_limit": {"requests_per_second": 1},
                "retry": {"max_attempts": 3, "backoff": 1.5},
                "authentication": None,
            },
            # Disabled sources
            "core_repository": {"name": "core_repository", "enabled": False},
            "repec": {"name": "repec", "enabled": False},
            "federal_register": {"name": "federal_register", "enabled": False},
            "hathitrust": {"name": "hathitrust", "enabled": False},
            "internet_archive": {"name": "internet_archive", "enabled": False},
            "courtlistener": {"name": "courtlistener", "enabled": False},
        },

        # Complete categories configuration
        "categories": {
            "medical": {
                "name": "medical",
                "display_name": "Medical & Biomedical Research",
                "description": "Specialized medical and healthcare research",
                "type": "standard",
                "sources": ["pubmed", "pubmed_central", "openalex", "clinicaltrials", "europe_pmc"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 6,
                "parallel_search": True,
            },
            "preprints": {
                "name": "preprints",
                "display_name": "Preprints & Latest Research",
                "description": "Focus on preprint repositories for cutting-edge research",
                "type": "standard",
                "sources": ["arxiv", "semantic_scholar", "openalex"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 6,
                "parallel_search": True,
            },
            "academic_premium": {
                "name": "academic_premium",
                "display_name": "Premium Academic Sources",
                "description": "High-quality peer-reviewed sources for authoritative research",
                "type": "standard",
                "sources": ["crossref", "semantic_scholar", "openalex", "doaj"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 6,
                "parallel_search": True,
            },
            "open_access": {
                "name": "open_access",
                "display_name": "Open Access Publications",
                "description": "Focus on freely available full-text articles",
                "type": "standard",
                "sources": ["arxiv", "semantic_scholar", "openalex", "doaj"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 5,
                "parallel_search": True,
            },
            "business": {
                "name": "business",
                "display_name": "Business & Economics Research",
                "description": "Business, economics, finance, and management research",
                "type": "standard",
                "sources": ["openalex", "crossref", "semantic_scholar"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 6,
                "parallel_search": True,
            },
            "social_sciences": {
                "name": "social_sciences",
                "display_name": "Social Sciences Research",
                "description": "Psychology, sociology, education, anthropology, and political science",
                "type": "standard",
                "sources": ["openalex", "semantic_scholar"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 6,
                "parallel_search": True,
            },
            "humanities": {
                "name": "humanities",
                "display_name": "Humanities Research",
                "description": "Literature, philosophy, arts, cultural studies, and languages",
                "type": "standard",
                "sources": ["openlibrary"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 8,
                "parallel_search": True,
            },
            "historical": {
                "name": "historical",
                "display_name": "Historical & Archive Sources",
                "description": "Focus on historical and archival content including government documents",
                "type": "standard",
                "sources": ["crossref"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 8,
                "parallel_search": True,
            },
            "legal_research": {
                "name": "legal_research",
                "display_name": "Legal Research",
                "description": "Case law, court opinions, and legal scholarship",
                "type": "standard",
                "sources": ["crossref"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 8,
                "parallel_search": True,
            },
            "government_policy": {
                "name": "government_policy",
                "display_name": "Government & Policy Research",
                "description": "Federal regulations, policy documents, and government publications",
                "type": "standard",
                "sources": ["crossref"],
                "includes": [],
                "merge_strategy": "union",
                "weights": {},
                "max_results_per_source": 8,
                "parallel_search": True,
            },
        },

        # Routing configuration
        "routing": {
            "enabled": True,
            "fallback_enabled": True,
            "domain_keywords": {
                "medical": [
                    "medical", "clinical", "patient", "treatment", "therapy",
                    "diagnosis", "biomedical", "healthcare", "pharmaceutical"
                ],
                "computer_science": [
                    "algorithm", "machine learning", "artificial intelligence",
                    "neural", "deep learning", "AI", "computer", "software", "programming"
                ],
                "physics": [
                    "quantum", "physics", "engineering", "materials",
                    "energy", "chemistry", "mathematics"
                ],
                "historical": [
                    "history", "historical", "archive", "government",
                    "document", "policy", "genealogy"
                ],
                "business": [
                    "business", "economics", "finance", "management",
                    "corporate", "entrepreneurship", "marketing"
                ],
                "social_sciences": [
                    "psychology", "sociology", "education", "anthropology",
                    "political", "social", "behavior"
                ],
                "humanities": [
                    "literature", "philosophy", "art", "culture",
                    "language", "religion", "humanities"
                ],
                "legal": [
                    "law", "legal", "court", "statute",
                    "regulation", "constitutional", "jurisprudence"
                ],
            },
            "domain_categories": {
                "medical": "medical",
                "computer_science": "preprints",
                "physics": "preprints",
                "historical": "historical",
                "business": "business",
                "social_sciences": "social_sciences",
                "humanities": "humanities",
                "legal": "legal_research",
                "general": None,
            },
        },
    }


def get_search_function_imports() -> dict:
    """
    Return a dictionary of search function imports.

    This provides direct imports of all search functions to ensure
    they're available even if configuration loading fails.
    """
    search_funcs = {}

    # Import all available search functions with error handling
    import_specs = [
        ("arxiv", "paperez_mcp.api_clients.arxiv_client", "search_arxiv"),
        ("pubmed", "paperez_mcp.api_clients.pubmed_client", "search_pubmed"),
        ("pubmed_central", "paperez_mcp.api_clients.pubmed_client", "search_pubmed_central"),
        ("crossref", "paperez_mcp.api_clients.crossref_client", "search_crossref"),
        ("semantic_scholar", "paperez_mcp.api_clients.semantic_scholar_client", "search_semantic_scholar"),
        ("europe_pmc", "paperez_mcp.api_clients.generic_http_client", "search_europe_pmc"),
        ("doaj", "paperez_mcp.api_clients.generic_http_client", "search_doaj"),
        ("clinicaltrials", "paperez_mcp.api_clients.generic_http_client", "search_clinicaltrials"),
        ("openalex", "paperez_mcp.api_clients.generic_http_client", "search_openalex"),
        ("openlibrary", "paperez_mcp.api_clients.generic_http_client", "search_openlibrary"),
    ]

    for name, module_path, func_name in import_specs:
        try:
            import importlib
            module = importlib.import_module(module_path)
            if hasattr(module, func_name):
                search_funcs[name] = getattr(module, func_name)
        except Exception:
            # Silently skip functions that can't be imported
            pass

    return search_funcs