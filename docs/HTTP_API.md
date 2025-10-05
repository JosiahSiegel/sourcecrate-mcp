# SourceCrate HTTP API Reference

Complete REST API reference for SourceCrate v1.1.0+

## Quick Start

### Start the Server (Zero-Installation)

**Recommended: Use uvx for instant setup:**

```bash
# Direct from GitHub - no installation needed!
uvx --from 'git+https://github.com/JosiahSiegel/source-crate.git[http]' sourcecrate-http
```

**Alternative methods:**

```bash
# From cloned repository
cd /path/to/source-crate
uvx --from '.[http]' sourcecrate-http

# Traditional pip install
pip install -e ".[http]"
sourcecrate-http

# Using Python module
python -m source_crate.http_server
```

Server runs on:
- **Port 9000** when using `local-manager.sh` script (recommended for development)
- **Port 8000** when running directly via `sourcecrate-http` or Python module

## Base URL

```
http://localhost:9000  # local-manager.sh (default for browser UI)
http://localhost:8000  # direct server (Python/uvx)
```

You can customize the port with `--port` flag or `HTTP_PORT` environment variable.

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/` | GET | API information |
| `/api/v1/search` | POST | Browse papers (metadata only) |
| `/api/v1/search/streaming` | POST | Browse papers (streaming, aggregated) |
| `/api/v1/search/stream` | GET | Browse papers (SSE progressive stream) |
| `/api/v1/download` | POST | Download papers |
| `/api/v1/convert/pdf-to-text` | POST | Convert PDF to text |
| `/api/v1/convert/pdf-to-markdown` | POST | Convert PDF to markdown |
| `/api/v1/convert/batch` | POST | Batch convert PDFs |
| `/api/v1/status` | GET | System status |
| `/api/v1/help` | GET | Configuration help |

### Health & Status

#### Health Check
```
GET /health
```

Returns server health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "source-crate"
}
```

#### API Information
```
GET /
```

Returns API version and available endpoints.

**Response:**
```json
{
  "service": "SourceCrate HTTP API",
  "version": "1.1.0",
  "description": "Academic paper research made easy",
  "docs": "/docs",
  "endpoints": { ... }
}
```

---

### Paper Search

#### Browse Papers
```
POST /api/v1/search
```

Search academic papers and return metadata/abstracts only.

**Request Body:**
```json
{
  "query": "machine learning",
  "limit": 10,
  "force_category": null,
  "debug": false
}
```

**Parameters:**
- `query` (string, required): Search query (keywords, DOI, author, title)
- `limit` (integer, optional): Max results, 1-50, default 10
- `force_category` (string, optional): Force specific source category
- `debug` (boolean, optional): Include diagnostic information, default false

**Response:**
```json
{
  "results": [
    {
      "title": "Paper Title",
      "authors": ["Author 1", "Author 2"],
      "abstract": "Paper abstract...",
      "year": 2024,
      "doi": "10.1000/xyz",
      "journal": "Journal Name",
      "url": "https://...",
      "pdf_url": "https://.../paper.pdf",
      "source": "arXiv",
      "is_downloadable": true
    }
  ],
  "total_found": 10,
  "api_status": { ... },
  "sources_used": ["arXiv", "CrossRef"],
  "query": "machine learning"
}
```

#### Browse Papers (Streaming - Aggregated Response)
```
POST /api/v1/search/streaming
```

Search with real-time results as sources complete, returned as a single aggregated response.

**Request Body:**
```json
{
  "query": "quantum computing",
  "limit": 10,
  "force_category": null,
  "debug": false
}
```

**Response:**
```json
{
  "streaming_results": [ ... ],
  "streaming_summary": {
    "sources_completed": ["arXiv", "Semantic Scholar"],
    "total_time_seconds": 3.2
  },
  "early_results": [ ... ],
  "final_results": [ ... ]
}
```

#### Browse Papers (Server-Sent Events Stream)
```
GET /api/v1/search/stream?query=machine+learning&limit=10&pdf_only=false&min_relevance=0
```

Search with true progressive streaming via Server-Sent Events (SSE). Results appear incrementally as each source completes.

**Query Parameters:**
- `query` (string, required): Search query (URL-encoded)
- `limit` (integer, optional): Max results, 1-50, default 10
- `force_category` (string, optional): Force specific source category
- `debug` (boolean, optional): Include diagnostic information, default false
- `pdf_only` (boolean, optional): Only papers with direct PDF downloads, default false
- `min_relevance` (integer, optional): Minimum relevance score 0-100, default 0

**Response Format:** Server-Sent Events (text/event-stream)

**Event Types:**

1. **`search_start`** - Search initiated
```json
{
  "query": "machine learning",
  "limit": 10,
  "timestamp": 1704067200.0
}
```

