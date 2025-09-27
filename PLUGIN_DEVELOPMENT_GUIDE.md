# PaperezMCP Plugin Development Guide

This comprehensive guide covers everything you need to know about developing, testing, and distributing plugins for PaperezMCP. Plugins allow you to add entirely new academic sources that have never been used before.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Plugin Architecture](#plugin-architecture)
4. [Development Workflow](#development-workflow)
5. [API Reference](#api-reference)
6. [Security Guidelines](#security-guidelines)
7. [Distribution](#distribution)
8. [Examples](#examples)
9. [Troubleshooting](#troubleshooting)

## Overview

PaperezMCP plugins extend the system's capability to search academic databases. Each plugin:

- Implements a standardized API for searching academic papers
- Handles authentication and rate limiting for external services
- Transforms results into a common format
- Integrates seamlessly with existing search categories

### Supported Source Types

- **API-based sources**: Academic databases with REST APIs (IEEE Xplore, Springer, etc.)
- **Web scrapers**: Public websites with academic content (ResearchGate, institutional pages)
- **File-based sources**: Local databases, CSV files, institutional repositories
- **OAI-PMH repositories**: Open Archives Initiative compatible repositories

## Quick Start

### 1. Install Plugin Development Tools

```bash
# Install PaperezMCP with plugin development tools
pip install paperez-mcp[dev]

# Verify installation
paperez-plugin --help
```

### 2. Create Your First Plugin

```bash
# Create a new plugin
paperez-plugin create my_source_plugin \
  --description "Integration with My Academic Database" \
  --author "Your Name" \
  --source-type api

# This creates a complete plugin template
cd my_source_plugin/
```

### 3. Implement Your API Integration

Edit `client.py` to implement your specific API:

```python
async def _perform_search(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
    """
    Implement your API-specific search logic here.
    Return list of standardized paper dictionaries.
    """
    # Your implementation here
    pass
```

### 4. Test Your Plugin

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Validate plugin structure
paperez-plugin validate .

# Security scan
paperez-plugin security-scan .
```

### 5. Install and Use

```bash
# Install the plugin
paperez-plugin install .

# Add to your configuration
paperez-plugin configure my_source_plugin

# Test with PaperezMCP
python -c "from paperez_mcp import search_papers; print(search_papers('test query'))"
```

## Plugin Architecture

### Directory Structure

```
my_plugin/
├── plugin.yaml           # Plugin manifest
├── client.py            # Main client implementation
├── __init__.py          # Python package init
├── requirements.txt     # Dependencies
├── README.md           # Documentation
├── example_config.yaml # Configuration example
├── tests/              # Test suite
│   ├── __init__.py
│   └── test_client.py
└── docs/               # Additional documentation
```

### Plugin Manifest (plugin.yaml)

```yaml
name: my_source_plugin
version: "1.0.0"
description: "Integration with My Academic Database"
author: "Your Name"
homepage: "https://github.com/yourname/my-plugin"

# Plugin metadata
paperez_version: ">=1.0.0"
python_version: ">=3.8"

# Plugin configuration
plugin:
  class_name: "MySourceClient"
  module_path: "my_source_plugin.client"

# Search capabilities
capabilities:
  - search
  - full_text_access
  - citation_data

# Configuration schema
config_schema:
  api_key:
    type: string
    required: true
    description: "API key for My Academic Database"

  base_url:
    type: string
    required: false
    description: "Custom base URL"
    default: "https://api.myacademicsource.com"
```

### Base Client Class

All plugins must extend `BaseAPIClient`:

```python
from paperez_mcp.api_clients.base_client import BaseAPIClient

class MySourceClient(BaseAPIClient):
    def __init__(self, api_key: str, **kwargs):
        super().__init__("My Source", cache_expire=3600)
        self.api_key = api_key
        # Your initialization here

    async def _perform_search(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
        # Your search implementation
        results = []
        # ... API calls and processing
        return [self._standardize_paper(paper) for paper in results]
```

## Development Workflow

### 1. Planning Phase

**Research Your Target Source:**
- API documentation and authentication requirements
- Rate limits and usage policies
- Available metadata fields
- Search capabilities and limitations

**Design Considerations:**
- How to handle authentication (API keys, OAuth, etc.)
- Rate limiting strategy
- Error handling for API failures
- Result filtering and pagination

### 2. Development Phase

**Set Up Development Environment:**

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create plugin template
paperez-plugin create my_plugin --source-type api

# Install development dependencies
cd my_plugin/
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-mock
```

**Implement Core Functionality:**

1. **Authentication Setup:**
```python
def __init__(self, api_key: str, base_url: str = None, **kwargs):
    super().__init__("My Source", cache_expire=3600)

    if not api_key:
        raise ValueError("API key is required")

    self.api_key = api_key
    self.base_url = base_url or "https://api.example.com"
    self.session_headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "PaperezMCP-Plugin/1.0"
    }
```

2. **Search Implementation:**
```python
async def _perform_search(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
    url = f"{self.base_url}/search"
    params = {
        "q": query,
        "limit": min(limit, 100),  # Respect API limits
        "format": "json"
    }

    # Add optional filters
    if "year" in kwargs:
        params["year"] = kwargs["year"]

    try:
        async with create_http_client() as client:
            response = await client.get(url, params=params, headers=self.session_headers)

            if response.status_code == 200:
                data = response.json()
                return self._process_results(data)
            elif response.status_code == 429:
                # Handle rate limiting
                await asyncio.sleep(60)
                return []
            else:
                logger.error(f"API error: {response.status_code}")
                return []

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []
```

3. **Result Processing:**
```python
def _process_results(self, api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []

    for item in api_data.get("results", []):
        paper_data = {
            "title": item.get("title", ""),
            "authors": self._extract_authors(item),
            "abstract": item.get("abstract", ""),
            "journal": item.get("journal", ""),
            "year": self._extract_year(item),
            "doi": item.get("doi"),
            "url": item.get("url"),
            "pdf_url": item.get("pdf_url"),
            "citation_count": item.get("citations", 0),

            # Source-specific fields
            "my_source_id": item.get("id"),
            "my_source_type": item.get("type")
        }

        standardized = self._standardize_paper(paper_data)
        results.append(standardized)

    return results
```

### 3. Testing Phase

**Unit Tests:**

```python
# tests/test_client.py
import pytest
from unittest.mock import AsyncMock, patch
from my_plugin.client import MySourceClient

class TestMySourceClient:
    def test_initialization(self):
        client = MySourceClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.source_name == "My Source"

    @pytest.mark.asyncio
    async def test_search_success(self):
        client = MySourceClient(api_key="test-key")

        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Test Paper",
                    "authors": ["Author One"],
                    "year": 2023
                }
            ]
        }

        with patch("my_plugin.client.create_http_client") as mock_client:
            mock_http = AsyncMock()
            mock_http.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_http

            results = await client.search("test query", limit=10)

            assert len(results) == 1
            assert results[0]["title"] == "Test Paper"
            assert results[0]["source"] == "My Source"
```

**Integration Tests:**

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_api_search():
    """Test with real API (requires valid API key)."""
    api_key = os.getenv("MY_SOURCE_API_KEY")
    if not api_key:
        pytest.skip("No API key provided")

    client = MySourceClient(api_key=api_key)
    results = await client.search("machine learning", limit=5)

    assert len(results) > 0
    assert all("title" in result for result in results)
```

**Manual Testing:**

```python
# test_manual.py - For development testing
import asyncio
from my_plugin.client import MySourceClient

async def main():
    client = MySourceClient(api_key="your-test-key")
    results = await client.search("artificial intelligence", limit=10)

    print(f"Found {len(results)} results:")
    for result in results:
        print(f"- {result['title']} ({result.get('year', 'N/A')})")

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Validation Phase

**Structure Validation:**

```bash
# Validate plugin structure
paperez-plugin validate .

# Fix common issues
paperez-plugin validate . --fix
```

**Security Scanning:**

```bash
# Run security scan
paperez-plugin security-scan .

# Review security report
paperez-plugin security-scan . --verbose
```

**Performance Testing:**

```python
# Performance test
import time
import asyncio

async def performance_test():
    client = MySourceClient(api_key="test-key")

    start_time = time.time()
    results = await client.search("test query", limit=50)
    end_time = time.time()

    print(f"Search took {end_time - start_time:.2f} seconds")
    print(f"Found {len(results)} results")
    print(f"Rate: {len(results) / (end_time - start_time):.2f} results/second")

asyncio.run(performance_test())
```

## API Reference

### BaseAPIClient Methods

Your plugin class must extend `BaseAPIClient` and implement:

#### Required Methods

```python
async def _perform_search(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
    """
    Perform the actual search implementation.

    Args:
        query: Search query string
        limit: Maximum number of results to return
        **kwargs: Additional search parameters specific to your source

    Returns:
        List of standardized paper dictionaries
    """
    pass
```

#### Inherited Methods

```python
async def search(self, query: str, limit: int = 5, **kwargs) -> List[Dict[str, Any]]:
    """Main search method with caching and error handling."""
    # Automatically handles caching, retries, and error logging

def _standardize_paper(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize paper data format across all sources."""
    # Ensures consistent output format

def _get_cache_key(self, query: str, limit: int, **kwargs) -> str:
    """Generate standardized cache key."""

def _log_success(self, query: str, result_count: int, **kwargs) -> None:
    """Log successful search with consistent format."""

def _log_failure(self, query: str, error: Exception) -> None:
    """Log search failure and update API status."""
```

### Standard Paper Format

All plugins must return papers in this standardized format:

```python
{
    # Required fields
    "title": str,           # Paper title
    "authors": List[str],   # List of author names
    "abstract": str,        # Paper abstract
    "journal": str,         # Publication venue
    "year": Optional[int],  # Publication year
    "doi": Optional[str],   # Digital Object Identifier
    "url": str,            # Link to paper
    "pdf_url": Optional[str], # Direct PDF link
    "citation_count": int,  # Number of citations
    "source": str,         # Source name (automatically set)

    # Optional source-specific fields
    "custom_field": Any,   # Any additional fields your source provides
}
```

### Configuration Schema

Define configuration options in your `plugin.yaml`:

```yaml
config_schema:
  api_key:
    type: string
    required: true
    description: "API key for authentication"

  rate_limit:
    type: integer
    required: false
    description: "Requests per minute"
    default: 100
    minimum: 1
    maximum: 1000

  include_preprints:
    type: boolean
    required: false
    description: "Include preprint papers"
    default: true

  custom_endpoint:
    type: string
    required: false
    description: "Custom API endpoint URL"
    format: "uri"
```

### Error Handling

Implement robust error handling in your plugin:

```python
async def _perform_search(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
    try:
        # Your search logic
        results = await self._make_api_call(query, limit)
        return self._process_results(results)

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        return []

    except RateLimitError as e:
        logger.warning(f"Rate limit exceeded: {e}")
        await asyncio.sleep(60)  # Wait before retry
        return []

    except APIError as e:
        logger.error(f"API error: {e}")
        return []

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
```

## Security Guidelines

### Code Security

1. **Input Validation:**
```python
def validate_query(self, query: str) -> str:
    """Validate and sanitize search query."""
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', query)
    return sanitized.strip()
```

2. **API Key Protection:**
```python
def __init__(self, api_key: str, **kwargs):
    # Validate API key format
    if not api_key or len(api_key) < 10:
        raise ValueError("Invalid API key format")

    # Store securely (avoid logging)
    self.api_key = api_key

    # Use in headers, not URL parameters
    self.headers = {"Authorization": f"Bearer {api_key}"}
```

3. **Rate Limiting:**
```python
import asyncio
from time import time

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def acquire(self):
        now = time()
        # Remove old requests
        self.requests = [req_time for req_time in self.requests
                        if now - req_time < self.time_window]

        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            await asyncio.sleep(sleep_time)

        self.requests.append(now)
```

### Avoid Security Anti-patterns

❌ **Don't do this:**
```python
# Never use eval or exec
eval(user_input)
exec(api_response)

# Don't log sensitive data
logger.info(f"API key: {api_key}")

# Don't ignore SSL certificates
requests.get(url, verify=False)

# Don't use shell commands
os.system(f"curl {user_url}")
```

✅ **Do this instead:**
```python
# Use proper JSON parsing
data = json.loads(api_response)

# Log safely
logger.info("API key configured")

# Verify SSL certificates
async with create_http_client(verify_ssl=True) as client:
    response = await client.get(url)

# Use HTTP client libraries
async with create_http_client() as client:
    response = await client.get(url)
```

## Distribution

### 1. Prepare for Distribution

**Update Documentation:**
```bash
# Update README.md with usage instructions
# Document configuration options
# Add examples and troubleshooting
```

**Version Your Plugin:**
```yaml
# plugin.yaml
version: "1.0.0"  # Follow semantic versioning
```

**License Your Code:**
```bash
# Add LICENSE file
# Common choices: MIT, Apache 2.0, GPL-3.0
```

### 2. Distribution Methods

#### GitHub Repository

```bash
# Create repository
git init
git add .
git commit -m "Initial plugin release"
git remote add origin https://github.com/yourname/my-plugin
git push -u origin main

# Create release
git tag v1.0.0
git push origin v1.0.0
```

Users can install with:
```bash
paperez-plugin install https://github.com/yourname/my-plugin
```

#### Python Package

```bash
# Create setup.py
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI
pip install twine
twine upload dist/*
```

Users can install with:
```bash
pip install my-plugin-package
paperez-plugin install my_plugin
```

#### Plugin Registry

Submit to the official PaperezMCP plugin registry:

```bash
# Submit plugin for review
curl -X POST https://plugins.paperez.dev/submit \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_plugin",
    "repository": "https://github.com/yourname/my-plugin",
    "version": "1.0.0"
  }'
```

### 3. Maintenance

**Update Process:**
1. Fix bugs and add features
2. Update version in `plugin.yaml`
3. Test thoroughly
4. Create new release
5. Update registry if applicable

**User Support:**
- Monitor issues in your repository
- Provide clear documentation
- Respond to security reports promptly

## Examples

See the `examples/plugins/` directory for complete, working examples:

1. **[IEEE Xplore Plugin](examples/plugins/ieee_xplore/)** - API-based integration
2. **[ResearchGate Scraper](examples/plugins/researchgate_scraper/)** - Web scraping
3. **[Institutional Repository](examples/plugins/institutional_repository/)** - Multi-protocol support

### Real-world Plugin Ideas

- **Publisher APIs**: Springer, Elsevier, Wiley, Nature
- **Government Databases**: NIH, NSF, NASA technical reports
- **Subject Repositories**: SSRN, RePEc, bioRxiv, chemRxiv
- **Institutional Collections**: University repositories, library catalogs
- **Patent Databases**: Google Patents, USPTO, EPO
- **Standards Organizations**: ISO, IEEE Standards, IETF RFCs

## Troubleshooting

### Common Issues

**1. Plugin Not Found After Installation**

```bash
# Check plugin is installed
paperez-plugin list-installed

# Verify configuration
paperez-plugin info my_plugin

# Check PaperezMCP configuration
paperez-plugin configure my_plugin
```

**2. Import Errors**

```python
# Ensure proper module structure
# Check __init__.py files exist
# Verify module_path in plugin.yaml
```

**3. API Authentication Failures**

```python
# Validate API key format
# Check rate limits
# Verify endpoint URLs
# Test with official API tools first
```

**4. No Search Results**

```python
# Test API directly
# Check query formatting
# Verify result processing logic
# Add debug logging
```

**5. Security Scan Failures**

```bash
# Review security warnings
paperez-plugin security-scan . --verbose

# Fix dangerous patterns
# Update dependencies
# Remove unnecessary imports
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in your plugin
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

### Getting Help

1. **Documentation**: Check this guide and API reference
2. **Examples**: Study the example plugins
3. **Community**: Join the PaperezMCP Discord/forum
4. **Issues**: Create GitHub issues with detailed error information
5. **Security**: Report security issues privately to security@paperez.dev

## Best Practices Summary

✅ **Do:**
- Follow the plugin template structure
- Implement comprehensive error handling
- Respect API rate limits and terms of service
- Write thorough tests
- Document configuration options clearly
- Use semantic versioning
- Validate inputs and sanitize outputs
- Cache results appropriately

❌ **Avoid:**
- Hardcoding API keys or credentials
- Ignoring rate limits
- Using unsafe eval/exec functions
- Skipping security validation
- Poor error handling
- Insufficient documentation
- Breaking changes without version updates

---

*For more information, visit the [PaperezMCP documentation](https://docs.paperez.dev) or join our [community discussions](https://github.com/paperez-mcp/paperez-mcp/discussions).*