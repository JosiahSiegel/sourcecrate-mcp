# Custom Source Development Guide

This guide explains how to integrate custom academic sources into PaperezMCP without modifying the core codebase. The system now uses a **capability-based architecture** that allows full extensibility through configuration.

## 🎯 Overview

PaperezMCP supports three types of sources:
- **Built-in sources**: Core sources like PubMed, arXiv (Python functions)
- **HTTP API sources**: RESTful APIs defined via YAML configuration
- **Plugin sources**: Custom Python modules for complex integrations

All sources are configured with **capabilities** that describe their characteristics, eliminating hardcoded assumptions.

## 📋 Prerequisites

- PaperezMCP installed and configured
- Understanding of YAML configuration
- For plugins: Python development experience

## 🔧 Source Capabilities System

### Core Concept

Instead of hardcoding source-specific logic (like `if source == "arxiv"`), PaperezMCP uses capabilities to determine behavior:

```python
# OLD (hardcoded)
if source == "arxiv":
    return f'ti:"{query}" OR abs:"{query}"'

# NEW (capability-based)
if capabilities.field_search and capabilities.stem_focus:
    return f'ti:"{query}" OR abs:"{query}"'
```

### Available Capabilities

```yaml
capabilities:
  # Content domains
  medical_focus: boolean          # Specializes in medical/health content
  stem_focus: boolean             # Specializes in STEM fields
  humanities_focus: boolean       # Specializes in humanities
  social_science_focus: boolean   # Specializes in social sciences
  preprint_server: boolean        # Primarily contains preprints

  # Technical capabilities
  field_search: boolean           # Supports field-specific search (title:, abstract:)
  phrase_search: boolean          # Supports quoted phrase searching
  boolean_search: boolean         # Supports AND/OR/NOT operators
  wildcard_search: boolean        # Supports wildcard patterns

  # Content availability
  high_pdf_availability: boolean  # Most papers have accessible PDFs
  open_access_only: boolean       # Only open access content
  subscription_content: boolean   # May include subscription-only content

  # Query optimization preferences
  prefers_simple_queries: boolean     # Works better with simple keywords
  prefers_natural_language: boolean   # Works better with natural language
  prefers_quoted_phrases: boolean     # Works better with quoted phrases

  # Content characteristics
  historical_depth: "low" | "medium" | "high" | "very_high"
  update_frequency: "daily" | "weekly" | "monthly"
  average_response_time: float    # Seconds

  # PDF-specific capabilities
  pdf_url_patterns: [string]      # Regex patterns for extracting PDF URLs
  pdf_validation_required: boolean

  # Priority and routing
  search_priority: int            # 1-10, higher = more important
  topic_routing_weight: float     # Weight for topic-based routing
```

## 🌐 HTTP API Sources

Most academic databases provide REST APIs that can be integrated via YAML configuration.

### Basic HTTP API Source

Create a YAML file in `.paperez/config/` (e.g., `my_custom_sources.yaml`):

```yaml
sources:
  my_research_db:
    name: my_research_db
    type: http_api
    enabled: true
    timeout: 30
    max_retries: 3
    cache_expire: 3600

    config:
      description: "My Custom Research Database"
      base_url: "https://api.myresearchdb.org"
      search_path: "/papers/search"
      query_param: "q"
      limit_param: "limit"
      response_format: "json"
      results_path: "data.papers"

      # Optional authentication
      auth_type: "ApiKey"  # or "Bearer" or "Basic"
      auth_header: "X-API-Key"
      api_key: "your-api-key-here"

      # Field mappings (maps API response to standard fields)
      field_mappings:
        title: "paper_title"
        authors: "author_list"
        abstract: "summary"
        journal: "publication"
        year: "pub_year"
        doi: "doi"
        url: "paper_url"
        pdf_url: "pdf_link"
        citation_count: "citations"

      # Rate limiting
      rate_limit_delay: 0.5  # Seconds between requests

    capabilities:
      # Define your source's characteristics
      medical_focus: false
      stem_focus: true
      humanities_focus: false
      social_science_focus: false
      preprint_server: false

      field_search: true
      phrase_search: true
      boolean_search: false
      high_pdf_availability: true

      prefers_quoted_phrases: true
      historical_depth: "medium"
      update_frequency: "weekly"
      search_priority: 7

      pdf_url_patterns:
        - "https://myresearchdb\\.org/pdf/(\\d+)\\.pdf"
```

### Advanced API Configuration

