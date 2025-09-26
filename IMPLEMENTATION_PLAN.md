# Implementation Plan: Improving Historical/Humanities Paper Access

## Problem Statement
The current paperez-mcp system fails to find downloadable papers for historical/humanities topics like "Balfour Declaration" because:
- Historical papers are mostly paywalled on CrossRef
- arXiv only contains STEM papers
- Semantic Scholar has limited historical content
- Google Scholar (which often finds open access versions) is not working
- Phrase search is too restrictive when exact phrases don't exist

## Implementation Strategy

### 1. Enhance Search Strategy for Non-STEM Topics

#### 1.1 Implement Fallback Search Strategy
**File: `paperez_mcp/api_clients/arxiv_client.py`**
```python
async def search_arxiv(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    # Try phrase search first
    results = await _search_with_strategy(query, limit, use_phrase=True)

    # If no results and multi-word query, try keyword search
    if len(results) == 0 and ' ' in query:
        results = await _search_with_strategy(query, limit, use_phrase=False)

    return results
```

#### 1.2 Query Reformulation for Historical Topics
**File: `paperez_mcp/utils/query_processor.py`** (new file)
```python
def generate_alternative_queries(query: str) -> List[str]:
    """Generate alternative queries for better coverage"""
    alternatives = [query]

    # Historical topic patterns
    historical_expansions = {
        "Balfour Declaration": ["British Mandate Palestine", "1917 Balfour", "Zionism British"],
        "World War": ["Great War", "WWI", "WWII", "1914-1918", "1939-1945"],
        # Add more patterns
    }

    for pattern, expansions in historical_expansions.items():
        if pattern.lower() in query.lower():
            alternatives.extend(expansions)

    return alternatives
```

### 2. Improve Open Access Discovery

#### 2.1 Add CORE API Integration
**File: `paperez_mcp/api_clients/core_client.py`** (new file)
```python
"""
CORE API client for open access papers
https://core.ac.uk/services/api
"""

async def search_core(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search CORE for open access papers"""
    url = "https://api.core.ac.uk/v3/search/works"
    params = {
        "q": query,
        "limit": limit,
        "fullText": True  # Only papers with full text
    }

    headers = {
        "Authorization": f"Bearer {config.core_api_key}"  # Need to add to config
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("results", []):
                if item.get("downloadUrl"):  # Only include if has PDF
                    results.append({
                        "title": item.get("title"),
                        "authors": item.get("authors", []),
                        "abstract": item.get("abstract"),
                        "pdf_url": item.get("downloadUrl"),
                        "source": "CORE",
                        "open_access": True
                    })
            return results
    return []
```

#### 2.2 Add DOAJ Integration
**File: `paperez_mcp/api_clients/doaj_client.py`** (new file)
```python
"""
Directory of Open Access Journals API client
https://doaj.org/api/v3/docs
"""

async def search_doaj(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search DOAJ for open access journal articles"""
    url = "https://doaj.org/api/v3/search/articles"
    params = {
        "query": query,
        "pageSize": limit
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("results", []):
                # Extract PDF URL from links
                pdf_url = None
                for link in item.get("bibjson", {}).get("link", []):
                    if link.get("type") == "fulltext":
                        pdf_url = link.get("url")
                        break

                if pdf_url:
                    results.append({
                        "title": item.get("bibjson", {}).get("title"),
                        "authors": [a.get("name") for a in item.get("bibjson", {}).get("author", [])],
                        "abstract": item.get("bibjson", {}).get("abstract"),
                        "pdf_url": pdf_url,
                        "source": "DOAJ",
                        "open_access": True
                    })
            return results
    return []
```

#### 2.3 Add SocArXiv for Social Sciences
**File: `paperez_mcp/api_clients/socarxiv_client.py`** (new file)
```python
"""
SocArXiv (OSF Preprints) client for social science papers
"""

async def search_socarxiv(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search SocArXiv for social science preprints"""
    url = "https://api.osf.io/v2/preprints/"
    params = {
        "filter[provider]": "socarxiv",
        "filter[title,description]": query,
        "page[size]": limit
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data.get("data", []):
                attrs = item.get("attributes", {})
                # Get PDF URL from primary file
                pdf_url = item.get("links", {}).get("preprint_download")

                if pdf_url:
                    results.append({
                        "title": attrs.get("title"),
                        "authors": attrs.get("authors", []),
                        "abstract": attrs.get("description"),
                        "pdf_url": pdf_url,
                        "source": "SocArXiv",
                        "open_access": True
                    })
            return results
    return []
```

### 3. Fix Google Scholar Integration

#### 3.1 Improve Proxy Configuration
**File: `paperez_mcp/api_clients/google_scholar_client.py`**
```python
def setup_scholarly_proxy():
    """Enhanced proxy setup with multiple fallbacks"""
    proxy_methods = [
        ("scraperapi", setup_scraperapi),
        ("free_proxies", setup_free_proxies),
        ("tor", setup_tor_proxy),
        ("no_proxy", setup_no_proxy)
    ]

    for name, setup_func in proxy_methods:
        try:
            if setup_func():
                logger.info(f"✅ Google Scholar configured with {name}")
                return True
        except Exception as e:
            logger.warning(f"⚠️ {name} failed: {e}")

    return False

def setup_tor_proxy():
    """Try Tor proxy for Google Scholar"""
    try:
        pg = ProxyGenerator()
        pg.Tor()  # Requires tor to be installed
        scholarly.use_proxy(pg)
        # Test the proxy
        test_query = scholarly.search_pubs("test")
        next(test_query)
        return True
    except:
        return False
```

