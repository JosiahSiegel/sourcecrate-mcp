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

The server runs on `http://localhost:9000`.

### 2. Verify API is Running

```bash
# Test the API endpoint
curl http://localhost:9000/health

# Should return: {"status":"healthy"}
```

### 3. Open the UI

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

### 4. Search Papers

1. Enter a search query (e.g., "machine learning", "climate change")
2. Set max results (1-50)
3. Optionally enable streaming search
4. Click "Search"

Results show:
- Paper titles, authors, year
- Abstracts
- Links to papers, PDFs, and DOIs

## Port Configuration

The UI automatically detects the API URL based on how you're running it:

| UI Access Method | UI Port | API Port | Auto-Detected URL |
|-----------------|---------|----------|-------------------|
| Direct file open | N/A | 9000 | `http://localhost:9000` |
| Local server (python -m http.server 3000) | 3000 | 9000 | `http://localhost:9000` |
| Devcontainer (VS Code) | 3001 | 9000 | `http://localhost:9000` |
| Fly.io production (same-origin) | 443 | 8080 | Same origin (HTTPS) |
| Custom deployment | Varies | Varies | Use `config.js` override |

**How it works:**
1. UI checks for `window.PAPEREZ_API_URL` from `config.js` (highest priority)
2. Auto-detects based on current page port (for local dev)
3. Falls back to `http://localhost:9000` (default local API)

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

**Option 1: Using config.js (Recommended for production)**
```bash
cp config.js.example config.js
```

Edit `config.js`:
```javascript
window.PAPEREZ_API_URL = 'https://your-api-server.com';
```

Add to `index.html` before `app.js`:
```html
<script src="config.js"></script>
<script src="app.js"></script>
```

**Option 2: Inline in HTML**
Add to `index.html`:
```html
<script>window.PAPEREZ_API_URL = 'https://your-api-server.com';</script>
<script src="app.js"></script>
```

**Option 3: Edit app.js directly (not recommended)**
```javascript
const API_BASE_URL = 'http://your-server:9000';
```

**Styling:**

Modify `styles.css` to customize colors, fonts, and layout.

## Files

- `index.html` - Main UI structure
- `app.js` - API client logic
- `styles.css` - UI styling
- `config.js.example` - Example production configuration
- `README.md` - This file

## Production Deployment

**🚀 Deploy for FREE:** See deployment guides for step-by-step instructions.

**Quick options:**

1. **Render.com** - [Quick Start](../docs/DEPLOYMENT.md)
   - Easiest setup, 100% free for hobby projects
   - Auto-deploys from GitHub
   - Cold starts after 15 min idle (by design)

2. **Fly.io** - [Complete Guide](../docs/DEPLOYMENT_FLYIO.md)
   - Recommended for production
   - Better free tier (3 VMs), no forced spin-down
   - Best for scaling to 100K+ users

**For advanced production use:**
- Add authentication to protect your API
- Configure rate limiting to prevent abuse
- Use custom domain for professional branding
- Set up monitoring and alerts

## Next Steps

- Explore all 8 API endpoints
- Add download functionality
- Integrate PDF viewer
- Add result filtering/sorting
- Save search history

## License

MIT - See repository LICENSE file
