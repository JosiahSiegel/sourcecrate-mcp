# PaperezMCP HTTP API Reference

Complete REST API reference for PaperezMCP v1.1.0+

## Base URL

```
http://localhost:8000
```

## API Endpoints

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
  "service": "paperez-mcp"
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
  "service": "PaperezMCP HTTP API",
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

#### Browse Papers (Streaming)
```
POST /api/v1/search/streaming
```

Search with real-time results as sources complete.

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
  "output_dir": ".paperez",
  "force_category": null,
  "convert_to_markdown": true,
  "debug": false
}
```

**Parameters:**
- `query` (string, required): Search query
- `limit` (integer, optional): Max papers to download, 1-20, default 5
- `output_dir` (string, optional): Output directory, default ".paperez"
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
  "output_directory": ".paperez"
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
    "user_config": "~/.paperez/config/config.yaml",
    "project_config": "./.paperez/config/config.yaml"
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

**Swagger UI:** `http://localhost:8000/docs`
**ReDoc:** `http://localhost:8000/redoc`

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

# Search papers
response = requests.post('http://localhost:8000/api/v1/search', json={
    'query': 'quantum computing',
    'limit': 10
})
papers = response.json()
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/v1/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'quantum computing', limit: 10 })
});
const papers = await response.json();
```

### cURL
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"quantum computing","limit":10}'
```

---

## Deployment

See [Docker deployment guide](../README.md#docker-deployment) for production setup.

## License

MIT - See repository LICENSE file
