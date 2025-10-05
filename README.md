# SourceCrate 📚🚀

> **Academic paper research made easy through the Model Context Protocol (MCP)**

SourceCrate is a comprehensive MCP server that makes academic research effortless. Get papers from multiple databases, extract full-text content, and convert PDFs to markdown - all with zero-installation via uvx.

[![GitHub](https://img.shields.io/badge/GitHub-JosiahSiegel%2Fsource--crate-blue)](https://github.com/JosiahSiegel/source-crate)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Quick Start for Claude Code

### ✨ **Zero-Setup Installation (Recommended)**

**All methods now use our seamless auto-installer - no manual dependency management required!**

#### Option 1: Direct Install from GitHub
```bash
claude mcp add -s project source-crate -- uvx --from git+https://github.com/JosiahSiegel/source-crate.git source-crate
```

#### Option 2: Using Cloned Repository
Perfect for development or offline use:

```bash
# 1. Clone the repository
git clone https://github.com/JosiahSiegel/source-crate.git
cd source-crate

# 2. Connect Claude Code using our auto-installer
claude mcp add -s project source-crate -- python /path/to/source-crate/install_and_run.py

# Or using uvx (also uses auto-installer):
claude mcp add -s project source-crate -- uvx --from /path/to/source-crate source-crate
```

### 🔧 **What the Auto-Installer Does:**
- ✅ **Automatic dependency detection** - Checks if already installed
- ✅ **Smart environment setup** - Creates isolated venv when needed
- ✅ **Multi-platform support** - Windows, macOS, Linux, WSL
- ✅ **Fallback strategies** - Multiple installation methods tried automatically
- ✅ **Zero manual configuration** - Works immediately after clone/download
- ✅ **Cache-friendly** - Reuses environments for faster subsequent starts

**Note:** Changes to MCP server code still require restarting Claude Code to take effect.

### Basic Usage
Ask Claude naturally:
- "Download 3 machine learning papers"
- "Convert this PDF to markdown: /path/to/paper.pdf"
- "Help me configure source-crate"

### Available Tools (8 Functions)

| Tool | Description |
|------|-------------|
| **`download_papers`** | 📄 **MAIN TOOL** - Get/download full papers as files |
| **`browse_papers`** | 🔍 Quick metadata overview (titles/abstracts only) |
| **`browse_papers_streaming`** | 🌊 **NEW** - Real-time streaming search with faster response times |
| **`convert_pdf_to_text`** | Convert PDF to plain text files |
| **`convert_pdf_to_markdown`** | Convert single PDF to markdown |
| **`batch_convert_pdfs`** | Convert entire directories of PDFs |
| **`get_status`** | Check API health and system status |
| **`get_help`** | Configuration guide and examples |

## 🌐 HTTP Server (NEW in v1.1.0)

SourceCrate now includes an HTTP/REST API server for browser-based and HTTP client access!

### ✨ Zero-Setup Installation (Recommended)

**Start the HTTP server instantly with uvx - no manual installation required!**

#### Option 1: Direct from GitHub
```bash
uvx --from 'git+https://github.com/JosiahSiegel/source-crate.git[http]' sourcecrate-http
# Server runs on http://localhost:8000
```

#### Option 2: From Cloned Repository
```bash
# 1. Clone the repository
git clone https://github.com/JosiahSiegel/source-crate.git
cd source-crate

# 2. Run with uvx
uvx --from '.[http]' sourcecrate-http
# Server runs on http://localhost:8000
```

### Alternative: Traditional Installation

```bash
# Install with HTTP support
pip install -e ".[http]"

# Start the HTTP server
sourcecrate-http
# Server runs on http://localhost:8000
```

### Browser UI

A clean, modern web interface with advanced features for academic paper search:

**Features:**
- 🔍 **One-Click Re-Search** - Magnifying glass icon on each title for instant search
- 📊 **Smart Relevance Scoring** - Multi-signal ranking (citations, title match, recency)
- 🔗 **Intelligent Link Deduplication** - Automatic URL and source deduplication
- 📄 **Direct PDF Access** - Primary download button with alternate sources
- 🔄 **DOI Fallback System** - Automatic fallback for broken publisher URLs
- 🌓 **Dark Aged Paper Theme** - Clean monotone design, WCAG AAA compliant
- 🚀 **Real-Time Streaming** - Progressive results as sources complete (2-5s first results)

**Quick Start:**
```bash
# Option 1: Direct file open
open browser-ui/index.html  # macOS
xdg-open browser-ui/index.html  # Linux
start browser-ui/index.html  # Windows

# Option 2: Serve with local server (recommended)
cd browser-ui
python -m http.server 3000
# Then visit http://localhost:3000
```

**See:** [Browser UI Documentation](browser-ui/README.md) for complete feature details

### API Documentation

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **Full API Reference**: [docs/HTTP_API.md](docs/HTTP_API.md)

### Available Endpoints

All 8 MCP tools available as REST endpoints, plus SSE streaming:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/search` | POST | Browse papers (metadata) |
| `/api/v1/search/streaming` | POST | Streaming search (aggregated) |
| `/api/v1/search/stream` | GET | SSE progressive streaming |
| `/api/v1/download` | POST | Download papers |
| `/api/v1/convert/pdf-to-text` | POST | Convert PDF to text |
| `/api/v1/convert/pdf-to-markdown` | POST | Convert PDF to markdown |
| `/api/v1/convert/batch` | POST | Batch convert PDFs |
| `/api/v1/status` | GET | System status |
| `/api/v1/help` | GET | Configuration help |

### Example Usage

**Python:**
```python
import requests

response = requests.post('http://localhost:8000/api/v1/search',
    json={'query': 'quantum computing', 'limit': 10})
papers = response.json()
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/search', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query: 'quantum computing', limit: 10})
});
const papers = await response.json();
```

**cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"quantum computing","limit":10}'
```