2. **`source_start`** - Source began searching (not currently sent)

3. **`results`** - New papers found from a source
```json
{
  "source": "arXiv",
  "papers": [{
    "title": "Paper Title",
    "authors": ["Author 1"],
    "abstract": "...",
    "year": 2024,
    "doi": "10.1000/xyz",
    "pdf_url": "https://.../paper.pdf",
    "citation_count": 100,
    "relevance_score": 0.85
  }],
  "total_so_far": 5
}
```

4. **`source_complete`** - Source finished searching
```json
{
  "source": "Semantic Scholar",
  "count": 8,
  "completed": 2,
  "total": 5
}
```

5. **`progress`** - Overall search progress
```json
{
  "completed": 3,
  "total": 5,
  "percentage": 60.0,
  "results_count": 15
}
```

6. **`complete`** - Search finished
```json
{
  "total_results": 20,
  "sources_searched": 5,
  "query": "machine learning",
  "timestamp": 1704067220.0
}
```

7. **`error`** - Error occurred
```json
{
  "source": "PubMed",
  "error": "Connection timeout",
  "fatal": false
}
```

**JavaScript Client Example:**
```javascript
const eventSource = new EventSource(
  '/api/v1/search/stream?query=machine+learning&limit=10&pdf_only=true&min_relevance=35'
);

eventSource.addEventListener('search_start', (e) => {
  const data = JSON.parse(e.data);
  console.log('Search started:', data.query);
});

eventSource.addEventListener('results', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Found ${data.papers.length} papers from ${data.source}`);
  // Add data.papers to UI
});

eventSource.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Progress: ${data.percentage}%`);
});

eventSource.addEventListener('complete', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Search complete: ${data.total_results} papers`);
  eventSource.close();
});

eventSource.addEventListener('error', (e) => {
  const data = JSON.parse(e.data);
  if (data.fatal) {
    console.error('Fatal error:', data.error);
    eventSource.close();
  } else {
    console.warn(`Source ${data.source} error:`, data.error);
  }
});
```

**Features:**
- Progressive results (first papers in 2-5 seconds)
- Real-time progress updates
- Client-side filtering by PDF availability and relevance
- Connection timeout: 5 minutes maximum
- Keepalive: Comments every 30 seconds
- Automatic cleanup on disconnect

---

### Paper Download

#### Download Papers
```
POST /api/v1/download
```

Download full papers and convert to markdown/PDF.

**Request Body:**
```json
{
  "query": "climate change",
  "limit": 5,
  "output_dir": ".sourcecrate",
  "force_category": null,
  "convert_to_markdown": true,
  "debug": false
}
```

**Parameters:**
- `query` (string, required): Search query
- `limit` (integer, optional): Max papers to download, 1-20, default 5
- `output_dir` (string, optional): Output directory, default ".sourcecrate"
- `force_category` (string, optional): Force specific source category
- `convert_to_markdown` (boolean, optional): Convert PDFs to markdown, default true
- `debug` (boolean, optional): Include diagnostic information

**Response:**
```json
{
  "results": [
    {
      "title": "Paper Title",
      "authors": ["Author 1"],
      "local_pdf": "/path/to/paper.pdf",
      "local_markdown": "/path/to/paper_full.md",
      "download_success": true,
      "markdown_characters": 15000
    }
  ],
  "total_found": 5,
  "downloaded_count": 5,
  "output_directory": ".sourcecrate"
}
```

---

### PDF Conversion

#### Convert PDF to Text
```
POST /api/v1/convert/pdf-to-text
```

Convert a local PDF file to plain text.

**Request Body:**
```json
{
  "file_path": "/path/to/paper.pdf",
  "output_path": null,
  "title": "Optional Title",
  "authors": ["Author 1", "Author 2"]
}
```

**Parameters:**
- `file_path` (string, required): Path to local PDF file
- `output_path` (string, optional): Output path for text file
- `title` (string, optional): Document title for header
- `authors` (array, optional): List of authors

**Response:**
```json
{
  "success": true,
  "text_path": "/path/to/paper_full.txt",
  "text_length": 25000,
  "original_file": "/path/to/paper.pdf",
  "pages_extracted": 10,
  "file_size": 524288,
  "extraction_method": "PyMuPDF Local"
}
```

#### Convert PDF to Markdown
```
POST /api/v1/convert/pdf-to-markdown
```

Convert a local PDF file to formatted markdown.

**Request Body:**
```json
{
  "file_path": "/path/to/paper.pdf",
  "title": "Paper Title",
  "authors": ["Author 1"],
  "output_path": null
}
```

**Response:**
```json
{
  "success": true,
  "markdown_path": "/path/to/paper_full.md",
  "markdown_length": 30000,
  "original_file": "/path/to/paper.pdf",
  "pages_extracted": 10
}
```

#### Batch Convert PDFs
```
POST /api/v1/convert/batch
```

Convert all PDFs in a directory to markdown.

**Request Body:**
```json
{
  "directory": "articles",
  "output_dir": "converted"
}
```

**Response:**
```json
{
  "success": true,
  "directory": "articles",
  "output_directory": "converted",
  "total_files": 5,
  "successful_conversions": 5,
  "failed_conversions": 0,
  "files": [
    {
      "input_file": "articles/paper1.pdf",
      "output_file": "converted/paper1_full.md",
      "success": true,
      "characters": 25000
    }
  ]
}
```

---

### System

#### Get Status
```
GET /api/v1/status?force_reload=false
```

Get comprehensive system status.

**Query Parameters:**
- `force_reload` (boolean, optional): Force reload configuration, default false

**Response:**
```json
{
  "api_status": {
    "arxiv": true,
    "crossref": true,
    "semantic_scholar": true,
    "pubmed": true
  },
  "cache_stats": {
    "size": "125 MB",
    "items": 1500
  },
  "config": {
    "categories": {
      "total_categories": 12,
      "functional_categories": 12
    },
    "sources": {
      "total_sources": 25,
      "enabled_sources": 22
    }
  },
  "health_report": { ... }
}
```

#### Get Help
```
GET /api/v1/help
```

Get configuration guidance and help.

**Response:**
```json
{
  "config_guide": "Configuration instructions...",
  "file_paths": {
    "user_config": "~/.sourcecrate/config/config.yaml",
    "project_config": "./.sourcecrate/config/config.yaml"
  },
  "schema_info": { ... },
  "examples": [ ... ]
}
```

---

## Error Responses

All endpoints return standard error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "detail": "The requested resource was not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred"
}
```