```yaml
sources:
  advanced_api:
    name: advanced_api
    type: http_api
    enabled: true

    config:
      # Complex response processing
      results_path: "response.results.papers"

      # Custom request parameters
      extra_params:
        format: "json"
        include_abstracts: "true"
        sort: "relevance"

      # Request headers
      request_headers:
        User-Agent: "PaperezMCP/1.0"
        Accept: "application/json"

      # Pagination support
      pagination:
        type: "offset"  # or "page" or "cursor"
        offset_param: "start"
        page_size_param: "count"

      # Error handling
      error_status_codes: [429, 503]  # Retry on these codes
      exponential_backoff: true
      backoff_max_delay: 60

    capabilities:
      # Capabilities determine system behavior
      medical_focus: true
      field_search: true
      high_pdf_availability: false
      prefers_natural_language: true
      search_priority: 8
      topic_routing_weight: 1.5
```

## 🔌 Plugin Sources (Advanced)

For complex integrations requiring custom logic, create Python plugins.

### 1. Create Plugin Module

Create `paperez_mcp/plugins/my_custom_source.py`:

```python
"""
Custom source plugin for My Research Database
"""

import asyncio
import logging
from typing import Any, Dict, List

import aiohttp

logger = logging.getLogger(__name__)


class MyCustomSourceClient:
    """Custom client for My Research Database"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url", "")
        self.api_key = config.get("api_key", "")

    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search the custom database

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of paper dictionaries with standard fields
        """
        try:
            # Custom search logic here
            url = f"{self.base_url}/search"
            params = {
                "q": query,
                "limit": limit,
                "format": "json"
            }

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_results(data)
                    else:
                        logger.error(f"API error: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _process_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process API response into standard format"""
        papers = []

        for item in data.get("results", []):
            paper = {
                "title": item.get("title", ""),
                "authors": self._extract_authors(item.get("authors", [])),
                "abstract": item.get("abstract", ""),
                "journal": item.get("journal", ""),
                "year": self._extract_year(item.get("published_date")),
                "doi": item.get("doi"),
                "url": item.get("url"),
                "pdf_url": item.get("pdf_url"),
                "citation_count": item.get("citation_count", 0),
                "source": "my_custom_source"
            }
            papers.append(paper)

        return papers

    def _extract_authors(self, authors_data: List[Any]) -> List[str]:
        """Extract author names from API response"""
        if not authors_data:
            return []

        # Handle different author formats
        if isinstance(authors_data[0], str):
            return authors_data
        elif isinstance(authors_data[0], dict):
            return [f"{a.get('first', '')} {a.get('last', '')}" for a in authors_data]
        else:
            return [str(a) for a in authors_data]

    def _extract_year(self, date_str: str) -> int:
        """Extract year from date string"""
        if not date_str:
            return 0
        try:
            return int(date_str[:4])
        except (ValueError, TypeError):
            return 0


# Entry point function for the registry
async def search_my_custom_source(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Entry point function called by PaperezMCP

    Args:
        query: Search query
        limit: Maximum results to return

    Returns:
        List of paper dictionaries
    """
    # Configuration is loaded from YAML
    from paperez_mcp.config import get_current_config

    config = get_current_config()
    source_config = config.sources.get("my_custom_source", {})

    client = MyCustomSourceClient(source_config.config)
    return await client.search(query, limit)
```

### 2. Configure Plugin Source

Add to your YAML configuration:

```yaml
sources:
  my_custom_source:
    name: my_custom_source
    type: plugin
    enabled: true

    # Plugin configuration
    module_path: "paperez_mcp.plugins.my_custom_source"
    class_name: "MyCustomSourceClient"  # Optional: for class-based plugins
    function_name: "search_my_custom_source"  # For function-based plugins

    config:
      base_url: "https://api.myresearchdb.org"
      api_key: "your-api-key"
      description: "My Custom Research Database"

    capabilities:
      medical_focus: false
      stem_focus: true
      field_search: true
      high_pdf_availability: true
      prefers_quoted_phrases: true
      search_priority: 8
      pdf_url_patterns:
        - "https://myresearchdb\\.org/files/(\\d+)\\.pdf"
```

## 📂 Categories and Meta-Categories

Organize sources into searchable categories:

```yaml
categories:
  my_domain:
    name: my_domain
    display_name: "My Research Domain"
    description: "Papers from my specialized field"
    type: standard
    sources:
      - my_research_db
      - pubmed  # Mix with existing sources
      - crossref
    max_results_per_source: 5
    parallel_search: true

  comprehensive_with_custom:
    name: comprehensive_with_custom
    display_name: "Comprehensive + Custom"
    type: meta
    includes:
      - scientific      # Built-in category
      - my_domain       # Your custom category
    merge_strategy: "weighted_union"
    weights:
      scientific: 0.7
      my_domain: 0.3
```