### Use Cases

- **Browser-based research** - Web UI for paper search
- **Integration** - Add paper search to your apps
- **Automation** - Programmatic access via REST API
- **Remote access** - Deploy on server, access from anywhere

### 🔌 Port Configuration

The system uses consistent ports across all environments:

| Environment | Component | Port | Access |
|-------------|-----------|------|--------|
| **Local Development** | HTTP API | 8000 | `http://localhost:8000` |
| | Browser UI | 3001 | `http://localhost:3001` |
| | UI (alternate) | 3000 | `http://localhost:3000` |
| **Devcontainer (VS Code)** | HTTP API | 8000 | `http://localhost:8000` |
| | Browser UI | 3001 | `http://localhost:3001` |
| **Fly.io Production** | HTTP API (internal) | 8080 | N/A (internal only) |
| | HTTP API (external) | 443 | `https://your-app.fly.dev` |
| | Browser UI | 443 | `https://your-app.fly.dev/` |

**Auto-Detection:** The browser UI automatically detects the correct API URL:
- Local dev → `http://localhost:8000`
- Production → Same origin (HTTPS)
- Can be overridden via `config.js`

**Management Scripts:**
- `scripts/local-manager.sh` - Interactive CLI for local development
- `scripts/fly-manager.sh` - Interactive CLI for Fly.io operations

### Production Deployment

**🚀 Deploy to Fly.io:** See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete step-by-step guide.

**Why Fly.io:**
- ✅ Free tier: 3 VMs (vs 1 on alternatives)
- ✅ No forced spin-down (runs 24/7)
- ✅ Global edge network (30+ regions)
- ✅ 3x rate limits (multi-region IPs)
- ✅ Scales to 100K users ($15-30/month)
- 👉 [Complete Deployment Guide](docs/DEPLOYMENT.md)


## 📋 Scope & Use Cases

### What SourceCrate Does
SourceCrate finds **academic research papers**:
- ✅ Journal articles, preprints, conference papers
- ✅ Papers **about** topics (scholarly analysis, research)
- ✅ Metadata + PDFs + markdown conversion

