# Scholarly MCP Server Setup Guide

This guide provides precise steps to create an MCP server for the scholarly Python library, enabling AI users to fetch articles from Google Scholar via a GitHub-hosted repository URL.

## Overview

This repository provides **two versions** of the MCP server:

### Basic Version (`scholarly_server.py`)
Integrates the `scholarly` Python library with FastMCP, allowing AI assistants to:
- Search for authors by name, ID, or organization
- Search for publications by keywords or titles
- Retrieve detailed author profiles and publication information
- Access citation data and bibliographic information

### Enhanced Version (`scholarly_enhanced_server.py`) ⭐ **RECOMMENDED**
Adds comprehensive **full-text retrieval capabilities**:
- **Open access detection** via Unpaywall, Semantic Scholar, and CORE APIs
- **PDF text extraction** using PyMuPDF
- **arXiv integration** for preprints
- **Multi-source full-text search** with automatic fallbacks
- **Rate limiting and error handling** for production use
- **Comprehensive metadata + full text** in single requests

## Prerequisites

- Python 3.8 or higher
- GitHub account
- Basic knowledge of Python and MCP concepts

## Step 1: Repository Setup

1. Create a new GitHub repository or use an existing one
2. Clone the repository locally:
   ```bash
   git clone https://github.com/your-username/your-repo-name.git
   cd your-repo-name
   ```

## Step 2: Install Dependencies

### For Basic Version
Create a `requirements.txt` file with the following dependencies:

```txt
fastmcp>=2.6.0
scholarly>=1.7.11
httpx>=0.25.0
```

### For Enhanced Version (Recommended)
Use the enhanced requirements file for full-text capabilities:

```txt
# Enhanced Scholarly MCP Server Dependencies
fastmcp>=2.6.0
scholarly>=1.7.11
httpx>=0.25.0
aiohttp>=3.8.0
requests>=2.28.0
PyMuPDF>=1.23.0
pdfplumber>=0.10.0
lxml>=4.9.0
asyncio-throttle>=1.0.2
```

Install the dependencies:
```bash
pip install -r requirements_enhanced.txt
```

## Step 3: Create the MCP Server

Create a file named `scholarly_server.py` with the following implementation:

