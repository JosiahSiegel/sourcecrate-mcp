# PaperezMCP Browser UI Example

A simple, clean browser-based interface for PaperezMCP HTTP API.

## Features

- **Search Papers**: Search academic papers across 20+ databases
- **Streaming Search**: Real-time results as sources complete
- **System Status**: Check API health and source availability
- **Clean UI**: Modern, responsive design
- **Zero Backend Dependencies**: Just HTML/CSS/JavaScript

## Quick Start

### 1. Start the HTTP Server

#### Recommended: Zero-Installation with uvx

```bash
# Direct from GitHub (no installation needed!)
uvx --from 'git+https://github.com/JosiahSiegel/paperez-mcp.git[http]' paperez-http

# Or from cloned repository
cd /path/to/paperez-mcp
uvx --from '.[http]' paperez-http
```

#### Alternative Methods

```bash
# Traditional pip install
pip install -e ".[http]"
paperez-http

# Or using Python module
python -m paperez_mcp.http_server
```

The server runs on `http://localhost:8000`.

### 2. Open the UI

Open `index.html` in your browser:

```bash
# Option 1: Direct file open (from browser-ui directory)
open index.html  # macOS
xdg-open index.html  # Linux
start index.html  # Windows

# Option 2: Using a local server (recommended)
# Run from the browser-ui directory:
python -m http.server 3000
# Then visit http://localhost:3000
```

### 3. Search Papers

1. Enter a search query (e.g., "machine learning", "climate change")
2. Set max results (1-50)
3. Optionally enable streaming search
4. Click "Search"

Results show:
- Paper titles, authors, year
- Abstracts
- Links to papers, PDFs, and DOIs

## API Endpoints Used

This UI demonstrates these HTTP API endpoints:

- `POST /api/v1/search` - Browse papers (metadata only)
- `POST /api/v1/search/streaming` - Streaming search
- `GET /api/v1/status` - System status check

See the [HTTP API documentation](../docs/HTTP_API.md) for all available endpoints.

## Development

### Testing with CORS

If testing from `file://` protocol, you may encounter CORS issues.

**Solutions:**

1. **Use local server** (recommended):
   ```bash
   python -m http.server 3000
   ```

2. **Configure CORS** in `paperez_mcp/http_server.py`:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # Already configured
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Customization

**Change API Server URL:**

Edit `app.js`:
```javascript
const API_BASE_URL = 'http://your-server:8000';
```

**Styling:**

Modify `styles.css` to customize colors, fonts, and layout.

## Files

- `index.html` - Main UI structure
- `app.js` - API client logic
- `styles.css` - UI styling
- `README.md` - This file

## Production Deployment

For production use:

1. **Build a proper frontend** with React/Vue/Svelte
2. **Add authentication** to protect your API
3. **Configure CORS** to allow only your domain
4. **Use environment variables** for API URL
5. **Add rate limiting** to prevent abuse

## Next Steps

- Explore all 8 API endpoints
- Add download functionality
- Integrate PDF viewer
- Add result filtering/sorting
- Save search history

## License

MIT - See repository LICENSE file
