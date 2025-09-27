"""
Default configuration for PaperezMCP - Built-in sources and categories.
Provides sensible defaults that can be overridden by user configurations.
"""

from typing import Dict, Any


def get_default_config() -> Dict[str, Any]:
    """Get the default PaperezMCP configuration."""
    return {
        'version': '1.0',
        'default_category': 'comprehensive',
        'max_concurrent_searches': 10,
        'global_cache_enabled': True,
        'global_cache_expire': 3600,
        'default_output_dir': '.paperez',
        'cleanup_temp_files': True,

        # Query routing configuration
        'routing': {
            'enabled': True,
            'fallback_enabled': True,
            'domain_keywords': {
                'medical': [
                    'medical', 'clinical', 'patient', 'treatment', 'therapy',
                    'disease', 'diagnosis', 'health', 'medicine', 'pharmaceutical',
                    'healthcare', 'hospital', 'surgery', 'medication', 'vaccine'
                ],
                'computer_science': [
                    'algorithm', 'machine learning', 'artificial intelligence',
                    'neural', 'deep learning', 'computer', 'software', 'programming',
                    'data science', 'computational', 'neural network', 'AI'
                ],
                'physics': [
                    'quantum', 'physics', 'engineering', 'materials', 'energy',
                    'electromagnetic', 'mechanical', 'thermal', 'optical'
                ]
            },
            'domain_categories': {
                'medical': 'medical',
                'computer_science': 'preprints',
                'physics': 'preprints',
                'general': 'comprehensive'
            }
        },

        # Built-in source providers
        'sources': {
            'crossref': {
                'name': 'crossref',
                'type': 'http_api',
                'enabled': True,
                'timeout': 30,
                'max_retries': 3,
                'cache_expire': 3600,
                'config': {
                    'description': 'Primary academic publisher database',
                    'coverage': 'peer-reviewed articles, books, conference papers',
                    'base_url': 'https://api.crossref.org',
                    'search_path': '/works',
                    'query_param': 'query',
                    'limit_param': 'rows',
                    'response_format': 'json',
                    'results_path': 'message.items',
                    'extra_params': {
                        'sort': 'relevance',
                        'order': 'desc',
                        'mailto': 'research@paperez.org'  # Default, users can override
                    },
                    'field_mappings': {
                        'title': 'title.0',
                        'authors': 'author',
                        'doi': 'DOI',
                        'abstract': 'abstract',
                        'journal': 'container-title.0',
                        'year': 'published-print.date-parts.0.0',
                        'url': 'URL',
                        'citation_count': 'is-referenced-by-count'
                    },
                    'rate_limit_delay': 0.1
                }
            },
            'semantic_scholar': {
                'name': 'semantic_scholar',
                'type': 'http_api',
                'enabled': True,
                'timeout': 30,
                'max_retries': 3,
                'cache_expire': 3600,
                'config': {
                    'description': 'AI-powered academic search engine',
                    'coverage': 'computer science, neuroscience, biomedical',
                    'base_url': 'https://api.semanticscholar.org/graph/v1',
                    'search_path': '/paper/search',
                    'query_param': 'query',
                    'limit_param': 'limit',
                    'response_format': 'json',
                    'results_path': 'data',
                    'extra_params': {
                        'fields': 'paperId,title,authors,year,abstract,venue,citationCount,url,openAccessPdf'
                    },
                    'field_mappings': {
                        'title': 'title',
                        'authors': 'authors',
                        'year': 'year',
                        'abstract': 'abstract',
                        'journal': 'venue',
                        'doi': 'externalIds.DOI',
                        'url': 'url',
                        'pdf_url': 'openAccessPdf.url',
                        'citation_count': 'citationCount'
                    },
                    'api_key': '',  # Users can provide their API key
                    'auth_header': 'x-api-key',
                    'auth_type': 'ApiKey',
                    'rate_limit_delay': 0.1
                }
            },
            'arxiv': {
                'name': 'arxiv',
                'type': 'builtin',
                'enabled': True,
                'function_name': 'search_arxiv',
                'timeout': 30,
                'max_retries': 3,
                'cache_expire': 3600,
                'config': {
                    'description': 'Preprint repository for STEM fields',
                    'coverage': 'physics, mathematics, computer science, biology'
                }
            },
            'pubmed': {
                'name': 'pubmed',
                'type': 'builtin',
                'enabled': True,
                'function_name': 'search_pubmed',
                'timeout': 30,
                'max_retries': 3,
                'cache_expire': 3600,
                'config': {
                    'description': 'Biomedical literature database',
                    'coverage': 'life sciences, biomedical research'
                }
            },
            'pubmed_central': {
                'name': 'pubmed_central',
                'type': 'builtin',
                'enabled': True,
                'function_name': 'search_pubmed_central',
                'timeout': 30,
                'max_retries': 3,
                'cache_expire': 3600,
                'config': {
                    'description': 'Full-text biomedical literature repository',
                    'coverage': 'open access medical and life science articles'
                }
            },
            'clinicaltrials': {
                'name': 'clinicaltrials',
                'type': 'builtin',
                'enabled': True,
                'function_name': 'search_clinicaltrials',
                'timeout': 30,
                'max_retries': 3,
                'cache_expire': 3600,
                'config': {
                    'description': 'Clinical trials database',
                    'coverage': 'clinical studies, medical trials'
                }
            },
            'google_scholar': {
                'name': 'google_scholar',
                'type': 'builtin',
                'enabled': True,
                'function_name': 'search_google_scholar_fallback',
                'timeout': 45,
                'max_retries': 2,
                'cache_expire': 7200,
                'config': {
                    'description': 'Google Scholar fallback search',
                    'coverage': 'broad academic content across all disciplines'
                }
            },

            # Config-based HTTP API sources (no Python code needed!)
            'europe_pmc': {
                'name': 'europe_pmc',
                'type': 'http_api',
                'enabled': True,
                'timeout': 30,
                'max_retries': 3,
                'cache_expire': 3600,
                'config': {
                    'description': 'Europe PMC - Life sciences database with 39M+ abstracts',
                    'coverage': 'biomedical and life sciences literature',
                    'base_url': 'https://www.ebi.ac.uk/europepmc/webservices/rest',
                    'search_path': '/search',
                    'query_param': 'query',
                    'limit_param': 'pageSize',
                    'response_format': 'json',
                    'results_path': 'resultList.result',
                    'extra_params': {
                        'format': 'json',
                        'resultType': 'core'
                    },
                    'field_mappings': {
                        'title': 'title',
                        'authors': 'authorString',
                        'abstract': 'abstractText',
                        'journal': 'journalTitle',
                        'year': 'pubYear',
                        'doi': 'doi',
                        'url': 'fullTextUrlList.fullTextUrl.0.url',
                        'citation_count': 'citedByCount'
                    },
                    'rate_limit_delay': 0.2
                }
            },
            'doaj': {
                'name': 'doaj',
                'type': 'http_api',
                'enabled': True,
                'timeout': 30,
                'max_retries': 3,
                'cache_expire': 3600,
                'config': {
                    'description': 'Directory of Open Access Journals - 2.1M+ open access articles',
                    'coverage': 'peer-reviewed open access articles across all subjects',
                    'base_url': 'https://doaj.org/api/search',
                    'search_path': '/articles/_search',
                    'query_param': 'q',
                    'limit_param': 'pageSize',
                    'response_format': 'json',
                    'results_path': 'results',
                    'field_mappings': {
                        'title': 'bibjson.title',
                        'authors': 'bibjson.author',
                        'abstract': 'bibjson.abstract',
                        'journal': 'bibjson.journal.title',
                        'year': 'bibjson.year',
                        'doi': 'bibjson.identifier.0.id',
                        'url': 'bibjson.link.0.url'
                    },
                    'rate_limit_delay': 0.5
                }
            },
            'core_ac_uk': {
                'name': 'core_ac_uk',
                'type': 'http_api',
                'enabled': False,  # Requires API key
                'timeout': 30,
                'max_retries': 3,
                'cache_expire': 3600,
                'config': {
                    'description': 'CORE - Open access research papers aggregator',
                    'coverage': 'open access papers from repositories worldwide',
                    'base_url': 'https://api.core.ac.uk/v3',
                    'search_path': '/search/works',
                    'query_param': 'q',
                    'limit_param': 'limit',
                    'response_format': 'json',
                    'results_path': 'results',
                    'api_key': '',  # User must provide
                    'auth_header': 'Authorization',
                    'auth_type': 'Bearer',
                    'field_mappings': {
                        'title': 'title',
                        'authors': 'authors',
                        'abstract': 'abstract',
                        'journal': 'journals.0.title',
                        'year': 'yearPublished',
                        'doi': 'doi',
                        'url': 'downloadUrl',
                        'pdf_url': 'fullTextPdfUrl'
                    },
                    'rate_limit_delay': 0.1
                }
            }
        },

        # Built-in categories
        'categories': {
            'comprehensive': {
                'name': 'comprehensive',
                'display_name': 'Comprehensive Search',
                'description': 'Search across all available sources for maximum coverage',
                'type': 'standard',
                'sources': [
                    'crossref', 'semantic_scholar', 'arxiv', 'pubmed',
                    'pubmed_central', 'clinicaltrials', 'europe_pmc', 'doaj'
                ],
                'max_results_per_source': 4,
                'parallel_search': True
            },
            'preprints': {
                'name': 'preprints',
                'display_name': 'Preprints & Latest Research',
                'description': 'Focus on preprint repositories for cutting-edge research',
                'type': 'standard',
                'sources': ['arxiv', 'semantic_scholar'],
                'max_results_per_source': 8,
                'parallel_search': True
            },
            'journals': {
                'name': 'journals',
                'display_name': 'Peer-Reviewed Journals',
                'description': 'Focus on peer-reviewed academic publications',
                'type': 'standard',
                'sources': ['crossref', 'pubmed'],
                'max_results_per_source': 8,
                'parallel_search': True
            },
            'medical': {
                'name': 'medical',
                'display_name': 'Medical & Biomedical Research',
                'description': 'Specialized medical and healthcare research',
                'type': 'standard',
                'sources': ['pubmed', 'pubmed_central', 'clinicaltrials'],
                'max_results_per_source': 8,
                'parallel_search': True
            },
            'open_access': {
                'name': 'open_access',
                'display_name': 'Open Access Publications',
                'description': 'Focus on freely available full-text articles',
                'type': 'standard',
                'sources': ['arxiv', 'pubmed_central', 'semantic_scholar', 'doaj', 'europe_pmc'],
                'max_results_per_source': 6,
                'parallel_search': True
            },
            'recent': {
                'name': 'recent',
                'display_name': 'Recent Publications',
                'description': 'Emphasize recent publications and preprints',
                'type': 'standard',
                'sources': ['arxiv', 'semantic_scholar', 'pubmed_central'],
                'max_results_per_source': 8,
                'parallel_search': True
            },
            'historical': {
                'name': 'historical',
                'display_name': 'Historical & Archive Sources',
                'description': 'Focus on historical and archival academic content',
                'type': 'standard',
                'sources': ['crossref', 'google_scholar'],
                'max_results_per_source': 10,
                'parallel_search': True
            },

            # Meta-categories that combine multiple categories
            'ai_research': {
                'name': 'ai_research',
                'display_name': 'AI & Machine Learning Research',
                'description': 'Comprehensive AI research across preprints and journals',
                'type': 'meta',
                'includes': ['preprints', 'journals'],
                'merge_strategy': 'weighted_union',
                'weights': {
                    'preprints': 0.7,  # Emphasize latest AI research
                    'journals': 0.3
                }
            },
            'medical_comprehensive': {
                'name': 'medical_comprehensive',
                'display_name': 'Comprehensive Medical Research',
                'description': 'All medical sources plus relevant general sources',
                'type': 'meta',
                'includes': ['medical', 'journals'],
                'merge_strategy': 'weighted_union',
                'weights': {
                    'medical': 0.8,
                    'journals': 0.2
                }
            },
            'interdisciplinary': {
                'name': 'interdisciplinary',
                'display_name': 'Interdisciplinary Research',
                'description': 'Broad search across multiple domains',
                'type': 'meta',
                'includes': ['comprehensive', 'preprints'],
                'merge_strategy': 'union'
            }
        }
    }


def get_builtin_source_names() -> list[str]:
    """Get list of built-in source names."""
    config = get_default_config()
    return [
        name for name, source_config in config['sources'].items()
        if source_config['type'] == 'builtin'
    ]


def get_builtin_category_names() -> list[str]:
    """Get list of built-in category names."""
    config = get_default_config()
    return list(config['categories'].keys())


def get_source_function_mapping() -> Dict[str, str]:
    """Get mapping of source names to their function names."""
    config = get_default_config()
    return {
        name: source_config['function_name']
        for name, source_config in config['sources'].items()
        if source_config['type'] == 'builtin' and 'function_name' in source_config
    }