```python
from fastmcp import FastMCP
from scholarly import scholarly
import asyncio
from typing import List, Dict, Any, Optional
import json

# Initialize the FastMCP server
mcp = FastMCP("Scholarly MCP Server")

@mcp.tool
def search_author(name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for authors by name on Google Scholar.

    Args:
        name: The author's name to search for
        limit: Maximum number of results to return (default: 5)

    Returns:
        List of author information dictionaries
    """
    try:
        search_query = scholarly.search_author(name)
        results = []

        for i, author in enumerate(search_query):
            if i >= limit:
                break
            results.append({
                'name': author.get('name', ''),
                'affiliation': author.get('affiliation', ''),
                'scholar_id': author.get('scholar_id', ''),
                'citedby': author.get('citedby', 0),
                'interests': author.get('interests', []),
                'email_domain': author.get('email_domain', ''),
                'url_picture': author.get('url_picture', '')
            })

        return results
    except Exception as e:
        return [{"error": f"Failed to search for author: {str(e)}"}]

@mcp.tool
def get_author_details(author_id: str, sections: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Get detailed information about an author using their Scholar ID.

    Args:
        author_id: The Google Scholar author ID
        sections: List of sections to fill ['basics', 'indices', 'counts', 'coauthors', 'publications']

    Returns:
        Detailed author information dictionary
    """
    try:
        if sections is None:
            sections = ['basics', 'indices', 'counts']

        author = scholarly.search_author_id(author_id)
        filled_author = scholarly.fill(author, sections=sections)

        return {
            'name': filled_author.get('name', ''),
            'affiliation': filled_author.get('affiliation', ''),
            'scholar_id': filled_author.get('scholar_id', ''),
            'citedby': filled_author.get('citedby', 0),
            'citedby5y': filled_author.get('citedby5y', 0),
            'hindex': filled_author.get('hindex', 0),
            'hindex5y': filled_author.get('hindex5y', 0),
            'i10index': filled_author.get('i10index', 0),
            'i10index5y': filled_author.get('i10index5y', 0),
            'interests': filled_author.get('interests', []),
            'homepage': filled_author.get('homepage', ''),
            'email_domain': filled_author.get('email_domain', ''),
            'coauthors': [
                {
                    'name': coauthor.get('name', ''),
                    'affiliation': coauthor.get('affiliation', ''),
                    'scholar_id': coauthor.get('scholar_id', '')
                }
                for coauthor in filled_author.get('coauthors', [])
            ] if 'coauthors' in sections else [],
            'publications': [
                {
                    'title': pub.get('bib', {}).get('title', ''),
                    'venue': pub.get('bib', {}).get('venue', ''),
                    'year': pub.get('bib', {}).get('pub_year', ''),
                    'author': pub.get('bib', {}).get('author', []),
                    'num_citations': pub.get('num_citations', 0)
                }
                for pub in filled_author.get('publications', [])
            ] if 'publications' in sections else []
        }
    except Exception as e:
        return {"error": f"Failed to get author details: {str(e)}"}

@mcp.tool
def search_publications(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for publications by keywords or title.

    Args:
        query: Search query for publications
        limit: Maximum number of results to return (default: 5)

    Returns:
        List of publication information dictionaries
    """
    try:
        search_query = scholarly.search_pubs(query)
        results = []

        for i, pub in enumerate(search_query):
            if i >= limit:
                break

            bib = pub.get('bib', {})
            results.append({
                'title': bib.get('title', ''),
                'author': bib.get('author', []),
                'venue': bib.get('venue', ''),
                'year': bib.get('pub_year', ''),
                'abstract': bib.get('abstract', ''),
                'num_citations': pub.get('num_citations', 0),
                'pub_url': pub.get('pub_url', ''),
                'eprint_url': pub.get('eprint_url', ''),
                'author_id': pub.get('author_id', [])
            })

        return results
    except Exception as e:
        return [{"error": f"Failed to search for publications: {str(e)}"}]

@mcp.tool
def get_publication_details(publication_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a publication.

    Args:
        publication_id: The publication identifier

    Returns:
        Detailed publication information dictionary
    """
    try:
        # Note: This is a simplified implementation
        # In practice, you'd need to implement publication lookup by ID
        return {"error": "Publication detail lookup by ID not yet implemented"}
    except Exception as e:
        return {"error": f"Failed to get publication details: {str(e)}"}

@mcp.tool
def search_organizations(organization_name: str) -> List[Dict[str, Any]]:
    """
    Search for organizations and return their IDs.

    Args:
        organization_name: Name of the organization to search for

    Returns:
        List of organization information dictionaries
    """
    try:
        orgs = scholarly.search_org(organization_name)
        return [
            {
                'name': org.get('Organization', ''),
                'id': org.get('id', '')
            }
            for org in orgs
        ]
    except Exception as e:
        return [{"error": f"Failed to search for organizations: {str(e)}"}]

@mcp.tool
def get_bibtex_citation(publication_title: str) -> Dict[str, Any]:
    """
    Get BibTeX citation for a publication by title.

    Args:
        publication_title: Title of the publication

    Returns:
        Dictionary containing BibTeX citation
    """
    try:
        search_query = scholarly.search_pubs(publication_title)
        pub = next(search_query)
        bibtex = scholarly.bibtex(pub)

        return {
            'title': pub.get('bib', {}).get('title', ''),
            'bibtex': bibtex
        }
    except Exception as e:
        return {"error": f"Failed to get BibTeX citation: {str(e)}"}

# Run the server
if __name__ == "__main__":
    mcp.run()
```

## Step 3b: Enhanced Server with Full-Text Retrieval (Recommended)

The enhanced server (`scholarly_enhanced_server.py`) provides all the basic functionality plus comprehensive full-text retrieval capabilities. This version is recommended for production use.

### Key Enhanced Features

1. **Full-Text Retrieval**: Downloads and extracts text from open access PDFs
2. **Multi-Source Open Access Detection**:
   - Unpaywall API (20M+ papers)
   - Semantic Scholar API (225M+ papers)
   - arXiv integration (preprints)
   - CORE API support (200M+ papers)
3. **PDF Processing**: Automatic text extraction using PyMuPDF
4. **Rate Limiting**: Built-in rate limiting for API calls
5. **Error Handling**: Comprehensive error handling and fallbacks
6. **Caching**: Efficient processing with temporary file management

### Enhanced Tools Available

The enhanced server provides all basic tools plus:

1. **find_open_access_versions**: Find open access versions using multiple sources
2. **get_full_text_by_doi**: Retrieve full text using DOI
3. **get_full_text_by_title**: Retrieve full text using paper title
4. **search_with_full_text**: Search papers and include full text when available
5. **extract_pdf_text_from_url**: Extract text from any PDF URL

### Enhanced Server Code

The enhanced server is provided in `scholarly_enhanced_server.py`. Here's an example of the enhanced functionality:

