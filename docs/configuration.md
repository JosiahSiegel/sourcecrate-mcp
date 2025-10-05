# Configuration Guide

## Overview

SourceCrate uses a **flexible multi-file configuration system** where you can create any number of YAML files in the `.sourcecrate/config/` directory. All files are automatically loaded and merged.

## Quick Setup

### Basic Configuration
```bash
mkdir -p .sourcecrate/config/
```

Create any YAML file (name doesn't matter):
```yaml
# .sourcecrate/config/my_config.yaml
version: "1.0"
use_default_sources: true
default_category: null  # Uses intelligent BM25 routing
max_concurrent_searches: 15
global_cache_enabled: true
```

### Domain-Specific Organization
```bash
# Organize by research domain
.sourcecrate/config/medical_sources.yaml      # Medical databases
.sourcecrate/config/engineering_apis.yaml     # Engineering sources
.sourcecrate/config/institution_db.yaml       # University databases
```

## Available Categories

### Built-in Categories
- **medical**: PubMed, PMC, ClinicalTrials, Europe PMC (4 sources)
- **academic_premium**: CrossRef, Semantic Scholar, DOAJ (3 sources)
- **preprints**: arXiv, Semantic Scholar (2 sources)
- **open_access**: arXiv, Semantic Scholar, DOAJ (3 sources)
- **business**: CrossRef, Semantic Scholar (2 sources)
- **social_sciences**: CORE Repository, Semantic Scholar (2 sources)
- **humanities**: Open Library, CORE Repository (2 sources)
- **legal_research**: CourtListener, CrossRef (2 sources)
- **government_policy**: Federal Register, CrossRef (2 sources)
- **historical**: Internet Archive, CrossRef (2 sources)

### Default Behavior
- `default_category: null` uses **intelligent BM25 routing** across all sources
- Queries are automatically routed to relevant categories based on keywords
- No category specified = comprehensive search across all enabled sources

## Custom Sources Configuration

### HTTP API Source Template
```yaml
sources:
  my_institution_api:
    name: my_institution_api
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600
    config:
      description: My University Research Database
      coverage: university research, theses, local studies
      base_url: https://api.myuni.edu
      search_path: /api/search
      query_param: q
      limit_param: limit
      response_format: json
      results_path: results
      extra_params:
        api_key: "your_api_key"
        format: json
      field_mappings:
        title: title
        authors: authors
        abstract: abstract
        journal: source
        year: publication_year
        doi: doi
        url: url
        pdf_url: pdf_link
        citation_count: citation_count
      rate_limit_delay: 0.5  # Seconds between requests
```

### Custom Categories
```yaml
categories:
  my_specialty:
    name: my_specialty
    display_name: My Research Specialty
    description: Custom category for specialized research
    type: standard
    sources:
      - my_institution_api
      - crossref         # Reference built-in sources
      - semantic_scholar # Mix custom + built-in
    max_results_per_source: 10
    parallel_search: true
```

## Configuration Validation

### Automatic Validation
- All configuration files are validated on startup
- Invalid configurations will show detailed error messages
- Use the test script to verify: `python tests/test_all_categories_dynamic.py`

### Required Fields
- **sources.name**: Unique identifier
- **sources.type**: Must be 'http_api' for custom sources
- **sources.config.base_url**: API endpoint
- **field_mappings**: At minimum title, authors, year

### Optional but Recommended
- **description**: Human-readable source description
- **rate_limit_delay**: Respect API rate limits
- **timeout**: Prevent hanging requests
- **cache_expire**: Cache duration in seconds

## Legal Compliance and Liability

### Legal Disclaimer for Custom Sources
**SourceCrate provides legal compliance only for default configuration sources. Users who add custom sources assume full legal responsibility for compliance with all applicable Terms of Service, copyright laws, and institutional policies.**

### User Legal Obligations for Custom Sources
1. **Full liability assumed** - Users are solely responsible for custom source compliance
2. **Independent verification required** - Users must verify Terms of Service compliance
3. **Legal compliance mandatory** - Respect rate limits, use legitimate APIs only
4. **Institutional policy compliance** - Ensure compliance with organizational policies
5. **No web scraping** - Use only official APIs with proper authorization
6. **SourceCrate disclaims liability** - No responsibility for user-configured sources

### Best Practices
```yaml
# Good: Respects ToS, includes delays, proper attribution
my_database:
  config:
    description: "University XYZ Research Repository (used with permission)"
    rate_limit_delay: 1.0  # Conservative rate limiting

# Avoid: No rate limiting, unclear source
fast_api:
  config:
    rate_limit_delay: 0.0  # Too aggressive
```

## Environment Variables

### Enhanced Performance
```bash
# API keys for better rate limits
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CROSSREF_EMAIL="your_email@university.edu"

# Custom source authentication
export MY_API_KEY="university_database_key"
```

### Using in Configuration
```yaml
sources:
  my_source:
    config:
      extra_params:
        api_key: "${MY_API_KEY}"  # Environment variable substitution
```

## Troubleshooting

### Common Issues
1. **"Category references disabled source"** - Check source `enabled: true`
2. **"No results found"** - Verify API endpoints and field mappings
3. **"Rate limit exceeded"** - Increase `rate_limit_delay`
4. **"Invalid configuration"** - Check YAML syntax and required fields

### Testing Configuration
```bash
# Test all categories and sources
python tests/test_all_categories_dynamic.py

# Check specific source
python -c "from source_crate.config.manager import ConfigManager; print(ConfigManager().get_config().sources)"
```

## Get Help

Use the built-in tool for comprehensive help:
```
"Help me configure source-crate"
```

This provides complete schemas, examples, and troubleshooting guidance.