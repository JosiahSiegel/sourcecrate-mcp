# Configuration Guide

## Configuration Overview

PaperezMCP uses a dual configuration system:
- **Legacy**: `settings.py` (backward compatibility)
- **New**: YAML-based configuration files

## Configuration Hierarchy

1. Built-in defaults (`.paperez/config/config.yaml`)
2. User home config (`~/.paperez/config/config.yaml`)
3. Project local config (`./paperez/config/config.yaml`)
4. Environment variables

## Quick Configuration

### Basic Setup

Create configuration directory:
```bash
mkdir -p .paperez/config/
```

Create basic config file:
```yaml
version: "1.0"
use_default_sources: true
default_category: comprehensive
max_concurrent_searches: 15
global_cache_enabled: true
default_output_dir: .paperez
```

### Configuration Options

#### Core Settings
- `version`: Configuration version (string, e.g., '1.0')
- `use_default_sources`: Include built-in sources (default: true)
- `default_category`: Default search category (default: 'comprehensive')
- `max_concurrent_searches`: Max parallel searches (default: 15)
- `global_cache_enabled`: Enable caching (default: true)
- `global_cache_expire`: Cache expiration in seconds (default: 7200)
- `default_output_dir`: Default output directory (default: '.paperez')

#### Query Routing
```yaml
routing:
  enabled: true
  fallback_enabled: true
  domain_keywords:
    medical:
      - medical
      - clinical
      - patient
    computer_science:
      - algorithm
      - machine learning
      - AI
```

## Available Sources

- **crossref**: Primary academic publisher database
- **semantic_scholar**: AI-powered academic search engine
- **arxiv**: Preprint repository for STEM fields
- **pubmed**: Biomedical literature database
- **pubmed_central**: Full-text biomedical repository
- **europe_pmc**: European life sciences database
- **doaj**: Directory of Open Access Journals
- **hathitrust**: Historical books and documents
- **internet_archive**: Historical documents and archives
- **ssrn**: Business and economics research
- **clinicaltrials**: Clinical trials database
- **google_scholar**: Google Scholar (disabled by default)

## Available Categories

- **comprehensive**: Search across all available sources (default)
- **academic_premium**: High-quality peer-reviewed sources
- **preprints**: Latest research from preprint repositories
- **medical**: Medical and biomedical research sources
- **open_access**: Freely available full-text articles
- **historical**: Historical and archival content
- **business**: Business, economics, and finance research

## Custom Sources

Add custom HTTP API sources:
```yaml
sources:
  my_custom_api:
    name: my_custom_api
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: My custom academic API
      base_url: https://api.example.com
      search_path: /search
      query_param: q
      limit_param: limit
      response_format: json
      results_path: results
      field_mappings:
        title: title
        authors: authors
        doi: doi
        year: publication_year
        abstract: abstract
        url: url
      rate_limit_delay: 0.5
```

## Custom Categories

Create custom search categories:
```yaml
categories:
  my_category:
    name: my_category
    display_name: My Custom Category
    description: Custom search category
    type: standard
    sources:
      - crossref
      - semantic_scholar
    max_results_per_source: 8
    parallel_search: true
```

## Configuration Examples

### Minimal Configuration
```yaml
version: "1.0"
use_default_sources: false
sources:
  crossref:
    name: crossref
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: Primary academic publisher database
      base_url: https://api.crossref.org
      search_path: /works
      query_param: query
      limit_param: rows
      response_format: json
      results_path: message.items
      field_mappings:
        title: title.0
        authors: author
        doi: DOI
        year: published-print.date-parts.0.0
categories:
  simple:
    name: simple
    display_name: Simple Search
    description: Basic CrossRef search
    type: standard
    sources:
      - crossref
    max_results_per_source: 10
    parallel_search: false
```

### Enhanced Configuration
```yaml
version: "1.0"
use_default_sources: true
# Add custom sources - they will be merged with defaults
sources:
  my_source:
    # custom source configuration
categories:
  my_category:
    # custom category configuration
```

## Get Configuration Help

Use the built-in help tool for complete guidance:
```
"Help me configure paperez-mcp"
```

This provides:
- Complete file paths and directory structure
- Configuration schema and field descriptions
- Practical examples for different use cases
- Troubleshooting guidance