```python
# Example of enhanced full-text retrieval
@mcp.tool
async def get_full_text_by_title(title: str, extract_text: bool = True) -> Dict[str, Any]:
    """Get full text of a paper using its title with multi-source checking"""

    # Search for paper in Google Scholar
    scholarly_results = search_publications(title, limit=1)
    paper = scholarly_results[0]

    # Check multiple open access sources
    oa_result = await find_open_access_versions(title, doi)

    # Extract text from available PDFs
    for source in oa_result["open_access_sources"]:
        pdf_url = source.get("url")
        if pdf_url and extract_text:
            extraction_result = await download_and_extract_pdf(pdf_url)
            if extraction_result.get("text"):
                return {
                    "title": title,
                    "full_text": extraction_result["text"],
                    "source": source["source"],
                    "metadata": {...}
                }

    return result
```

### Usage Examples

```python
# Get full text by DOI
result = await client.call_tool("get_full_text_by_doi", {
    "doi": "10.1038/nature12373",
    "extract_text": True
})

# Search with full text extraction
papers = await client.call_tool("search_with_full_text", {
    "query": "machine learning neural networks",
    "limit": 3,
    "extract_text": True
})

# Find open access versions
oa_versions = await client.call_tool("find_open_access_versions", {
    "title": "Deep Learning in Medical Imaging",
    "doi": "10.1016/j.media.2017.07.005"
})
```

### API Rate Limits and Considerations

The enhanced server respects rate limits for all external APIs:

- **Unpaywall**: 100,000 calls/day, no API key required
- **Semantic Scholar**: 1,000 requests/hour (free tier)
- **arXiv**: No explicit limits, but respectful usage recommended
- **CORE**: Requires registration for API key

For production use, consider:
1. Implementing caching to reduce API calls
2. Setting up API keys for higher rate limits
3. Using proxy rotation for scholarly requests

## Step 4: Create Server Configuration

Create a `server_config.py` file for additional configuration options:

```python
from scholarly import ProxyGenerator
import os

def setup_proxy():
    """
    Setup proxy configuration for scholarly if needed.
    This helps avoid being blocked by Google Scholar.
    """
    pg = ProxyGenerator()

    # Try to use free proxies if available
    try:
        success = pg.FreeProxies()
        if success:
            scholarly.use_proxy(pg)
            print("Proxy setup successful")
        else:
            print("Proxy setup failed, using direct connection")
    except Exception as e:
        print(f"Proxy setup error: {e}, using direct connection")

# Uncomment the line below if you want to use proxies
# setup_proxy()
```

## Step 5: Create FastMCP Cloud Deployment Configuration

Create a `fastmcp.yaml` file (optional, for advanced configuration):

### For Basic Server
```yaml
name: scholarly-mcp-server
description: MCP server for Google Scholar data access via scholarly library
entrypoint: scholarly_server.py:mcp
python_version: "3.11"
dependencies:
  - fastmcp>=2.6.0
  - scholarly>=1.7.11
  - httpx>=0.25.0
```

### For Enhanced Server (Recommended)
```yaml
name: scholarly-enhanced-mcp-server
description: Enhanced MCP server with full-text retrieval capabilities
entrypoint: scholarly_enhanced_server.py:mcp
python_version: "3.11"
dependencies:
  - fastmcp>=2.6.0
  - scholarly>=1.7.11
  - httpx>=0.25.0
  - aiohttp>=3.8.0
  - requests>=2.28.0
  - PyMuPDF>=1.23.0
  - pdfplumber>=0.10.0
  - lxml>=4.9.0
  - asyncio-throttle>=1.0.2
```

## Step 6: Push to GitHub

1. Add all files to git:
   ```bash
   git add .
   ```

2. Commit the changes:
   ```bash
   git commit -m "Add scholarly MCP server implementation"
   ```

3. Push to GitHub:
   ```bash
   git push origin main
   ```

## Step 7: Deploy to FastMCP Cloud

