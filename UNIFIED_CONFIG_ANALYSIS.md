# Should Default Sources Use Config System? **YES!**

## 🔍 Current State (Inconsistent)

### Built-in Sources (Hardcoded Python)
- `crossref_client.py` - 150+ lines of code
- `semantic_scholar_client.py` - 120+ lines of code
- `arxiv_client.py` - 180+ lines of code
- `pubmed_client.py` - 200+ lines of code
- Each implements same patterns: HTTP requests, JSON parsing, field mapping

### New Sources (Config-based)
- Just YAML configuration
- Works immediately
- No code needed

## ✅ Benefits of Unified Config System

### 1. **Consistency**
```yaml
# ALL sources work the same way
crossref: {type: http_api, config: {...}}
europe_pmc: {type: http_api, config: {...}}
my_custom: {type: http_api, config: {...}}
```

### 2. **Massive Code Reduction**
| Current | Unified Config |
|---------|---------------|
| 150+ lines Python per source | 20 lines YAML per source |
| 8 API client files | 0 API client files |
| Custom retry/cache per client | Built-in unified handling |

### 3. **User Customization**
```yaml
# Users can customize built-in sources!
crossref:
  config:
    extra_params:
      mailto: my-email@university.edu  # Custom email
    rate_limit_delay: 0.5  # Slower for politeness
```

### 4. **Easier Maintenance**
- Bug fix in `GenericHTTPClient` → fixes ALL sources
- No more duplicate API client code
- Consistent error handling everywhere

### 5. **Trivial Source Addition**
```yaml
# Add any REST API in minutes
new_source:
  type: http_api
  config:
    base_url: https://api.example.com
    # ... just configuration
```

## 📊 Code Comparison

### Current CrossRef Client (150+ lines)
```python
class CrossRefClient(BaseAPIClient):
    def __init__(self):
        super().__init__("CrossRef", cache_expire=3600)

    async def _perform_search(self, query: str, limit: int, **kwargs):
        url = "https://api.crossref.org/works"
        params = {
            "query": formatted_query,
            "rows": limit,
            "sort": "relevance",
            # ... 50+ more lines of request logic
        }
        # ... 100+ more lines of response parsing
```

### Config-Based CrossRef (20 lines)
```yaml
crossref:
  type: http_api
  config:
    base_url: https://api.crossref.org
    search_path: /works
    query_param: query
    limit_param: rows
    results_path: message.items
    field_mappings:
      title: title.0
      authors: author
      doi: DOI
    # Done!
```

## 🚨 What This Means

### Current Codebase
- 8 API client files (~1200 lines)
- Duplicate error handling
- Inconsistent retry logic
- Hard to customize
- Complex to add sources

### Unified Config System
- 0 API client files
- Unified error handling in `GenericHTTPClient`
- Consistent everything
- Users can customize any source
- Trivial to add sources

## 🎯 Migration Strategy

### Phase 1: Convert Simple Sources
```yaml
# These are just REST APIs - easy conversion
crossref: {type: http_api, config: {...}}
semantic_scholar: {type: http_api, config: {...}}
europe_pmc: {type: http_api, config: {...}}
```

### Phase 2: Handle Complex Sources
```yaml
# PubMed (2-step API) - might need custom logic
pubmed: {type: builtin, function_name: search_pubmed}

# Google Scholar (scraping) - definitely needs custom logic
google_scholar: {type: builtin, function_name: search_google_scholar}
```

### Phase 3: Full Unification
- Extend `GenericHTTPClient` for multi-step APIs
- Support XML parsing (arXiv)
- Support authentication variants

## 🏆 The Vision

```yaml
# Single, consistent config for EVERYTHING
sources:
  crossref: {type: http_api, config: {...}}
  semantic_scholar: {type: http_api, config: {...}}
  arxiv: {type: http_api, config: {...}}
  pubmed: {type: http_api, config: {...}}
  europe_pmc: {type: http_api, config: {...}}
  doaj: {type: http_api, config: {...}}
  my_university: {type: http_api, config: {...}}
  any_api: {type: http_api, config: {...}}
```

**Result**:
- ✅ 90% less code
- ✅ 100% consistent
- ✅ User customizable
- ✅ Trivial to extend

## 🤔 Should We Do This?

**ABSOLUTELY!** This would make PaperezMCP:
- Much simpler to maintain
- Much easier for users to customize
- Much more consistent
- Much easier to extend

The only question is: migration strategy and timeline.