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

- 🔍 **Multi-Source Search** - 15+ verified legal academic APIs across all disciplines
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

**📋 [Complete Terms of Service](TERMS_OF_SERVICE.md) - Full legal compliance details and user obligations**

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
- ✅ **Email contact** configured where required (CrossRef: <research@paperez.org>)
- ✅ **Academic research use only** - all sources designed for scholarly access
- ✅ **Attribution requirements** met with proper source citation
- ✅ **Government databases** prioritized for public domain content
- ✅ **Official APIs only** - no web scraping or unofficial endpoints
- ✅ **Proactive compliance monitoring** - sources disabled if ToS change

**Legal Disclaimer - Custom Source Liability:**
- PaperezMCP provides legal compliance only for default configuration sources
- Users who modify configurations assume full legal responsibility for compliance
- Custom source additions are solely under user control and legal liability
- Users must independently verify Terms of Service compliance for any modifications
- PaperezMCP disclaims all responsibility for user-configured sources outside defaults
- Institutional and legal compliance for custom sources is the user's sole responsibility

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License & Terms

- **Software License:** MIT License - see the [LICENSE](LICENSE) file for details
- **Terms of Service:** [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md) - Legal compliance and usage terms

---

## Ready to Get Started?

**Transform academic research with AI! Zero installation required! 🚀**