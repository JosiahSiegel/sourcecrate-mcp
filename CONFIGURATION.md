# PaperezMCP Configuration Guide

PaperezMCP uses a YAML-based configuration system that allows you to customize source providers, categories, and search behavior without writing any Python code.

## Configuration Hierarchy

Configuration is loaded in this order (highest priority first):

1. **Environment variables** (`PAPEREZ_*`)
2. **Local project config** (`./paperez.config.yaml`)
3. **User home config** (`~/.paperez/config.yaml`)
4. **Built-in defaults** (`default_config.yaml`)

## Quick Start

### Create Your Custom Config

Create a file named `paperez.config.yaml` in your project directory:

```yaml
# Override default category
default_category: "open_access"

# Add a custom category
categories:
  my_research:
    name: "my_research"
    display_name: "My Research Focus"
    description: "Sources relevant to my specific research area"
    type: "standard"
    sources:
      - "arxiv"
      - "semantic_scholar"
      - "pubmed"
    max_results_per_source: 6
    parallel_search: true

# Configure a new HTTP API source
sources:
  my_university_repo:
    name: "my_university_repo"
    type: "http_api"
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: "University institutional repository"
      coverage: "University research papers and theses"
      base_url: "https://repository.university.edu/api"
      search_path: "/search"
      query_param: "q"
      limit_param: "limit"
      response_format: "json"
      results_path: "results"
      field_mappings:
        title: "title"
        authors: "authors"
        abstract: "abstract"
        year: "year"
        url: "url"
        pdf_url: "pdf_url"
      rate_limit_delay: 0.5
```

### Environment Variables

Override any setting using environment variables:

```bash
export PAPEREZ_DEFAULT_CATEGORY="medical"
export PAPEREZ_CACHE_ENABLED="true"
export PAPEREZ_OUTPUT_DIR="/path/to/papers"
export PAPEREZ_CONFIG_PATH="/path/to/custom/config.yaml"
```

## Configuration Structure

### Top-Level Settings

```yaml
version: "1.0"                    # Configuration version
default_category: "comprehensive" # Default search category
max_concurrent_searches: 10       # Max parallel searches
global_cache_enabled: true        # Enable result caching
global_cache_expire: 3600         # Cache expiration (seconds)
default_output_dir: ".paperez"    # Default download directory
cleanup_temp_files: true          # Clean up temporary files
```

### Source Providers

#### HTTP API Sources (Config-Only)

Perfect for REST APIs - no Python code required:

```yaml
sources:
  my_api_source:
    name: "my_api_source"
    type: "http_api"
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: "Description of the source"
      coverage: "What content it covers"
      base_url: "https://api.example.com"
      search_path: "/search"
      query_param: "query"           # URL parameter for search terms
      limit_param: "limit"           # URL parameter for result limit
      response_format: "json"
      results_path: "data.results"   # JSONPath to results array

      # Optional authentication
      api_key: "your-api-key"
      auth_header: "Authorization"   # Header name
      auth_type: "Bearer"           # "Bearer", "ApiKey", or "Basic"

      # Field mapping from API response to standard format
      field_mappings:
        title: "title"                    # JSONPath to title
        authors: "authors"                # JSONPath to authors array
        abstract: "abstract"              # JSONPath to abstract
        year: "publication_year"          # JSONPath to year
        journal: "journal.name"           # JSONPath to journal
        doi: "identifiers.doi"           # JSONPath to DOI
        url: "url"                       # JSONPath to paper URL
        pdf_url: "files.pdf.url"        # JSONPath to PDF URL
        citation_count: "metrics.citations"

      # Optional extra parameters for all requests
      extra_params:
        format: "json"
        include_metadata: "true"

      rate_limit_delay: 0.5              # Delay between requests
```

#### Builtin Sources (Python-Based)

For complex cases requiring specialized libraries:

```yaml
sources:
  arxiv:
    name: "arxiv"
    type: "builtin"
    enabled: true
    function_name: "search_arxiv"
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: "arXiv preprint repository"
      coverage: "Physics, math, CS, biology preprints"
```

