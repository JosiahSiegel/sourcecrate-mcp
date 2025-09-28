# PaperezMCP 📚🚀

> **Academic paper research made easy through the Model Context Protocol (MCP)**

PaperezMCP is a comprehensive MCP server that makes academic research effortless. Get papers from multiple databases, extract full-text content, and convert PDFs to markdown - all with zero-installation via uvx.

[![GitHub](https://img.shields.io/badge/GitHub-JosiahSiegel%2Fpaperz--mcp-blue)](https://github.com/JosiahSiegel/paperez-mcp)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### Core Capabilities

- 🔍 **Multi-Source Academic Search** - CrossRef, Semantic Scholar, arXiv, PubMed, Google Scholar
- 📖 **Unlimited PDF Text Extraction** - No page or character limits, full papers processed
- 🔄 **Zero-Token Markdown Conversion** - PDF to structured markdown using pymupdf4llm
- 📄 **Advanced PDF Processing** - Handles complex layouts, formulas, and references
- ⚡ **Intelligent API Fallback** - Robust multi-source search with graceful error handling
- 🎯 **MCP Protocol Native** - Direct integration with AI assistants
- 🗄️ **Smart Caching System** - 1GB disk cache for improved performance

### Advanced Features

- 🧠 **Comprehensive Search Engine** - Queries multiple academic databases simultaneously
- 📚 **Complete Paper Archives** - Local PDF and markdown storage capabilities
- 🌍 **Open Access Detection** - Automatically finds free versions across sources
- 📊 **Citation Analysis** - Comprehensive bibliometric data from multiple APIs
- 🏗️ **Modular Architecture** - Clean, maintainable codebase with focused components
- 🔧 **Development Tools** - Built-in batch processing and file utilities

## 🚀 Zero-Installation Deployment

### For Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "paperez-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JosiahSiegel/scholarly-mcp.git",
        "scholarly-mcp"
      ],
      "env": {
        "UNPAYWALL_EMAIL": "your_email@example.com"
      }
    }
  }
}
```

### For Claude Code

Run this command in Claude Code:

```bash
claude mcp add -s project paperez-mcp -- uvx --from git+https://github.com/JosiahSiegel/paperez-mcp.git paperez-mcp
```

or

```bash
/mcp add paperez-mcp uvx --from git+https://github.com/JosiahSiegel/paperez-mcp.git paperez-mcp
```

## 📋 Available Tools (7 Optimized Functions)

### 🔍 Search & Discovery

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| **`download_papers`** | 📄 **MAIN TOOL** - Get/download full papers as files | `limit=5` papers<br/>`output_dir` for custom location |
| **`browse_papers`** | 🔍 Quick metadata overview (titles/abstracts only) | Use for exploration before downloading |

### 📄 PDF Processing

| Tool | Description | Use Case |
|------|-------------|----------|
| **`convert_pdf_to_text`** | Convert PDF to plain text files (unlimited characters) | Text analysis, content extraction |
| **`convert_pdf_to_markdown`** | Convert single PDF to markdown (zero tokens) | Document conversion, structure preservation |
| **`batch_convert_pdfs`** | Convert entire directories of PDFs to markdown | Bulk processing, research archives |

### 🔧 System

| Tool | Description | Purpose |
|------|-------------|---------|
| **`get_status`** | Check API health, performance metrics, and system status | Troubleshooting, monitoring |
| **`get_help`** | Configuration guide with paths, schemas, and examples | Setup, customization |

## 🎯 Getting Papers: Browse vs Download

### 🔍 Browse Papers (Metadata Only)
```python
# Quick overview of available papers - returns titles/abstracts only
browse_papers("machine learning transformers", limit=10)
```

### 📄 Download Papers (Full Papers as Files)
```python
# Get full papers as markdown files - this is what most users want
download_papers("machine learning transformers", limit=5)

# Save to specific directory
download_papers("neural networks", limit=3, output_dir="my_research")

# Keep as PDFs instead of converting to markdown
download_papers("AI papers", limit=2, convert_to_markdown=False)
```

### 🎯 Quick Solutions by Use Case

| Request | Solution |
|---------|----------|
| "Get papers on topic" | `download_papers("topic", limit=5)` → **full papers as files** |
| "Browse papers first" | `browse_papers("topic", limit=10)` → **metadata only** |
| "Save to specific folder" | `download_papers("topic", output_dir="my_folder")` |
| "Get configuration help" | `get_help()` → **setup guidance** |


## 💡 Usage Examples

### Basic Usage

```bash
# Download papers as files (most common use case)
/mcp call paperez-mcp download_papers '{"query": "machine learning", "limit": 3}'

