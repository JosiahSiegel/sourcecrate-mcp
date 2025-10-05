# Custom Source Quick Start

## 5-Minute Setup: HTTP API Source

### 1. Add to Configuration

Create or edit `.sourcecrate/config/my_sources.yaml`:

```yaml
sources:
  my_api:
    name: my_api
    type: http_api
    enabled: true
    config:
      base_url: https://api.example.com
      search_path: /search
      query_param: q
      limit_param: limit
      field_mappings:
        title: title
        authors: authors
        abstract: abstract
        doi: doi
        url: url
        pdf_url: pdf_url
    capabilities:
      peer_reviewed: true
      stem_focus: true
```

### 2. Test

```bash
python3 -c "
import asyncio
from source_crate.config.manager import get_current_config
config = get_current_config()
print('✅ Loaded' if 'my_api' in config.sources else '❌ Failed')
"
```

### 3. Use

Your source is now available in all SourceCrate tools!

## Common Patterns

### Research Repository

```yaml
university_repo:
  name: university_repo
  type: http_api
  enabled: true
  config:
    base_url: https://repo.university.edu
    search_path: /api/search
    query_param: query
    field_mappings:
      title: metadata.title
      authors: metadata.creator
      abstract: metadata.description
      pdf_url: bitstreams.0.url
  capabilities:
    open_access_focus: true
    historical_depth: high
```

### Academic Database

```yaml
academic_db:
  name: academic_db
  type: http_api
  enabled: true
  config:
    base_url: https://academic-db.org
    search_path: /v1/papers
    query_param: search
    limit_param: count
    headers:
      Authorization: "Bearer YOUR_API_KEY"
    field_mappings:
      title: paper_title
      authors: author_list
      year: pub_year
  capabilities:
    peer_reviewed: true
    medical_focus: true
```

## Need Authentication?

See the [full guide](CUSTOM_SOURCE_GUIDE.md#plugin-sources) for plugin examples with custom authentication.

## Troubleshooting

- **Not working?** Check [troubleshooting guide](CUSTOM_SOURCE_GUIDE.md#troubleshooting)
- **Need help?** See [full documentation](CUSTOM_SOURCE_GUIDE.md)
- **Complex requirements?** Consider [plugin sources](CUSTOM_SOURCE_GUIDE.md#plugin-sources)