### What SourceCrate Doesn't Do
- ❌ Primary literary texts/books (use [Project Gutenberg](https://gutenberg.org))
- ❌ General books (use [Google Books](https://books.google.com))
- ❌ Non-scholarly content

### Example: Humanities Research
**✅ Correct:** "scholarship on Arthurian legend" → SourceCrate finds academic papers ABOUT the topic
**❌ Incorrect:** "Le Morte d'Arthur full text" → Use Project Gutenberg for the actual book

**For primary texts, use:**
- [Project Gutenberg](https://gutenberg.org) - Public domain books
- [Internet Archive](https://archive.org) - Books, manuscripts, media
- [HathiTrust](https://hathitrust.org) - Digitized books
- [Google Books](https://books.google.com) - Book search

## 🔧 Configuration (Optional)

### Environment Variables (Enhanced Performance)
```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CROSSREF_EMAIL="your_email@example.com"
export NCBI_API_KEY="your_ncbi_api_key"  # Recommended: 10 RPS vs 3 RPS default
```

**API Key Benefits:**
- **NCBI/PubMed**: Register at [NCBI](https://www.ncbi.nlm.nih.gov/account/) for 10 RPS (vs 3 RPS default)
- **Semantic Scholar**: Higher rate limits for academic research
- **CrossRef**: Email contact improves service reliability

### Custom Configuration Files

SourceCrate supports **multiple configuration files** organized by research domain. Create any YAML file in `.sourcecrate/config/` directory:

#### Option 1: Single Custom Config
```bash
mkdir -p .sourcecrate/config/
# Create .sourcecrate/config/my_custom.yaml
```

```yaml
# .sourcecrate/config/my_custom.yaml
version: "1.0"
use_default_sources: true
sources:
  my_institution_api:
    name: my_institution_api
    type: http_api
    enabled: true
    timeout: 30
    config:
      description: My University Research Database
      base_url: https://api.myuni.edu
      search_path: /search
      query_param: q
      field_mappings:
        title: title
        authors: authors
        abstract: abstract
        year: publication_year
        url: link
      rate_limit_delay: 0.5
categories:
  my_specialty:
    name: my_specialty
    display_name: My Research Specialty
    description: Custom category for my field
    sources:
      - my_institution_api
      - crossref  # Reference built-in sources
    max_results_per_source: 10
```

#### Option 2: Domain-Specific Files
```bash
# Create specialized config files by domain
.sourcecrate/config/chemistry.yaml      # Chemistry sources
.sourcecrate/config/engineering.yaml    # Engineering databases
.sourcecrate/config/local_sources.yaml  # Institution-specific APIs
```

All YAML files in `.sourcecrate/config/` are automatically loaded and merged with built-in sources.

Use `get_help` tool for complete configuration schemas and examples.

## 🛠️ Troubleshooting

### Auto-Installer Issues

If you encounter problems with the automatic installation:

#### Problem: "No papers found" with empty api_status
```json
{
  "results": [],
  "total_found": 0,
  "api_status": {},
  "sources_used": []
}
```

**Cause:** Dependencies weren't properly installed or API clients failed to initialize.

**Solutions:**
1. **Restart Claude Code** after installation
2. **Check installation logs** - Look for dependency installation failures in the terminal
3. **Manual fallback installation:**
   ```bash
   # Navigate to the source-crate directory
   cd /path/to/source-crate

   # Run the installer manually to see detailed output
   python install_and_run.py
   ```
4. **Force clean installation:**
   ```bash
   # Remove cached venv and reinstall
   rm -rf .venv
   python install_and_run.py
   ```

#### Problem: "Module not found" errors
**Solution:** The auto-installer creates isolated environments. Ensure you're using the correct MCP configuration:
```json
{
  "mcpServers": {
    "source-crate": {
      "type": "stdio",
      "command": "python",
      "args": ["/path/to/source-crate/install_and_run.py"]
    }
  }
}
```

#### Problem: Slow first-time startup
**Expected behavior:** First run takes 1-2 minutes for dependency installation. Subsequent runs are fast thanks to caching.

## 🌟 Features

- 🔍 **Multi-Source Search** - 15+ verified legal academic APIs across all disciplines
- 🔧 **Fully Extensible** - Add custom sources via YAML configuration
- 📖 **Unlimited PDF Processing** - No page or character limits
- 🔄 **Zero-Token Conversion** - PDF to markdown without AI usage
- ⚡ **Intelligent Fallback** - Robust multi-source search
- 🗄️ **Smart Caching** - 1GB disk cache for performance

## 📚 Documentation

- **[HTTP API Reference](docs/HTTP_API.md)** - Complete REST API documentation
- **[Configuration Guide](docs/configuration.md)** - Custom sources and advanced config
- **[Custom Source Guide](docs/CUSTOM_SOURCE_GUIDE.md)** - Add your own academic databases
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment to Fly.io
- **[Terms of Service](docs/legal/TERMS_OF_SERVICE.md)** - Legal compliance and usage terms
- **[Development Guide](docs/development/VALIDATION.md)** - Validation and testing

## ⚖️ Legal & Ethical Usage

**📋 [Complete Terms of Service](docs/legal/TERMS_OF_SERVICE.md) - Full legal compliance details and user obligations**

**All 15+ enabled sources verified legal for academic research (2025):**

### Scientific & General Sources
- **[OpenAlex](https://docs.openalex.org/)** - Open catalog of 240M+ scholarly works, fully open access, no authentication required
- **[CrossRef](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)** - Official API from non-profit organization, requires email contact (configured)
- **[Semantic Scholar](https://www.semanticscholar.org/product/api#Terms-of-Service)** - Microsoft/Allen Institute official API, 1 RPS rate limit respected
- **[arXiv](https://info.arxiv.org/help/api/user-manual.html)** - Cornell University preprint repository, 1 request per 3 seconds
- **[DOAJ](https://doaj.org/api/docs/)** - Directory of Open Access Journals, 2 requests/second limit respected

### Medical & Biomedical Sources
- **[PubMed/PMC](https://www.ncbi.nlm.nih.gov/home/about/policies/)** - NIH/NCBI government databases, 3 RPS default rate limit
- **[Europe PMC](https://europepmc.org/privacy)** - European biomedical database, ~10 requests/time period limit
- **[ClinicalTrials.gov](https://clinicaltrials.gov/data-about-studies/learn-about-this-site/terms-and-conditions)** - US government database, ~50 requests/minute, public domain

### Business & Economics Sources
- **[RePEc](https://ideas.repec.org/api.html)** - Economics research papers (5M+ items), public domain bibliographic data

### Specialized Domain Sources ✅
- **[Open Library](https://openlibrary.org/developers/api)** - Internet Archive's book database, humanities focus
- **[CORE Repository](https://core.ac.uk/services/api/)** - Open access research aggregator, demo API key
- **[CourtListener](https://www.courtlistener.com/api/rest-info/)** - Free Law Project non-profit, legal opinions database

### Recently Disabled Sources (2025 ToS Changes)
- **Federal Register** - DISABLED: Now requires IP-based access approval due to anti-scraping measures
- **Internet Archive** - DISABLED: API terms unclear as of 2025, requires verification

### Previously Disabled Sources (Compliance Issues)
- **Google Scholar** - No official API available
- **SSRN** - ToS restrictions on data mining

**Compliance measures (verified 2025):**
- ✅ **ToS verification completed** for all 15+ enabled sources as of 2025
- ✅ **Strict rate limiting** per each source's requirements (0.05s to 1.0s delays)
- ✅ **Email contact** configured where required (CrossRef: <research@sourcecrate.org>)
- ✅ **Academic research use only** - all sources designed for scholarly access
- ✅ **Attribution requirements** met with proper source citation
- ✅ **Government databases** prioritized for public domain content
- ✅ **Official APIs only** - no web scraping or unofficial endpoints
- ✅ **Proactive compliance monitoring** - sources disabled if ToS change

**Legal Disclaimer - Custom Source Liability:**
- SourceCrate provides legal compliance only for default configuration sources
- Users who modify configurations assume full legal responsibility for compliance
- Custom source additions are solely under user control and legal liability
- Users must independently verify Terms of Service compliance for any modifications
- SourceCrate disclaims all responsibility for user-configured sources outside defaults
- Institutional and legal compliance for custom sources is the user's sole responsibility

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License & Terms

- **Software License:** MIT License - see the [LICENSE](LICENSE) file for details
- **Terms of Service:** [TERMS_OF_SERVICE.md](docs/legal/TERMS_OF_SERVICE.md) - Legal compliance and usage terms

---

## Ready to Get Started?

**Transform academic research with AI! Zero installation required! 🚀**