# Browse papers (metadata only)
/mcp call paperez-mcp browse_papers '{"query": "Geoffrey Hinton", "limit": 5}'

# Get configuration help
/mcp call paperez-mcp get_help '{}'
```

### Full-Text Retrieval & Processing

```bash
# Download full papers as files
/mcp call paperez-mcp download_papers '{"query": "transformer attention mechanism", "limit": 3}'

# Browse papers first, then download selected ones
/mcp call paperez-mcp browse_papers '{"query": "Attention Is All You Need", "limit": 5}'

# Convert PDF to markdown (zero AI tokens)
/mcp call paperez-mcp convert_pdf_to_markdown '{"file_path": "/path/to/paper.pdf"}'

# Convert PDF to plain text
/mcp call paperez-mcp convert_pdf_to_text '{"file_path": "/path/to/paper.pdf"}'

# Batch convert multiple PDFs
/mcp call paperez-mcp batch_convert_pdfs '{"directory": "research_papers/"}'
```

### Natural Language with AI

Simply ask your AI assistant:

- _"Search for recent papers about quantum computing across all databases"_
- _"Get the complete full text of the BERT paper and convert it to markdown"_
- _"Download and process the Vision Transformer paper with unlimited text extraction"_
- _"Find all open access versions of papers about neural networks"_
- _"Convert all PDFs in my research folder to structured markdown"_

## 🔧 Configuration (Optional)

### Environment Variables

Set these for enhanced functionality:

```bash
# Optional: Enhanced API access
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export SCRAPERAPI_KEY="your_key_here"          # For Google Scholar access
export CROSSREF_EMAIL="your_email@example.com"  # For CrossRef polite pool