#### 3.2 Add Retry Logic with Different Strategies
**File: `paperez_mcp/api_clients/google_scholar_client.py`**
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=30))
async def search_google_scholar_with_retry(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search with automatic proxy rotation on failure"""
    try:
        return await _search_google_scholar(query, limit)
    except Exception as e:
        logger.warning(f"Google Scholar search failed, rotating proxy: {e}")
        setup_scholarly_proxy()  # Try different proxy
        raise  # Trigger retry
```

### 4. Add Smart Query Detection

#### 4.1 Topic Classification
**File: `paperez_mcp/utils/topic_classifier.py`** (new file)
```python
from typing import Dict, List

def classify_query_topic(query: str) -> Dict[str, float]:
    """Classify query into topic categories"""

    # Keywords for different domains
    DOMAIN_KEYWORDS = {
        "stem": ["algorithm", "computation", "neural", "quantum", "equation",
                 "theorem", "proof", "optimization", "machine learning", "AI"],
        "medical": ["disease", "treatment", "clinical", "patient", "therapy",
                   "drug", "cancer", "diagnosis", "medical", "health"],
        "historical": ["history", "historical", "war", "century", "empire",
                      "declaration", "treaty", "revolution", "colonial", "mandate"],
        "social_science": ["society", "social", "political", "economic", "culture",
                          "psychology", "anthropology", "sociology", "demographic"]
    }

    query_lower = query.lower()
    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in query_lower)
        scores[domain] = score / len(keywords)

    return scores

def get_recommended_sources(query: str) -> List[str]:
    """Recommend sources based on query topic"""
    scores = classify_query_topic(query)

    # Determine primary topic
    primary_topic = max(scores, key=scores.get)

    if primary_topic == "stem":
        return ["arxiv", "semantic_scholar", "crossref"]
    elif primary_topic == "medical":
        return ["pubmed", "semantic_scholar", "crossref"]
    elif primary_topic == "historical":
        return ["core", "doaj", "socarxiv", "google_scholar", "crossref"]
    elif primary_topic == "social_science":
        return ["socarxiv", "core", "semantic_scholar", "crossref"]
    else:
        return ["semantic_scholar", "crossref", "arxiv"]  # Default
```

#### 4.2 Update Smart Search to Use Topic Detection
**File: `paperez_mcp/utils/smart_search.py`**
```python
async def smart_downloadable_search(query: str, limit: int, ...) -> List[Dict[str, Any]]:
    """Enhanced smart search with topic awareness"""

    # Get recommended sources for this query
    recommended_sources = get_recommended_sources(query)

    # Reorder sources based on recommendation
    source_priority = []
    for source in recommended_sources:
        if source == "arxiv":
            source_priority.append(("arxiv", "arXiv preprints"))
        elif source == "core":
            source_priority.append(("core", "CORE open access"))
        # ... etc

    # Skip sources not recommended for this topic
    if "historical" in classify_query_topic(query) and classify_query_topic(query)["historical"] > 0.3:
        # Skip arXiv for clearly historical topics
        source_priority = [s for s in source_priority if s[0] != "arxiv"]
```

### 5. Immediate Quick Fix

#### 5.1 Less Restrictive Phrase Search
**File: `paperez_mcp/api_clients/semantic_scholar_client.py`**
```python
async def search_semantic_scholar(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Enhanced search with fallback"""

    # Try phrase search first
    formatted_query = f'"{query}"' if ' ' in query else query
    results = await _search_semantic_scholar_internal(formatted_query, limit)

    # If no results with phrase search, try without quotes
    if len(results) == 0 and ' ' in query:
        results = await _search_semantic_scholar_internal(query, limit)

    return results
```

#### 5.2 Add Comprehensive Logging
**File: `paperez_mcp/utils/smart_search.py`**
```python
import json

async def smart_downloadable_search(...):
    """Smart search with detailed logging"""

    search_log = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "sources_searched": [],
        "results_per_source": {}
    }

    for source_name, description in source_priority:
        try:
            results = await search_func(query, search_limit_per_source)
            search_log["sources_searched"].append(source_name)
            search_log["results_per_source"][source_name] = {
                "count": len(results),
                "has_pdfs": sum(1 for r in results if r.get("pdf_url")),
                "sample": results[0].get("title") if results else None
            }
            logger.info(f"Search log: {json.dumps(search_log, indent=2)}")
```

## Implementation Priority

1. **Phase 1 (Immediate)**: Quick fixes
   - Implement fallback from phrase to keyword search
   - Add detailed logging
   - Fix Google Scholar proxy

2. **Phase 2 (Short term)**: New sources
   - Add CORE API integration
   - Add DOAJ integration
   - Add SocArXiv for social sciences

3. **Phase 3 (Medium term)**: Intelligence
   - Implement topic classification
   - Add query reformulation
   - Source recommendation based on topic

## Configuration Updates Needed

**File: `paperez_mcp/config.py`**
```python
class Config:
    # Existing configs...

    # New API keys
    core_api_key: Optional[str] = os.getenv("CORE_API_KEY")

    # Feature flags
    enable_fallback_search: bool = True
    enable_topic_detection: bool = True
    enable_query_reformulation: bool = True
```

## Testing Strategy

1. **Test Historical Queries**:
   - "Balfour Declaration"
   - "Treaty of Versailles"
   - "American Revolution"

2. **Test STEM Queries** (should still work):
   - "machine learning"
   - "quantum computing"

3. **Test Mixed Queries**:
   - "history of computing"
   - "medical ethics"

## Success Metrics

- Historical queries should return at least 3 downloadable papers
- Response time should remain under 10 seconds
- Download success rate should improve from 0% to >30% for humanities topics
- False positive rate (irrelevant papers) should remain <10%