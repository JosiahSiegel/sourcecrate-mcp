# Custom Source Integration Guide

This guide provides comprehensive instructions for adding custom academic sources to SourceCrate. The system is designed to support unlimited custom sources without code changes.

## Table of Contents

1. [Overview](#overview)
2. [Source Types](#source-types)
3. [Quick Start](#quick-start)
4. [Configuration Schema](#configuration-schema)
5. [Source Capabilities](#source-capabilities)
6. [Field Mappings](#field-mappings)
7. [Category Integration](#category-integration)
8. [Testing Custom Sources](#testing-custom-sources)
9. [Advanced Examples](#advanced-examples)
10. [Troubleshooting](#troubleshooting)

## Overview

SourceCrate supports three types of custom sources:

- **HTTP API Sources**: Connect to any REST API with configurable mappings
- **Plugin Sources**: Python plugins for complex custom logic
- **Built-in Sources**: Pre-integrated sources with optimized clients

All source types use the same configuration system and support dynamic capabilities for intelligent routing.

## Source Types

### HTTP API Sources

Best for APIs that return JSON responses with straightforward field mappings.

**Example Configuration:**

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
      description: "My custom academic database"
      coverage: "specialized research papers"
      base_url: https://api.example.com
      search_path: /v1/search
      query_param: q
      limit_param: limit
      response_format: json
      results_path: results
      field_mappings:
        title: title
        authors: author_list
        abstract: summary
        year: pub_year
        doi: doi
        url: html_url
        pdf_url: pdf_link
        citation_count: citations
        journal: journal_name
    capabilities:
      # Define source characteristics for intelligent routing
      medical_focus: false
      stem_focus: true
      peer_reviewed: true
      open_access_focus: false
      high_pdf_availability: true
      historical_depth: medium
```

### Plugin Sources

Best for sources requiring custom authentication, complex API logic, or data transformation.

**Creating a Plugin:**

```python
# my_custom_plugin.py
from source_crate.api_clients.base_client import BaseAPIClient
from typing import Any

class MyCustomClient(BaseAPIClient):
    """Custom client for specialized academic database."""

    def __init__(self):
        super().__init__("MyCustomSource", cache_expire=3600)

    async def _perform_search(
        self, query: str, limit: int, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Implement custom search logic."""
        # Custom authentication
        headers = {"Authorization": f"Bearer {self._get_api_key()}"}

        # Custom query transformation
        processed_query = self._transform_query(query)

        # Custom API call
        params = {
            "search": processed_query,
            "count": limit,
            "format": "json"
        }

        response = await self._make_request(
            "https://api.example.com/search",
            params=params,
            headers=headers
        )

        # Custom response processing
        return self._process_response(response)

    def _get_api_key(self) -> str:
        """Get API key from environment or configuration."""
        import os
        return os.getenv("MY_CUSTOM_API_KEY", "")

    def _transform_query(self, query: str) -> str:
        """Transform query for API-specific format."""
        # Example: convert spaces to operators
        return query.replace(" ", " AND ")

    def _process_response(self, response: dict) -> list[dict[str, Any]]:
        """Process API response into standard format."""
        papers = []
        for item in response.get("data", []):
            paper = {
                "title": item.get("title", ""),
                "authors": item.get("authors", []),
                "abstract": item.get("abstract", ""),
                "year": item.get("publication_year"),
                "doi": item.get("doi"),
                "url": item.get("url"),
                "pdf_url": item.get("pdf_url"),
                "citation_count": item.get("citation_count", 0),
                "journal": item.get("journal"),
                "source": self.source_name
            }
            papers.append(paper)
        return papers

# Register the plugin
def create_plugin():
    """Factory function to create plugin instance."""
    return MyCustomClient()
```

**Plugin Configuration:**

```yaml
sources:
  my_custom_plugin:
    name: my_custom_plugin
    type: plugin
    enabled: true
    module_path: plugins.my_custom_plugin
    class_name: MyCustomClient
    capabilities:
      stem_focus: true
      peer_reviewed: true
      high_pdf_availability: true
```

## Configuration Schema

### Required Fields

```yaml
sources:
  source_name:
    name: string           # Unique identifier
    type: string           # "http_api", "plugin", or "builtin"
    enabled: boolean       # Whether source is active
```

### Optional Fields

```yaml
    disabled_reason: string    # Reason if disabled (shown in warnings)
    timeout: number           # Request timeout in seconds (default: 30)
    max_retries: number       # Maximum retry attempts (default: 3)
    cache_expire: number      # Cache duration in seconds (default: 3600)
    rate_limit_delay: number  # Delay between requests (default: 0.5)
```

### HTTP API Configuration

```yaml
    config:
      description: string          # Human-readable description
      coverage: string            # What topics this source covers
      base_url: string            # API base URL
      search_path: string         # Search endpoint path
      query_param: string         # Query parameter name
      limit_param: string         # Limit parameter name
      response_format: string     # "json" or "xml"
      results_path: string        # Path to results array in response
      extra_params: object        # Additional static parameters
      field_mappings: object      # Map API fields to standard fields
      headers: object             # Static headers
```

### Plugin Configuration

```yaml
    module_path: string    # Python module path
    class_name: string     # Client class name
    config: object         # Plugin-specific configuration
```

## Source Capabilities

Capabilities enable intelligent query routing and source recommendation. Define characteristics that match your source:

### Domain Focus

```yaml
capabilities:
  medical_focus: boolean           # Medical/healthcare specialization
  stem_focus: boolean             # STEM fields focus
  humanities_focus: boolean       # Arts, literature, culture
  social_science_focus: boolean   # Psychology, sociology, etc.
  business_focus: boolean         # Economics, finance, management
  legal_focus: boolean            # Law, court decisions, legal scholarship
  historical_focus: boolean      # Historical documents, archives
```

### Content Types

```yaml
  peer_reviewed: boolean          # Peer-reviewed academic papers
  preprint_focus: boolean         # Preprints and early research
  open_access_focus: boolean      # Open access content
  subscription_content: boolean   # Paywalled content
  government_focus: boolean       # Government documents
```

### Technical Characteristics

```yaml
  high_pdf_availability: boolean  # >70% papers have PDFs
  recent_focus: boolean           # Emphasizes recent publications
  historical_depth: string       # "low", "medium", "high", "very_high"
  search_priority: number         # 1-10 priority score
```

### Query Preferences

```yaml
  prefers_simple_queries: boolean    # Works better with simple terms
  prefers_natural_language: boolean  # Supports natural language queries
  prefers_quoted_phrases: boolean    # Benefits from quoted phrases
```

## Field Mappings

Map API response fields to standard SourceCrate fields:

### Standard Fields

```yaml
field_mappings:
  # Required fields
  title: "api_field_name"           # Paper title
  authors: "authors_field"          # Author list (array or string)

  # Highly recommended fields
  abstract: "abstract_field"        # Paper abstract/summary
  year: "year_field"               # Publication year
  doi: "doi_field"                 # Digital Object Identifier
  url: "url_field"                 # Link to paper
  pdf_url: "pdf_field"             # Direct PDF link

  # Optional fields
  citation_count: "citations"       # Number of citations
  journal: "journal_field"         # Journal/venue name
  keywords: "keywords_field"       # Keywords/tags
  publication_date: "date_field"   # Full publication date
```

### Nested Field Mappings

For nested JSON responses, use dot notation:

```yaml
field_mappings:
  title: "metadata.title"
  authors: "metadata.authors.name"
  abstract: "content.abstract"
  doi: "identifiers.doi"
  pdf_url: "links.pdf.url"
```

### Complex Mappings

For advanced field extraction:

```yaml
field_mappings:
  # Array index access
  pdf_url: "download_links.0.url"

  # Conditional field selection
  authors: "author_list"  # Will try multiple strategies

  # Multiple field attempts (plugin sources only)
  abstract: "abstract || summary || description"
```

## Category Integration

Add your custom source to relevant categories for automatic routing:

### Adding to Existing Categories

```yaml
categories:
  medical:
    name: medical
    sources:
      - pubmed
      - pubmed_central
      - my_medical_source    # Add your source

  preprints:
    name: preprints
    sources:
      - arxiv
      - my_preprint_source   # Add your source
```

### Creating Custom Categories

```yaml
categories:
  my_specialty:
    name: my_specialty
    display_name: "My Research Specialty"
    description: "Specialized papers in my field"
    type: standard
    sources:
      - my_custom_source
      - other_relevant_source
    max_results_per_source: 10
    parallel_search: true
```

### Domain Keywords

Add domain keywords for automatic routing:

```yaml
routing:
  domain_keywords:
    my_domain:
      - "specialized term"
      - "domain keyword"
      - "field-specific phrase"

  domain_categories:
    my_domain: my_specialty
```

## Testing Custom Sources

### 1. Configuration Validation

```bash
# Test configuration loading
python3 scripts/validate_source_enablement.py

# Check for configuration warnings
python3 -c "
from source_crate.config.manager import get_current_config
config = get_current_config()
warnings = config.validate_configuration()
for warning in warnings:
    print(f'Warning: {warning}')
"
```

### 2. Source Functionality

```bash
# Test basic source functionality
python3 -c "
import asyncio
from source_crate.config.registry import SourceRegistry

async def test_source():
    registry = SourceRegistry()
    service = registry.get_configurable_service()
    results = await service.search('test query', limit=3, force_category=None)
    print(f'Found {len(results)} results')
    for result in results[:2]:
        print(f'- {result.get(\"title\", \"No title\")}')

asyncio.run(test_source())
"
```

### 3. MCP Tool Integration

```bash
# Test via MCP tools
python3 source_crate_server.py &
# Then test with Claude Code or MCP client
```

## Advanced Examples

### Example 1: Research Gate API

```yaml
sources:
  researchgate:
    name: researchgate
    type: http_api
    enabled: true
    config:
      description: "ResearchGate academic social network"
      base_url: https://api.researchgate.net
      search_path: /v1/publications
      query_param: query
      limit_param: limit
      field_mappings:
        title: title
        authors: authors.name
        abstract: abstract
        doi: doi
        url: url
        citation_count: stats.reads
    capabilities:
      peer_reviewed: true
      stem_focus: true
      social_science_focus: true
      historical_depth: high
```

### Example 2: Institutional Repository

```yaml
sources:
  university_repo:
    name: university_repo
    type: http_api
    enabled: true
    config:
      description: "University institutional repository"
      base_url: https://repository.university.edu
      search_path: /api/search
      query_param: q
      limit_param: size
      extra_params:
        format: json
        type: thesis
      headers:
        User-Agent: "SourceCrate/1.0"
      field_mappings:
        title: metadata.title
        authors: metadata.creator
        abstract: metadata.description
        year: metadata.date
        url: handle_url
        pdf_url: bitstreams.0.download_url
    capabilities:
      open_access_focus: true
      historical_depth: very_high
      high_pdf_availability: true
```

### Example 3: Specialized Database Plugin

```python
# specialized_db_plugin.py
from source_crate.api_clients.base_client import BaseAPIClient
import aiohttp
import json

class SpecializedDBClient(BaseAPIClient):
    """Client for specialized database with complex authentication."""

    def __init__(self):
        super().__init__("SpecializedDB", cache_expire=7200)
        self.session_token = None

    async def _get_session_token(self):
        """Authenticate and get session token."""
        if self.session_token:
            return self.session_token

        auth_url = "https://specialized-db.com/auth"
        auth_data = {
            "username": os.getenv("SPECIALIZED_DB_USER"),
            "password": os.getenv("SPECIALIZED_DB_PASS")
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, json=auth_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.session_token = result["access_token"]
                    return self.session_token

        raise Exception("Failed to authenticate with SpecializedDB")

    async def _perform_search(self, query: str, limit: int, **kwargs):
        """Perform authenticated search."""
        token = await self._get_session_token()

        search_url = "https://specialized-db.com/api/search"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "query": query,
            "max_results": limit,
            "format": "json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(search_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._transform_results(data["publications"])
                else:
                    return []

    def _transform_results(self, publications):
        """Transform API results to standard format."""
        results = []
        for pub in publications:
            result = {
                "title": pub.get("title", ""),
                "authors": [a["name"] for a in pub.get("authors", [])],
                "abstract": pub.get("abstract", ""),
                "year": pub.get("year"),
                "doi": pub.get("identifiers", {}).get("doi"),
                "url": pub.get("web_url"),
                "pdf_url": pub.get("pdf_url"),
                "citation_count": pub.get("metrics", {}).get("citations", 0),
                "journal": pub.get("journal", {}).get("name"),
                "source": self.source_name
            }
            results.append(result)
        return results
```

## Troubleshooting

### Common Issues

#### 1. Source Not Found

```
Error: Source 'my_source' not found in registry
```

**Solution:** Check that:
- Source is defined in configuration YAML
- Configuration file is loaded properly
- Source name matches exactly

#### 2. No Results Returned

```
Warning: Source 'my_source' returned 0 results
```

**Solutions:**
- Test API endpoint directly
- Check field mappings
- Verify authentication
- Check query parameter names

#### 3. Authentication Errors

```
Error: 401 Unauthorized
```

**Solutions:**
- Verify API credentials
- Check authentication method
- Ensure API key is valid
- Test with source's documentation

#### 4. Category Not Working

```
Warning: Category 'my_category' references unknown source 'my_source'
```

**Solutions:**
- Ensure source is enabled
- Check source name spelling
- Verify configuration loading

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("source_crate").setLevel(logging.DEBUG)
```

### Testing Queries

Test individual components:

```python
# Test configuration loading
from source_crate.config.manager import get_current_config
config = get_current_config()
print(f"Loaded {len(config.sources)} sources")

# Test source capabilities
source_config = config.sources['my_source']
print(f"Capabilities: {source_config.capabilities}")

# Test category routing
from source_crate.services.search_service import SearchService
service = SearchService()
analysis = service.analyze_query_domain("my test query")
print(f"Domain: {analysis['domain']}")
print(f"Recommended sources: {analysis['recommended_sources']}")
```

## Best Practices

1. **Start Simple**: Begin with HTTP API sources before moving to plugins
2. **Test Incrementally**: Test configuration, then functionality, then integration
3. **Use Capabilities**: Define accurate capabilities for better routing
4. **Handle Errors**: Implement proper error handling in plugins
5. **Cache Effectively**: Set appropriate cache expiration times
6. **Document Sources**: Add clear descriptions and coverage information
7. **Follow Standards**: Use standard field names when possible
8. **Rate Limit**: Respect source API rate limits
9. **Authenticate Securely**: Use environment variables for credentials
10. **Monitor Performance**: Track response times and success rates

## Contributing

To contribute new built-in sources or improve the custom source system:

1. Fork the repository
2. Add your source configuration
3. Test thoroughly
4. Submit a pull request
5. Include documentation updates

For questions or support, please see the main project documentation or create an issue on GitHub.