# Configuration
export MAX_RETRIES=3
export BASE_DELAY=1.0
```

### API Rate Limits & Sources

| Service              | Free Tier           | Enhanced Access        | Notes                          |
| -------------------- | ------------------- | ---------------------- | ------------------------------ |
| **CrossRef**         | No explicit limits  | Same                   | Primary source, most reliable  |
| **Semantic Scholar** | 1,000 requests/hour | 10,000+ with API key   | 225M+ papers                   |
| **arXiv**            | No explicit limits  | Same                   | Preprints and technical papers |
| **PubMed**           | No explicit limits  | Same                   | Biomedical literature          |
| **Google Scholar**   | Rate limited        | Stable with ScraperAPI | Fallback source                |

## 📚 Multi-Source Academic Coverage

The server provides comprehensive access through:

### Search Sources (Automatic Fallback)

- 🥇 **CrossRef** - Primary source, 130M+ DOIs, most reliable
- 🧠 **Semantic Scholar** - 225M+ papers with AI-powered insights
- 📚 **arXiv** - Physics, math, CS, and technical preprints
- 🏥 **PubMed** - Comprehensive biomedical literature
- 🔍 **Google Scholar** - Broadest coverage, fallback source

### Full-Text Processing

- 📄 **Unlimited PDF Extraction** - No page or character limits
- 🔄 **Zero-Token Markdown** - Direct conversion without AI usage
- 🎯 **Smart Content Detection** - Handles formulas, tables, references
- 💾 **Local Storage** - Download and archive papers permanently

## 🚦 Performance & Capabilities

### Performance Characteristics

- **Multi-source search**: ~1-3 seconds (with intelligent fallback)
- **Unlimited PDF extraction**: ~5-30 seconds (depending on paper size)
- **Zero-token markdown conversion**: ~2-10 seconds per paper
- **Batch processing**: Concurrent operations supported
- **Smart caching**: 1GB cache improves repeat queries dramatically

### Technical Capabilities

- ✅ **No character limits** - Complete papers extracted (100k+ characters)
- ✅ **No page limits** - All pages processed automatically
- ✅ **Robust error handling** - Graceful fallback across 5 API sources
- ✅ **Modular architecture** - Maintainable, extensible codebase
- ✅ **Zero-token processing** - PDF conversion without AI context usage

### Current Limitations

- Full text requires **publicly accessible PDFs** (open access, arXiv, etc.)
- **Complex mathematical notation** converted to text symbols
- **Rate limits** apply to external APIs (handled automatically)
- **Network dependent** - Requires internet for API access

## 💡 Why uvx Deployment?

### ✅ True Zero Installation

- No Python setup required
- No dependency management
- No local configuration files
- Works instantly on any system with uvx

### ✅ Always Updated

- Automatic updates from GitHub
- Latest features and bug fixes
- No maintenance required
- Community contributions included

### ✅ Universal Compatibility

- Works with Claude Desktop
- Works with Claude Code
- Works with any MCP client
- Automatic dependency resolution

## 🎯 Use Cases

### 🎓 Academic Research

- Literature reviews and meta-analyses
- Citation analysis and impact tracking
- Author collaboration networks
- Research trend analysis

### 🤖 AI-Assisted Research

- Automated paper summarization
- Research question generation
- Hypothesis development
- Knowledge synthesis

### 📊 Data Science Projects

- Academic dataset creation
- Research metrics analysis
- Publication trend forecasting
- Scientific impact modeling

## 🔒 Privacy & Ethics

- **No API keys stored** - User-provided credentials only
- **Respects publisher policies** - Only accesses legally available content
- **Rate limiting** - Responsible API usage
- **Open access focus** - Promotes accessible research

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### 1. "No Results Found" from Search

**Problem**: Query not finding papers across databases.
**Solutions**:

- **Use comprehensive_search**: Automatically tries all 5 sources with fallback
- **Specific queries**: Use exact titles, author names, or DOIs when possible
- **Check API status**: Use `get_api_status` to see which sources are available
- **Biomedical papers**: Server automatically includes PubMed for medical terms

#### 2. HTTP 429 (Rate Limited) Errors

**Problem**: Hitting API rate limits.
**Solutions**:

- **Automatic handling**: Server implements exponential backoff and retry logic
- **API keys**: Set SEMANTIC_SCHOLAR_API_KEY for higher Semantic Scholar limits
- **Multi-source fallback**: Rate limits on one source trigger automatic fallback
- **Smart caching**: Repeat queries served from 1GB local cache

#### 3. PDF Extraction Issues

**Problem**: Cannot extract text from PDF URLs.
**Solutions**:

- **Use find_open_access_versions**: Automatically finds alternative PDF sources
- **Check accessibility**: Some PDFs may be behind paywalls or access restrictions
- **Local processing**: Download PDF first, then use `extract_pdf_text_from_local_file`
- **Batch processing**: Use `batch_convert_local_pdfs` for multiple files

#### 4. MCP Server Not Detected

**Problem**: Configuration or path issues.
**Solutions**:

1. Verify `.mcp.json` syntax and location
2. Restart Claude Code/Desktop after changes
3. Use absolute uvx path if needed:
   ```json
   "command": "/home/node/.local/bin/uvx"
   ```

#### 5. Large PDF Processing

**Problem**: Very large PDFs taking too long or failing.
**Solutions**:

- **Unlimited processing**: Server handles papers of any size (no character/page limits)
- **Zero-token conversion**: Use `download_and_convert_paper` for efficient processing
- **Local storage**: Download first, process locally to avoid network timeouts
- **Batch operations**: Use `batch_convert_local_pdfs` for multiple large files

### Best Practices

1. **Multi-Source Strategy**: Use `comprehensive_search` for maximum coverage across databases
2. **Specific Queries**: DOIs and exact titles work better than broad keyword searches
3. **API Configuration**: Set SEMANTIC_SCHOLAR_API_KEY and CROSSREF_EMAIL for optimal performance
4. **Caching Leverage**: Repeated queries benefit from 1GB smart cache system
5. **Processing Pipeline**: Search → find open access → extract/convert → store locally

### Performance Tips

- **comprehensive_search** provides best results with automatic fallback
- **Zero-token conversion** saves AI context for large document processing
- **Biomedical queries** automatically include PubMed for better coverage
- **Local processing** is faster and more reliable than repeated URL extraction
- **Batch operations** handle multiple papers efficiently

## 🆘 Support

- **Documentation**: This README
- **Troubleshooting**: See guide above
- **Issues**: [GitHub Issues](https://github.com/JosiahSiegel/scholarly-mcp/issues)
- **Repository**: [GitHub](https://github.com/JosiahSiegel/scholarly-mcp)

## 🙏 Acknowledgments

Built with:

- [FastMCP](https://fastmcp.cloud) - MCP framework
- [scholarly](https://github.com/scholarly-python-package/scholarly) - Google Scholar API
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [Unpaywall](https://unpaywall.org/) - Open access detection
- [Semantic Scholar](https://www.semanticscholar.org/) - Academic search API

---

**Ready to transform academic research with AI? Zero installation required! 🚀**

[![Deploy Now](https://img.shields.io/badge/Deploy%20Now-Zero%20Installation-blue?style=for-the-badge)](https://github.com/JosiahSiegel/scholarly-mcp)
