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

For enhanced performance, set environment variables:
```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CROSSREF_EMAIL="your_email@example.com"
```

Custom configuration via `.paperez/config/config.yaml`:
```yaml
version: "1.0"
use_default_sources: true
default_category: comprehensive
sources:
  # Add custom sources here
categories:
  # Add custom categories here
```

Use `get_help` tool for complete configuration guidance.

## 🌟 Features

- 🔍 **Multi-Source Search** - CrossRef, Semantic Scholar, arXiv, PubMed, Google Scholar
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

- **CrossRef** - Official API from non-profit organization, encourages research use
- **Semantic Scholar** - Microsoft/Allen Institute official API for academic research
- **arXiv** - Cornell University preprint repository with official API
- **PubMed/PMC** - NIH/NCBI government databases with public APIs
- **Europe PMC** - European biomedical database with official research API
- **DOAJ** - Open access directory specifically promoting programmatic access
- **HathiTrust** - Academic library consortium with official catalog API
- **Internet Archive** - Non-profit digital library with official API
- **SSRN** - Elsevier's official research platform API
- **ClinicalTrials.gov** - US government database with mandated public access

**Compliance measures:**
- ✅ Respects rate limits and terms of service for all sources
- ✅ Only accesses publicly available metadata and open access content
- ✅ Includes proper attribution and email contacts where required
- ✅ No paywalled content accessed without permission
- ✅ Google Scholar disabled by default (no official API)

**User responsibility:** Custom configurations and additional sources are under user control and responsibility.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

---

**Ready to transform academic research with AI? Zero installation required! 🚀**