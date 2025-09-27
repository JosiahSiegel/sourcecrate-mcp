# Adding New Academic Sources to PaperezMCP

**The Simplest Way to Add Any Academic Database**

Adding a new academic source to PaperezMCP is designed to be as simple as possible. Whether you're a researcher who needs access to a specific database or a developer wanting to integrate a new API, this guide will get you there in minutes.

## 🚀 Quick Start (3 Steps)

### Step 1: Create a Plugin Template

```bash
./scripts/paperez-plugin create my_source
```

This creates `my_source_plugin.py` with all the boilerplate code you need.

### Step 2: Add Your API Logic

Edit the generated file and replace the TODO section in `_perform_search()` with your API calls.

### Step 3: Install the Plugin

```bash
./scripts/paperez-plugin install my_source_plugin.py
```

**That's it!** Your source is now available in all searches.

## 📋 Real Examples

### Example 1: IEEE Xplore (API-based)

```bash
# Create IEEE Xplore plugin with working example
./scripts/paperez-plugin example ieee_xplore

# The generated file already includes:
# - IEEE Xplore API integration
# - Authentication handling
# - Result standardization
# - Error handling

# Just add your API key to ~/.paperez/config/config.yaml:
# sources:
#   ieee_xplore:
#     config:
#       api_key: "your-ieee-api-key"

# Install it
./scripts/paperez-plugin install ieee_xplore_plugin.py
```

### Example 2: ResearchGate (Web Scraping)

```bash
# Create ResearchGate plugin with working example
./scripts/paperez-plugin example researchgate

# The generated file includes:
# - Respectful web scraping
# - Rate limiting
# - HTML parsing
# - Error recovery

# Install it (no API key needed)
./scripts/paperez-plugin install researchgate_plugin.py
```

### Example 3: Institutional Repository

```bash
# Create institutional repository plugin
./scripts/paperez-plugin example institutional

# Supports multiple repository types:
# - DSpace
# - EPrints
# - Fedora
# - OAI-PMH

# Configure for your institution in ~/.paperez/config/config.yaml:
# sources:
#   institutional:
#     config:
#       base_url: "https://repository.myuni.edu"
#       type: "dspace"

./scripts/paperez-plugin install institutional_plugin.py
```

## 🔧 Plugin Development Details

### Required Methods

Your plugin only needs to implement one method:

```python
async def _perform_search(self, query: str, limit: int, **kwargs) -> List[Dict[str, Any]]:
    """
    Your search logic goes here.

    Return a list of papers with these fields:
    - title: Paper title
    - authors: List of author names
    - abstract: Paper abstract
    - journal: Journal name
    - year: Publication year
    - doi: DOI identifier
    - url: Paper URL
    - pdf_url: Direct PDF URL (optional)
    - citation_count: Citation count (optional)
    """
```

### Configuration

Your plugin automatically gets configuration from the user's config file:

```python
def __init__(self, **config):
    super().__init__("MySource", cache_expire=3600)

    # Access user configuration
    self.api_key = config.get("api_key")
    self.base_url = config.get("base_url", "https://api.default.com")
    self.timeout = config.get("timeout", 30)
```

### Built-in Features

Your plugin automatically inherits:

- ✅ **Retry logic** with exponential backoff
- ✅ **Caching** with configurable expiration
- ✅ **Error handling** and logging
- ✅ **Result standardization**
- ✅ **Performance monitoring**

## 🏗️ Best Practices

### 1. API-Based Sources

```python
# Good: Use proper headers and authentication
headers = {
    "Authorization": f"Bearer {self.api_key}",
    "User-Agent": "PaperezMCP Academic Research Tool",
    "Accept": "application/json"
}

# Good: Handle rate limiting
if response.status_code == 429:
    retry_after = int(response.headers.get("Retry-After", 60))
    await asyncio.sleep(retry_after)
    continue

# Good: Validate responses
if response.status_code != 200:
    self.logger.warning(f"API error {response.status_code}: {response.text}")
    return []
```

### 2. Web Scraping Sources

```python
# Good: Respect robots.txt and rate limits
await asyncio.sleep(1)  # Be respectful

# Good: Use appropriate user agent
headers = {"User-Agent": "PaperezMCP Academic Research Tool"}

# Good: Handle missing elements gracefully
title = item.select_one('.title')
title_text = title.get_text(strip=True) if title else ""
```

### 3. Error Handling

```python
# Good: Comprehensive error handling
try:
    response = await client.get(url, timeout=self.timeout)
    # ... process response
except httpx.TimeoutException:
    self.logger.warning(f"Timeout searching {self.source_name}")
    return []
except httpx.HTTPError as e:
    self.logger.warning(f"HTTP error: {e}")
    return []
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
    return []
```

### 4. Configuration Management

```python
# Good: Validate required configuration
def __init__(self, **config):
    super().__init__("MySource")

    self.api_key = config.get("api_key")
    if not self.api_key:
        raise ValueError("api_key is required for MySource")

    # Provide sensible defaults
    self.base_url = config.get("base_url", "https://api.default.com")
    self.timeout = config.get("timeout", 30)
```

## 🔍 Testing Your Plugin

### Test Locally

Every generated plugin includes a test section:

```bash
# Test your plugin
python my_source_plugin.py
```

### Test with PaperezMCP

```bash
# Install and test
./scripts/paperez-plugin install my_source_plugin.py

# Test a search (after configuring credentials)
python -c "
from paperez_mcp.config import get_search_service
service = get_search_service()
# Your source will be included automatically
"
```

## 📦 Sharing Your Plugin

### Option 1: Direct File Sharing

```bash
# Share your plugin file
cp my_source_plugin.py /path/to/share/

# Others can install with:
./scripts/paperez-plugin install my_source_plugin.py
```

### Option 2: GitHub Repository

```bash
# Create a repository
git init my-paperez-plugin
git add my_source_plugin.py README.md
git commit -m "Add MySource plugin for PaperezMCP"
git push origin main

# Others can install with:
git clone https://github.com/you/my-paperez-plugin
./scripts/paperez-plugin install my-paperez-plugin/my_source_plugin.py
```

### Option 3: Python Package (Advanced)

Create a proper Python package and publish to PyPI:

```bash
pip install paperez-plugin-mysource
```

## 🚨 Common Pitfalls

### 1. ❌ Don't Block the Event Loop

```python
# Bad: Blocking synchronous calls
response = requests.get(url)  # Blocks!

# Good: Async calls
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

### 2. ❌ Don't Ignore Rate Limits

```python
# Bad: Hammering the API
for query in many_queries:
    await search(query)  # Too fast!

# Good: Respectful rate limiting
for query in many_queries:
    await search(query)
    await asyncio.sleep(1)  # Be nice
```

### 3. ❌ Don't Hardcode Configuration

```python
# Bad: Hardcoded values
API_KEY = "abc123"  # Don't do this!

# Good: Use configuration
self.api_key = config.get("api_key")
```

## 🎯 Next Steps

1. **Create your first plugin**: `./scripts/paperez-plugin create my_source`
2. **Try a working example**: `./scripts/paperez-plugin example ieee_xplore`
3. **Join the community**: Share your plugins with other researchers
4. **Contribute back**: Submit useful plugins to the main repository

## 💡 Need Help?

- **Check existing examples**: `./scripts/paperez-plugin list`
- **Review error logs**: Check the PaperezMCP logs for debugging info
- **Test incrementally**: Start with a simple API call, then add features
- **Ask the community**: Share your questions with other plugin developers

---

**Remember**: The goal is to make academic research more accessible. Every source you add helps the entire research community! 🌟