## 🧪 Testing Your Custom Source

### 1. Configuration Validation

```bash
# Test configuration loading
python3 -c "
from paperez_mcp.config import get_current_config
config = get_current_config()
print('Available sources:', list(config.sources.keys()))
print('My source enabled:', config.sources.get('my_custom_source', {}).enabled)
"
```

### 2. Integration Testing

```bash
# Run the custom source validation
python3 scripts/validate_custom_source_integration.py
```

### 3. Manual Testing

```python
import asyncio
from paperez_mcp import server

async def test_custom_source():
    # Test browsing with your custom source
    result = await server.browse_papers.fn("machine learning", limit=3)
    papers = result[0].get('results', [])

    for paper in papers:
        if paper.get('source') == 'my_custom_source':
            print(f"✅ Found paper from custom source: {paper.get('title')}")

asyncio.run(test_custom_source())
```

## 🔍 Capability-Based System Benefits

### Automatic Behavior

Your custom source automatically gets:

1. **Query Optimization**: Based on `field_search`, `prefers_quoted_phrases`, etc.
2. **Topic Filtering**: Based on `medical_focus`, `stem_focus`, etc.
3. **PDF Prioritization**: Based on `high_pdf_availability`
4. **Smart Routing**: Based on `search_priority`, `topic_routing_weight`
5. **Error Handling**: Consistent across all sources

### Example: Auto-Generated Behavior

```yaml
# Your configuration
capabilities:
  stem_focus: true
  field_search: true
  prefers_quoted_phrases: true
  high_pdf_availability: true
  search_priority: 8

# Automatic behaviors generated:
# 1. Query "machine learning" becomes 'ti:"machine learning" OR abs:"machine learning"'
# 2. Non-STEM queries get filtered out
# 3. Papers from this source get high download priority
# 4. Source gets priority 8 in search ordering
```

## 🚀 Advanced Features

### Custom PDF Pattern Extraction

```yaml
capabilities:
  pdf_url_patterns:
    - "https://mydb\\.org/pdf/(\\d+)\\.pdf"
    - "https://mydb\\.org/papers/([a-z0-9]+)/download"
    # System automatically uses these for PDF discovery
```

### Rate Limiting and Performance

```yaml
config:
  rate_limit_delay: 1.0        # Seconds between requests
  exponential_backoff: true    # Automatic retry with backoff
  backoff_max_delay: 60       # Maximum delay
  concurrent_requests: 3       # Max parallel requests
```

### Authentication

```yaml
config:
  auth_type: "Bearer"          # Bearer token
  auth_header: "Authorization"
  api_key: "${MY_API_KEY}"     # Environment variable

  # Or use OAuth2
  auth_type: "OAuth2"
  client_id: "your-client-id"
  client_secret: "${OAUTH_SECRET}"
  token_url: "https://api.example.com/oauth/token"
```

## 🐛 Troubleshooting

### Common Issues

1. **Source not appearing**: Check `enabled: true` and YAML syntax
2. **No results**: Verify API endpoint and field mappings
3. **Rate limiting**: Increase `rate_limit_delay`
4. **Capability issues**: Validate capabilities match your source's behavior

### Debug Mode

```yaml
# Add to your source config
config:
  debug: true  # Enables detailed logging
```

### Validation

```bash
# Validate your configuration
python3 -c "
from paperez_mcp.config.schemas import SourceProviderConfig
import yaml

with open('.paperez/config/my_sources.yaml') as f:
    data = yaml.safe_load(f)

for name, config in data.get('sources', {}).items():
    try:
        source = SourceProviderConfig(**config)
        print(f'✅ {name}: Valid configuration')
    except Exception as e:
        print(f'❌ {name}: {e}')
"
```

## 📚 Examples

See the `.paperez/config/` directory for examples of:
- `medical.yaml` - Built-in and HTTP API sources
- `scientific.yaml` - Sources with different capabilities
- `business.yaml` - Domain-specific source configurations

## 🤝 Contributing

Found issues or want to contribute improvements to the custom source system? Please:

1. Test with the validation script: `python3 scripts/validate_custom_source_integration.py`
2. Ensure no hardcoded assumptions remain
3. Update capability definitions if needed
4. Contribute examples of successful integrations

---

**The capability-based architecture ensures your custom sources integrate seamlessly without any code changes to PaperezMCP core!** 🎉