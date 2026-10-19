# SourceCrate 📚🚀

> **Academic paper research made easy through the Model Context Protocol (MCP)**

SourceCrate is a comprehensive MCP server that makes academic research effortless. Get papers from multiple databases, extract full-text content, and convert PDFs to markdown - with isolated installation through uvx.

[![GitHub](https://img.shields.io/badge/GitHub-JosiahSiegel%2Fsource--crate--mcp-blue)](https://github.com/JosiahSiegel/sourcecrate-mcp)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Install in any MCP-capable agent

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git on PATH.
No SourceCrate account, API key, hosted service, or repository clone is required.
`uvx` installs the pinned release in an isolated environment and downloads Python 3.12
if needed. Preinstall once before connecting your agent (the first download can take minutes):

```sh
uvx --python 3.12 --from git+https://github.com/JosiahSiegel/sourcecrate-mcp.git@v2.1.0 sourcecrate --version
```

Add this entry to your client's MCP server configuration, then restart/reconnect it:

```json
{
  "mcpServers": {
    "sourcecrate": {
      "command": "uvx",
      "args": [
        "--python", "3.12",
        "--from", "git+https://github.com/JosiahSiegel/sourcecrate-mcp.git@v2.1.0",
        "sourcecrate"
      ]
    }
  }
}
```

A ready-to-copy [mcp-config.json](mcp-config.json) is included. Clients with a different
configuration format use the same command and arguments, transport **stdio**.
On Windows use the absolute path to `uvx.exe` if your desktop agent cannot find it
(`where.exe uvx`); on macOS/Linux use `command -v uvx`. Set a startup timeout of at
least 120 seconds where supported, or preinstall using the command above.

For agents that support MCP, start with `get_help`, then `browse_papers` for metadata,
and `download_papers` only when files are wanted. Search results use relevance scores
from 0 to 100. Download and conversion tools write files; supply an explicit output
directory. Remote academic sources may have their own availability or rate limits.

SourceCrate speaks standard MCP over stdin/stdout; diagnostics go to stderr. It does
not expose a remote MCP URL. The optional REST API below is a separate interface.
To upgrade, replace the release tag in the command and configuration, preinstall it,
and restart your agent. For development use `uv run --locked sourcecrate` in a clone.

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

SourceCrate includes an optional HTTP/REST API server for programmatic access!

### HTTP access and file workspace

Set `SOURCECRATE_HTTP_TOKEN` to a randomly generated secret before starting the HTTP server.
API and debug requests require `Authorization: Bearer <token>`.
Health checks, CORS preflight and documentation are public; use **Authorize** in Swagger UI. The default bind address is `127.0.0.1`.

```powershell
$env:SOURCECRATE_HTTP_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:SOURCECRATE_HTTP_ROOT = "$PWD/research-files"
uv sync --locked --extra http --extra dev
uv run --locked sourcecrate-http
```

HTTP conversion and download paths resolve inside `SOURCECRATE_HTTP_ROOT` (default:
`.sourcecrate/http`). Place input PDFs there. Paths escaping it and filesystem links
are rejected. Set `SOURCECRATE_CORS_ORIGINS` to a comma-separated list of allowed
browser origins when needed; by default no cross-origin access is granted.
The website at https://sourcecrate.org is deployed independently through GitHub Pages
from the separate `sourcecrate` repository. It calls academic APIs directly and does
not require this optional REST server.

PDF downloads allow only public HTTP(S) destinations on ports 80/443, revalidate
redirects, pin validated DNS addresses, and stop at 25 MiB. Local MCP stdio tools
remain suitable for trusted local file workflows.

Paper `relevance_score` values use **0–100** in both repositories. SSE clients must
send the bearer header using fetch (native EventSource cannot set it). The final
`results` event has `replace: true`; replace provisional papers with its deduplicated
snapshot. Shared identity/filter fixtures live in `tests/fixtures/paper-contract.json`
in both repositories and should be updated together.

### ✨ Zero-Setup Installation (Recommended)

**Start the HTTP server instantly with uvx - no manual installation required!**

#### Option 1: Direct from GitHub
```bash
uvx --from 'sourcecrate[http] @ git+https://github.com/JosiahSiegel/sourcecrate-mcp.git@v2.1.0' sourcecrate-http
# Server runs on http://localhost:8000
```

#### Option 2: From Cloned Repository
```bash
# 1. Clone the repository
git clone https://github.com/JosiahSiegel/sourcecrate-mcp.git
cd sourcecrate-mcp

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
import os
import requests

response = requests.post('http://localhost:8000/api/v1/search',
    headers={'Authorization': f'Bearer {os.environ["SOURCECRATE_HTTP_TOKEN"]}'},
    json={'query': 'quantum computing', 'limit': 10})
papers = response.json()
```

**JavaScript:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/search', {
  method: 'POST',
  headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
  body: JSON.stringify({query: 'quantum computing', limit: 10})
});
const papers = await response.json();
```

**cURL:**
```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer $SOURCECRATE_HTTP_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"query":"quantum computing","limit":10}'
```

### Use Cases

- **Integration** - Add paper search to your apps
- **Automation** - Programmatic access via REST API
- **Remote access** - Deploy on server, access from anywhere
- **Web applications** - Build custom interfaces with REST API

### Deployment and validation

The website uses GitHub Pages. This repository distributes a local MCP server;
there is no hosted SourceCrate API dependency. Run the optional HTTP server locally
on port 8000 with a bearer token when your application needs REST access.

CI runs locked dependency installation, lint, typing, formatting, and offline tests
on Linux, Windows, and macOS. It builds a wheel, installs it in an isolated environment,
and checks an actual MCP handshake, tool discovery, and `get_help` outside the checkout.
Pushing a `v*` tag reruns these checks, verifies the package version, and publishes
the tested wheel, source archive, and portable MCP configuration to GitHub Releases.

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

- **Command not found:** install uv and Git, then restart the agent so its PATH refreshes.
  Desktop clients can use an absolute path to `uvx`.
- **Slow first startup:** run the `--version` preinstallation command before connecting.
- **Connection closes:** run the exact configured command with `--help` in a terminal
  and inspect stderr. Do not put `--help` or `--version` in the agent configuration.
- **No papers:** use `get_status` to inspect sources; external APIs may be unavailable
  or rate-limited. Try another query. Basic stdio use needs no HTTP bearer token.
- **Upgrade:** use a newer published release tag, preinstall it, and reconnect your agent.

## 🌟 Features

- 🔍 **Multi-Source Search** - 15+ verified legal academic APIs across all disciplines
- 🔧 **Fully Extensible** - Add custom sources via YAML configuration
- 📖 **Unlimited PDF Processing** - No page or character limits
- 🔄 **Zero-Token Conversion** - PDF to markdown without AI usage
- ⚡ **Intelligent Fallback** - Robust multi-source search
- 🗄️ **Smart Caching** - JSON-only SQLite cache with a 1GB payload budget, stored in
  `~/.sourcecrate/cache` (override with `SOURCECRATE_CACHE_DIR`). Legacy shared pickle
  caches are never loaded. Unavailable cache storage does not prevent research.

## 📚 Documentation

- **[HTTP API Reference](docs/HTTP_API.md)** - Complete REST API documentation
- **[Configuration Guide](docs/configuration.md)** - Custom sources and advanced config
- **[Custom Source Guide](docs/CUSTOM_SOURCE_GUIDE.md)** - Add your own academic databases
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
