# Adding Academic Sources with Configuration Only

**The Simplest Way**: No Python coding required! Add new academic databases to PaperezMCP using just configuration files.

## ✅ What You Get

- **No coding**: Just configuration (YAML/JSON)
- **Working examples**: Europe PMC and DOAJ included
- **Immediate availability**: Sources work right after restart
- **Full integration**: All PaperezMCP features (caching, retry, deduplication)

## 🚀 Quick Start

### 1. Copy the config template
```bash
mkdir -p ~/.paperez/config && cp examples/simple_config_sources.yaml ~/.paperez/config/config.yaml
```

### 2. Restart PaperezMCP
The new sources are immediately available!

### 3. Test it
```python
from paperez_mcp.config import get_search_service
service = get_search_service()
# europe_pmc and doaj are now available automatically
```

## 📋 Working Examples

### Europe PMC (39M+ papers, no API key)
```yaml
sources:
  europe_pmc:
    name: europe_pmc
    type: http_api
    enabled: true
    config:
      base_url: 'https://www.ebi.ac.uk/europepmc/webservices/rest'
      search_path: '/search'
      query_param: 'query'
      limit_param: 'pageSize'
      field_mappings:
        title: 'title'
        authors: 'authorString'
        abstract: 'abstractText'
        journal: 'journalTitle'
        year: 'pubYear'
        doi: 'doi'
```

### DOAJ (2.1M+ open access articles, no API key)
```yaml
sources:
  doaj:
    name: doaj
    type: http_api
    enabled: true
    config:
      base_url: 'https://doaj.org/api/search'
      search_path: '/articles/_search'
      query_param: 'q'
      limit_param: 'pageSize'
      results_path: 'results'
      field_mappings:
        title: 'bibjson.title'
        authors: 'bibjson.author'
        journal: 'bibjson.journal.title'
```

## 🔧 How to Add Any API

### Required Configuration
```yaml
your_source:
  name: your_source
  type: http_api
  enabled: true
  config:
    base_url: 'https://api.yoursite.com'
    search_path: '/search'
    query_param: 'q'
    limit_param: 'limit'
    response_format: 'json'
    results_path: 'results'  # JSONPath to results array
    field_mappings:
      title: 'title'
      authors: 'authors'
      abstract: 'abstract'
      year: 'year'
      doi: 'doi'
      url: 'url'
```

### Optional Configuration
```yaml
config:
  # Authentication
  api_key: 'your-api-key'
  auth_header: 'Authorization'  # or 'X-API-Key'
  auth_type: 'Bearer'  # or 'ApiKey', 'Basic'

  # Request tuning
  timeout: 30
  rate_limit_delay: 0.5
  extra_params:
    format: 'json'
    fields: 'title,authors,abstract'

  # Response parsing
  total_path: 'total'  # JSONPath to total count
  headers:
    User-Agent: 'MyApp 1.0'
```

## 🎯 Field Mappings

Map API response fields to standard format:

```yaml
field_mappings:
  title: 'title'                    # Paper title
  authors: 'authors'                # List of author names
  abstract: 'description'           # Paper abstract
  journal: 'venue.name'             # Journal name
  year: 'published_year'            # Publication year
  doi: 'identifiers.doi'           # DOI identifier
  url: 'links.html'                 # Paper URL
  pdf_url: 'links.pdf'              # Direct PDF URL
  citation_count: 'metrics.cited'   # Citation count
```

Supports nested fields with dot notation: `'metadata.authors.0.name'`

## ⚙️ Response Parsing

The `results_path` uses JSONPath to find the results array:

```yaml
# For API response: {"data": {"results": [...]}}
results_path: 'data.results'

# For API response: {"hits": {"hits": [...]}}
results_path: 'hits.hits'

# For API response: {"results": [...]}
results_path: 'results'
```

## 🏷️ Adding to Categories

Include your source in existing categories:

```yaml
categories:
  comprehensive:
    sources: ['crossref', 'arxiv', 'your_source']

  my_category:
    name: my_category
    display_name: 'My Custom Category'
    type: standard
    sources: ['your_source', 'another_source']
    max_results_per_source: 8
```

## 🚨 Common Issues

### Authentication
```yaml
# API Key in header
api_key: 'abc123'
auth_header: 'X-API-Key'
auth_type: 'ApiKey'

# Bearer token
api_key: 'xyz789'
auth_header: 'Authorization'
auth_type: 'Bearer'

# Basic auth (username:password base64 encoded)
api_key: 'user:pass'
auth_type: 'Basic'
```

### Rate Limiting
```yaml
rate_limit_delay: 1.0  # Wait 1 second between requests
```

### Field Parsing
```yaml
# Authors as string: "Smith, J; Jones, A"
authors: 'author_string'

# Authors as array: [{"name": "Smith"}, {"name": "Jones"}]
authors: 'authors'

# Year from date: "2023-05-15"
year: 'publication_date'  # Automatically extracts year
```

## 💡 Tips

1. **Test incrementally**: Start with basic config, then add features
2. **Check API docs**: Look for pagination, rate limits, required headers
3. **Use browser dev tools**: Inspect actual API calls from the website
4. **JSONPath testing**: Use https://jsonpath.com to test your paths

## 🌟 Examples in the Wild

See `examples/simple_config_sources.yaml` for:
- Europe PMC (life sciences, 39M+ papers)
- DOAJ (open access journals, 2.1M+ articles)
- CORE (with API key)
- Template for institutional repositories

## ⚡ Comparison

| Method | Complexity | Time to Add | Flexibility |
|--------|------------|-------------|-------------|
| **Config-only** | ⭐ | 5 minutes | ⭐⭐⭐ |
| Python Plugin | ⭐⭐⭐ | 30+ minutes | ⭐⭐⭐⭐⭐ |
| Core Integration | ⭐⭐⭐⭐⭐ | Hours | ⭐⭐⭐⭐⭐ |

For 90% of REST APIs, config-only is perfect! 🎯