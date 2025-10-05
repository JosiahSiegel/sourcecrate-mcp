# API Clients - YAML-Driven Architecture

## Design Philosophy

**This directory contains ONLY generic, configuration-driven clients. NO provider-specific code should exist here.**

All source behavior is determined entirely by YAML configuration files in `sourcecrate_mcp/default_configs/`.

## Architecture

### What belongs here:
- `base_client.py` - Abstract base class for all clients
- `generic_http_client.py` - Generic HTTP client driven by YAML configuration
- `__init__.py` - Module initialization

### What does NOT belong here:
- ❌ Provider-specific clients (e.g., `arxiv_client.py`, `pubmed_client.py`)
- ❌ Hardcoded API logic for specific sources
- ❌ Provider-specific URL transformations or rate limiting

## How it works

1. **Sources are defined in YAML** (`default_configs/*.yaml`):
   ```yaml
   sources:
     arxiv:
       type: builtin  # or http_api
       config:
         # All API configuration here
         pdf_url_transform:
           "arxiv.org/pdf/": "export.arxiv.org/pdf/"
         rate_limit_seconds: 3
   ```

2. **Generic client reads configuration**:
   - For `type: http_api` → Uses `GenericHTTPClient`
   - For `type: builtin` → Uses built-in search functions from `sourcecrate_mcp/search_functions/`

3. **All behavior is configurable**:
   - URL patterns and transformations
   - Rate limiting
   - Authentication
   - Field mappings
   - Response parsing

## Adding New Sources

To add a new academic source:

1. **DO NOT** create a new Python client file
2. **DO** add configuration to `default_configs/*.yaml`:
   ```yaml
   sources:
     new_source:
       type: http_api
       enabled: true
       config:
         base_url: https://api.example.com
         search_path: /search
         # ... other configuration
   ```

3. The `GenericHTTPClient` will automatically handle it

## User Customization

Users can override ANY source configuration by creating `.sourcecrate/config/config.yaml`:

```yaml
sources:
  arxiv:
    config:
      # Override any settings
      rate_limit_seconds: 5
      pdf_url_transform:
        "arxiv.org/": "my-mirror.org/"
```

## Why This Architecture?

1. **No hardcoding**: Everything is configuration-driven
2. **User control**: Users can modify behavior without touching code
3. **Maintainability**: One generic client to maintain instead of many
4. **Extensibility**: New sources added via YAML only
5. **Single source of truth**: YAML files define all behavior

## Migration Note

If you see provider-specific files like `arxiv_client.py` or `pubmed_client.py`, they should be removed. All their functionality should be expressed through YAML configuration instead.