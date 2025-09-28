# PaperezMCP 📚🚀

> **Academic paper research made easy through the Model Context Protocol (MCP)**

PaperezMCP is a comprehensive MCP server that makes academic research effortless. Get papers from multiple databases, extract full-text content, and convert PDFs to markdown - all with zero-installation via uvx.

[![GitHub](https://img.shields.io/badge/GitHub-JosiahSiegel%2Fpaperz--mcp-blue)](https://github.com/JosiahSiegel/paperez-mcp)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Quick Start for Claude Code

### Install
```bash
claude mcp add -s project paperez-mcp -- uvx --from git+https://github.com/JosiahSiegel/paperez-mcp.git paperez-mcp
```

### Basic Usage
Ask Claude naturally:
- "Download 3 machine learning papers"
- "Convert this PDF to markdown: /path/to/paper.pdf"
- "Help me configure paperez-mcp"

### Available Tools (7 Functions)

| Tool | Description |
|------|-------------|
| **`download_papers`** | 📄 **MAIN TOOL** - Get/download full papers as files |
| **`browse_papers`** | 🔍 Quick metadata overview (titles/abstracts only) |
| **`convert_pdf_to_text`** | Convert PDF to plain text files |
| **`convert_pdf_to_markdown`** | Convert single PDF to markdown |
| **`batch_convert_pdfs`** | Convert entire directories of PDFs |
| **`get_status`** | Check API health and system status |
| **`get_help`** | Configuration guide and examples |

## 🔧 Configuration (Optional)

### Environment Variables (Enhanced Performance)
```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CROSSREF_EMAIL="your_email@example.com"
```

### Custom Configuration Files

PaperezMCP supports **multiple configuration files** organized by research domain. Create any YAML file in `.paperez/config/` directory:

#### Option 1: Single Custom Config
```bash
mkdir -p .paperez/config/
# Create .paperez/config/my_custom.yaml
```

```yaml
# .paperez/config/my_custom.yaml
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
.paperez/config/chemistry.yaml      # Chemistry sources
.paperez/config/engineering.yaml    # Engineering databases
.paperez/config/local_sources.yaml  # Institution-specific APIs
```

All YAML files in `.paperez/config/` are automatically loaded and merged with built-in sources.

Use `get_help` tool for complete configuration schemas and examples.

## 🌟 Features

- 🔍 **Multi-Source Search** - CrossRef, Semantic Scholar, arXiv, PubMed, Google Scholar
- 🔧 **Fully Extensible** - Add custom sources via YAML configuration
- 📖 **Unlimited PDF Processing** - No page or character limits
- 🔄 **Zero-Token Conversion** - PDF to markdown without AI usage
- ⚡ **Intelligent Fallback** - Robust multi-source search
- 🗄️ **Smart Caching** - 1GB disk cache for performance

## 📚 Documentation

- [Installation Guide](docs/installation.md) - Detailed setup instructions
- [Configuration Guide](docs/configuration.md) - Advanced configuration options
- [API Reference](docs/api-reference.md) - Complete tool documentation
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions
- [Examples](docs/examples.md) - Usage examples and workflows

## ⚖️ Legal & Ethical Usage

**All default sources use legitimate public APIs designed for academic research:**

### Scientific & General Sources
- **CrossRef** - Official API from non-profit organization, requires email contact (configured)
- **Semantic Scholar** - Microsoft/Allen Institute official API, 1 RPS rate limit respected
- **arXiv** - Cornell University preprint repository, 1 request per 3 seconds
- **DOAJ** - Directory of Open Access Journals, 2 requests/second limit respected

### Medical & Biomedical Sources
- **PubMed/PMC** - NIH/NCBI government databases, 3 RPS default rate limit
- **Europe PMC** - European biomedical database, ~10 requests/time period limit
- **ClinicalTrials.gov** - US government database, ~50 requests/minute, public domain

### Specialized Domain Sources
- **Internet Archive** - Non-profit digital library, ~1 RPS for non-commercial use
- **Open Library** - Internet Archive's book database, humanities focus
- **CORE Repository** - Open access research aggregator, demo API key
- **Federal Register** - US government regulations database, public domain
- **CourtListener** - Free Legal opinions database, 5 requests/second

### Disabled Sources (Compliance Issues)
- **HathiTrust** - Disabled: No keyword search API available, only item lookup
- **Google Scholar** - Disabled: No official API, potential ToS violations
- **SSRN** - Disabled: ToS reserves data mining rights, restricted access

**Compliance measures:**
- ✅ **Strict rate limiting** per each source's ToS requirements (0.1s to 3s delays)
- ✅ **Email contact** information included where required (CrossRef)
- ✅ **Small-scale queries** only, no bulk data harvesting or scraping
- ✅ **Non-commercial academic research** use only
- ✅ **Proper attribution** included in documentation and citations
- ✅ **Public domain/open data** preference for government sources
- ✅ **Legitimate API endpoints** only, no web scraping
- ✅ **User-agent identification** as academic research tool

**User responsibility for custom sources:**
- Verify Terms of Service compliance before adding custom sources
- Respect rate limits and usage restrictions of institutional APIs
- Ensure proper authorization for private/subscription databases
- Custom configurations are under user control and responsibility
- Users must comply with their institution's data usage policies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

---

## Ready to Get Started?

**Transform academic research with AI! Zero installation required! 🚀**