### Categories

#### Standard Categories

Search specific sources:

```yaml
categories:
  medical_focus:
    name: "medical_focus"
    display_name: "Medical Research"
    description: "Biomedical and clinical research"
    type: "standard"
    sources:
      - "pubmed"
      - "pubmed_central"
      - "clinicaltrials"
    max_results_per_source: 8
    parallel_search: true
```

#### Meta-Categories

Combine multiple categories:

```yaml
categories:
  comprehensive_ai:
    name: "comprehensive_ai"
    display_name: "Comprehensive AI Research"
    description: "AI research across preprints and journals"
    type: "meta"
    includes:
      - "preprints"    # Include preprints category
      - "journals"     # Include journals category
    merge_strategy: "weighted_union"
    weights:
      preprints: 0.7  # 70% weight to preprints
      journals: 0.3   # 30% weight to journals
```

### Smart Routing

Automatically select categories based on query content:

```yaml
routing:
  enabled: true
  fallback_enabled: true
  domain_keywords:
    medical:
      - "clinical"
      - "patient"
      - "therapy"
      - "diagnosis"
    ai:
      - "machine learning"
      - "neural network"
      - "artificial intelligence"
  domain_categories:
    medical: "medical"
    ai: "preprints"
    general: "comprehensive"
```

## Built-in Sources

### Config-Based Sources (HTTP APIs)
- **CrossRef**: Primary academic publisher database
- **Semantic Scholar**: AI-powered academic search
- **ClinicalTrials**: Clinical trials database
- **Europe PMC**: European life sciences database
- **DOAJ**: Directory of Open Access Journals
- **CORE**: Open access research aggregator

### Builtin Sources (Python-Based)
- **arXiv**: Preprint repository (uses arXiv Python library)
- **PubMed/PMC**: Biomedical databases (uses NIH E-utilities)
- **Google Scholar**: Broad academic search (uses web scraping)

## Example Configurations

### Research Lab Setup

```yaml
# Focus on open access with custom categories
default_category: "lab_research"

categories:
  lab_research:
    name: "lab_research"
    display_name: "Lab Research"
    type: "standard"
    sources: ["arxiv", "pubmed_central", "doaj"]
    max_results_per_source: 10

sources:
  lab_repo:
    name: "lab_repo"
    type: "http_api"
    enabled: true
    config:
      base_url: "https://lab.university.edu/api"
      # ... API configuration
```

### Student Configuration

```yaml
# Prioritize free sources
default_category: "free_papers"

categories:
  free_papers:
    name: "free_papers"
    display_name: "Free Papers"
    type: "standard"
    sources: ["arxiv", "pubmed_central", "doaj", "europe_pmc"]
```

### Corporate Research

```yaml
# Use premium APIs with authentication
sources:
  semantic_scholar:
    name: "semantic_scholar"
    type: "http_api"
    enabled: true
    config:
      api_key: "${SEMANTIC_SCHOLAR_API_KEY}"
      # ... rest of config

  core_ac_uk:
    name: "core_ac_uk"
    type: "http_api"
    enabled: true
    config:
      api_key: "${CORE_API_KEY}"
      # ... rest of config
```

## Validation and Testing

Test your configuration:

```python
from paperez_mcp.config import validate_current_configuration

status = validate_current_configuration()
print(f"Valid: {status['valid']}")
if not status['valid']:
    print(f"Warnings: {status['warnings']}")
```

## Migration from Python Config

The new YAML system is fully backward compatible. Your existing code will continue to work while you migrate to YAML configuration.

Old (Python):
```python
# Complex Python configuration code
```

New (YAML):
```yaml
# Simple, user-friendly YAML
sources:
  my_source:
    type: "http_api"
    config:
      base_url: "https://api.example.com"
      # Simple configuration
```

## Hot-Reloading

Configuration changes are automatically detected and reloaded (requires `watchdog` package):

```bash
pip install watchdog
```

Changes to any config file will automatically update the running system without restart.