# Configuration Guide

## Quick Setup

Create `.paperez/config/config.yaml`:
```bash
mkdir -p .paperez/config/
```

```yaml
version: "1.0"
use_default_sources: true
default_category: comprehensive
max_concurrent_searches: 15
global_cache_enabled: true
```

## Key Settings

- `use_default_sources`: Include built-in sources (default: true)
- `default_category`: Search category - comprehensive, medical, preprints, etc.
- `max_concurrent_searches`: Parallel searches (default: 15)
- `global_cache_enabled`: Enable caching (default: true)

## Available Categories

- **comprehensive**: All sources (default)
- **medical**: PubMed, clinical trials
- **preprints**: arXiv, latest research
- **open_access**: Free full-text articles
- **business**: Economics, finance research

## Custom Sources

Add to config.yaml:
```yaml
sources:
  my_api:
    name: my_api
    type: http_api
    enabled: true
    config:
      base_url: https://api.example.com
      search_path: /search
      field_mappings:
        title: title
        authors: authors
```

## Get Help

Use the built-in tool: "Help me configure paperez-mcp"