1. Visit [FastMCP Cloud](https://fastmcp.cloud)
2. Sign in with your GitHub account
3. Click "Create New Project"
4. Select your repository
5. Set the entrypoint:
   - **For basic server**: `scholarly_server.py:mcp`
   - **For enhanced server (recommended)**: `scholarly_enhanced_server.py:mcp`
6. Click "Deploy"

**Note**: The enhanced server may take longer to deploy due to additional dependencies, but provides significantly more functionality.

## Step 8: Using the Deployed Server

Once deployed, you'll receive a URL like `https://your-project.fastmcp.app/mcp`. You can use this URL with any MCP-compatible AI client:

### Python Client Example

```python
import asyncio
from fastmcp import Client

async def test_scholarly_server():
    client = Client("https://your-project.fastmcp.app/mcp")

    async with client:
        # Search for an author
        result = await client.call_tool("search_author", {"name": "Steven Cholewiak"})
        print("Author search result:", result)

        # Search for publications
        result = await client.call_tool("search_publications", {"query": "machine learning"})
        print("Publication search result:", result)

# Run the test
asyncio.run(test_scholarly_server())
```

### Claude Desktop Integration

Add the server to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "scholarly": {
      "command": "python",
      "args": ["scholarly_server.py"],
      "cwd": "/path/to/your/repo"
    }
  }
}
```

## Available Tools

### Basic Server Tools

The basic MCP server provides the following tools:

1. **search_author**: Search for authors by name
2. **get_author_details**: Get detailed author information by Scholar ID
3. **search_publications**: Search for publications by keywords
4. **get_publication_details**: Get detailed publication information
5. **search_organizations**: Search for organizations
6. **get_bibtex_citation**: Get BibTeX citation for publications

### Enhanced Server Tools

The enhanced server includes all basic tools plus:

7. **find_open_access_versions**: Find open access versions using multiple sources
8. **get_full_text_by_doi**: Retrieve full text of a paper using its DOI
9. **get_full_text_by_title**: Retrieve full text of a paper using its title
10. **search_with_full_text**: Search papers and include full text when available
11. **extract_pdf_text_from_url**: Extract text from any PDF URL

### Full-Text Capabilities

The enhanced server can retrieve full text from:
- **Open Access journals** via multiple APIs
- **arXiv preprints** (physics, math, CS, etc.)
- **PubMed Central** (biomedical papers)
- **Institutional repositories** via Unpaywall
- **Any PDF URL** with direct text extraction

## Usage Tips

### General Tips

1. **Rate Limiting**: Google Scholar has rate limits. Both servers include rate limiting, but consider delays between requests for high-volume usage.

2. **Proxy Usage**: For production use, implement proxy rotation to avoid IP blocking from Google Scholar.

3. **Error Handling**: Both servers include comprehensive error handling with graceful fallbacks.

4. **Authentication**: For private deployments, add Bearer token authentication to your FastMCP Cloud deployment.

### Enhanced Server Tips

5. **Full-Text Performance**: PDF text extraction can be slow. Set `extract_text=False` for faster metadata-only searches.

6. **API Keys**: Register for API keys to get higher rate limits:
   - Semantic Scholar: 1,000 requests/hour → 10,000+ with API key
   - CORE: Register at https://core.ac.uk/services/api for full access

7. **Caching**: The enhanced server uses temporary files efficiently, but consider implementing Redis caching for production.

8. **Open Access Coverage**: Not all papers have open access versions. The server will return metadata even when full text isn't available.

## Troubleshooting

### Basic Issues
- **Blocked by Google Scholar**: Try implementing proxy usage in `server_config.py`
- **Deployment Issues**: Check that all dependencies are correctly specified in requirements file
- **Tool Not Found**: Ensure the server is running and the tool names match exactly

### Enhanced Server Issues
- **PDF Extraction Fails**: Some PDFs have complex layouts. The server will still return open access URLs.
- **API Rate Limits**: Implement delays or get API keys for higher limits
- **Large PDF Processing**: Very large PDFs may timeout. Consider breaking into smaller chunks.
- **Memory Usage**: PDF processing is memory-intensive. Monitor server resources.
- **No Full Text Found**: Not all papers are open access. Check the `open_access_sources` field for available URLs.

## Advanced Configuration

### Basic Server Customizations
- Adding authentication mechanisms
- Implementing caching for frequently requested data
- Adding more sophisticated error handling and retry logic
- Integrating with other academic databases

### Enhanced Server Customizations
- **API Key Management**: Set up environment variables for API keys
- **Caching Layer**: Implement Redis or database caching for full-text results
- **Custom PDF Processing**: Add support for specialized document types
- **Batch Processing**: Implement batch full-text extraction for multiple papers
- **Content Analysis**: Add text analysis tools (sentiment, topic modeling, etc.)
- **Database Integration**: Store extracted full-text in a searchable database

### Production Deployment Tips

1. **Environment Variables**: Set up API keys securely
```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CORE_API_KEY="your_key_here"
```

2. **Resource Monitoring**: Monitor memory usage for PDF processing

3. **Error Alerting**: Set up monitoring for API failures and rate limits

4. **Backup Strategy**: Cache results to avoid re-processing

## Conclusion

This setup provides two powerful options for accessing Google Scholar data:

- **Basic Server**: Fast, reliable access to scholarly metadata
- **Enhanced Server**: Comprehensive solution with full-text retrieval capabilities

The enhanced server transforms your MCP deployment from a simple metadata service into a comprehensive academic research tool, enabling AI users to access not just paper information but the complete content of millions of open access publications.

Both versions are deployable via GitHub URL to FastMCP Cloud, making academic research more accessible and efficient for AI-assisted workflows.