---

## Interactive Documentation

**Swagger UI:** `http://localhost:9000/docs` (or `:8000/docs` if using direct server)
**ReDoc:** `http://localhost:9000/redoc` (or `:8000/redoc` if using direct server)

**Note:** The SSE streaming endpoint (`/api/v1/search/stream`) is best tested in a browser with EventSource or using the browser UI, as Swagger UI has limited SSE support.

---

## Authentication

Currently, the API has no authentication. For production:

1. **Add API key authentication**:
   ```python
   from fastapi.security import APIKeyHeader

   api_key_header = APIKeyHeader(name="X-API-Key")

   @app.post("/api/v1/search")
   async def search(request: SearchRequest, api_key: str = Depends(api_key_header)):
       # Validate API key
       ...
   ```

2. **Add rate limiting**:
   ```python
   from slowapi import Limiter

   limiter = Limiter(key_func=get_remote_address)

   @app.post("/api/v1/search")
   @limiter.limit("10/minute")
   async def search(...):
       ...
   ```

---

## CORS Configuration

CORS is enabled for all origins by default. For production, restrict to your domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Rate Limits

No rate limits by default. Recommended for production:

- **Search**: 10 requests/minute per IP
- **Download**: 5 requests/minute per IP
- **Conversion**: 20 requests/minute per IP
- **Status/Help**: Unlimited

---

## Example Clients

### Python
```python
import requests

# Search papers (standard)
response = requests.post('http://localhost:9000/api/v1/search', json={
    'query': 'quantum computing',
    'limit': 10
})
papers = response.json()

# SSE streaming (requires sseclient-py)
from sseclient import SSEClient

messages = SSEClient('http://localhost:9000/api/v1/search/stream?query=quantum+computing&limit=10')
for msg in messages:
    if msg.event == 'results':
        import json
        data = json.loads(msg.data)
        print(f"Found {len(data['papers'])} papers from {data['source']}")
    elif msg.event == 'complete':
        break
```

### JavaScript (Standard)
```javascript
const response = await fetch('http://localhost:9000/api/v1/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'quantum computing', limit: 10 })
});
const papers = await response.json();
```

### JavaScript (SSE Streaming)
```javascript
const eventSource = new EventSource('/api/v1/search/stream?query=quantum+computing&limit=10');

eventSource.addEventListener('results', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Found ${data.papers.length} papers from ${data.source}`);
  // Render papers to UI
});

eventSource.addEventListener('complete', (e) => {
  const data = JSON.parse(e.data);
  console.log(`Complete: ${data.total_results} papers`);
  eventSource.close();
});
```

### cURL
```bash
# Standard search
curl -X POST http://localhost:9000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"quantum computing","limit":10}'

# SSE streaming (requires curl with HTTP/2 support)
curl -N http://localhost:9000/api/v1/search/stream?query=quantum+computing&limit=10
```

---

## Deployment

See [Docker deployment guide](../README.md#docker-deployment) for production setup.

## License

MIT - See repository LICENSE file
