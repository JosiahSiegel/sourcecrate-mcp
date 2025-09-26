# Enhanced Scholarly MCP Server 🚀

> **Full-text academic paper retrieval through the Model Context Protocol (MCP)**

A comprehensive MCP server that combines Google Scholar search capabilities with advanced full-text retrieval from multiple open access sources. Built with FastMCP for seamless AI integration.

[![FastMCP](https://img.shields.io/badge/FastMCP-Compatible-blue)](https://fastmcp.cloud)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### Core Capabilities
- 🔍 **Google Scholar Integration** - Search authors, papers, and organizations
- 📖 **Full-Text Retrieval** - Extract complete text from open access papers
- 🔓 **Multi-Source Open Access Detection** - Unpaywall, Semantic Scholar, arXiv, CORE
- 📄 **Intelligent PDF Processing** - PyMuPDF-based text extraction
- ⚡ **Rate Limiting & Error Handling** - Production-ready reliability
- 🎯 **MCP Protocol Native** - Direct integration with AI assistants

### Advanced Features
- 🧠 **Semantic Scholar API** - Access to 225M+ academic papers
- 📚 **arXiv Integration** - Direct preprint access and processing
- 🌍 **Unpaywall Database** - 20M+ open access paper detection
- 📊 **Citation Analysis** - Comprehensive bibliometric data
- 🏷️ **BibTeX Generation** - Automatic citation formatting

## 🚀 Quick Start

### 1. Deploy from GitHub URL (Zero Installation!)

**For Claude Desktop** - Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "scholarly-enhanced": {
      "command": "fastmcp",
      "args": [
        "run",
        "https://github.com/your-username/scholarly-mcp.git",
        "--entrypoint",
        "scholarly_enhanced_server.py:mcp"
      ],
      "env": {
        "UNPAYWALL_EMAIL": "your_email@example.com"
      }
    }
  }
}
```

**For Claude Code** - Add this server:
```bash
/mcp add scholarly-enhanced fastmcp run https://github.com/your-username/scholarly-mcp.git --entrypoint scholarly_enhanced_server.py:mcp
```

### 2. Deploy to FastMCP Cloud

1. **Visit [FastMCP Cloud](https://fastmcp.cloud)** and sign in
2. **Create new project** from URL: `https://github.com/your-username/scholarly-mcp.git`
3. **Set entrypoint**: `scholarly_enhanced_server.py:mcp`
4. **Deploy** and get your server URL

### 3. Local Development

See `DEV_SETUP.md` for local development configuration.

```bash
# Quick local test
python3 local_test_client.py

# Run examples
python3 examples/basic_usage.py
```

## 💡 Why GitHub URL Deployment?

### ✅ Zero Installation
- No Python setup required
- No dependency management
- No local configuration files
- Works instantly on any system

### ✅ Always Updated
- Automatic updates from GitHub
- Latest features and bug fixes
- No maintenance required
- Community contributions included

### ✅ Universal Compatibility
- Works with Claude Desktop
- Works with Claude Code
- Works with any MCP client
- Works with FastMCP Cloud

## 📋 Available Tools

### Basic Search & Metadata
| Tool | Description |
|------|-------------|
| `search_author` | Search authors by name |
| `get_author_details` | Detailed author profiles with h-index, publications |
| `search_publications` | Search papers by keywords/title |
| `search_organizations` | Find academic institutions |
| `get_bibtex_citation` | Generate BibTeX citations |

### Enhanced Full-Text Tools
| Tool | Description |
|------|-------------|
| `get_full_text_by_doi` | **Retrieve full paper text using DOI** |
| `get_full_text_by_title` | **Retrieve full paper text using title** |
| `find_open_access_versions` | **Find open access URLs across multiple sources** |
| `search_with_full_text` | **Search papers with optional full-text extraction** |
| `extract_pdf_text_from_url` | **Extract text from any PDF URL** |

## 💡 Usage Examples

### Basic Paper Search
```python
from fastmcp import Client

async with Client("your-server-url/mcp") as client:
    # Search for papers
    papers = await client.call_tool("search_publications", {
        "query": "machine learning transformers",
        "limit": 5
    })
```

### Full-Text Retrieval
```python
# Get complete paper text by DOI
full_text = await client.call_tool("get_full_text_by_doi", {
    "doi": "10.48550/arXiv.1706.03762",  # "Attention Is All You Need"
    "extract_text": True
})

if full_text.data["full_text"]:
    print(f"📄 Retrieved from: {full_text.data['source']}")
    print(f"📊 Pages: {full_text.data['num_pages']}")
    print(f"📝 Text: {full_text.data['full_text'][:500]}...")
```

### Enhanced Search with Full-Text
```python
# Search papers and get full text when available
papers = await client.call_tool("search_with_full_text", {
    "query": "neural attention mechanisms",
    "limit": 3,
    "extract_text": True
})

for paper in papers.data:
    print(f"Title: {paper['title']}")
    if paper.get('full_text'):
        print(f"✅ Full text available from {paper['full_text_source']}")
    else:
        print(f"📄 Metadata only")
```

## 🔧 Configuration

### Environment Variables
```bash
# API Keys (optional, for higher rate limits)
export SEMANTIC_SCHOLAR_API_KEY="your_key"
export CORE_API_KEY="your_key"

# Required for Unpaywall API
export UNPAYWALL_EMAIL="your_email@example.com"

# PDF Processing
export MAX_PDF_SIZE_MB="50"
export PDF_TIMEOUT="60"

# Proxy Configuration (optional)
export PROXY_TYPE="none"  # none, free, scraperapi, luminati
```

### Rate Limits & API Access

| Service | Free Tier | With API Key |
|---------|-----------|--------------|
| **Unpaywall** | 100,000 calls/day | Same (no key needed) |
| **Semantic Scholar** | 1,000 requests/hour | 10,000+ requests/hour |
| **CORE** | Limited access | Full access (registration required) |
| **arXiv** | No explicit limits | Same |

## 📚 Full-Text Sources

The server automatically checks multiple sources for open access content:

- ✅ **arXiv** - Physics, math, CS, and other preprints
- ✅ **PubMed Central** - Biomedical literature
- ✅ **Institutional Repositories** - University-hosted papers
- ✅ **Publisher Open Access** - Journal-hosted open access
- ✅ **Author Self-Archives** - Personal/departmental websites

## 🛠️ Development

### Project Structure
```
scholarly-mcp/
├── scholarly_enhanced_server.py    # Main server with full-text capabilities
├── enhanced_config.py              # Configuration management
├── requirements_enhanced.txt       # Full dependencies
├── fastmcp.yaml                    # Deployment configuration
├── .mcp.json                       # MCP project configuration
├── test_local.py                   # Local testing suite
├── local_test_client.py            # MCP integration testing
├── deploy.sh                       # Automated deployment script
├── examples/
│   ├── client_example.py           # Comprehensive usage examples
│   └── basic_usage.py              # Simple examples
├── SETUP_GUIDE.md                 # Detailed setup instructions
└── README.md                      # This file
```

### Testing
```bash
# Test MCP configuration
python3 local_test_client.py

# Run comprehensive local tests
python3 test_local.py

# Test specific functionality
python3 examples/basic_usage.py

# Run with FastMCP CLI
fastmcp run scholarly_enhanced_server.py:mcp
```

## 🚦 Performance & Limitations

### Performance Characteristics
- **Metadata queries**: ~1-2 seconds
- **Open access detection**: ~2-3 seconds
- **Full PDF text extraction**: ~5-15 seconds (depending on size)
- **Batch processing**: Concurrent requests supported

### Current Limitations
- Full text only available for **open access papers** (~30% of literature)
- PDF extraction may fail on **complex layouts** (returns URLs as fallback)
- **Rate limits** apply to external APIs
- **Mathematical formulas** extracted as text symbols

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

## 🆘 Support

### Common Issues

**"No full text found"**
- Not all papers are open access (~30% coverage)
- Check `open_access_sources` for available URLs

**"API rate limit exceeded"**
- Wait a few minutes or get API keys for higher limits
- Semantic Scholar: [Register here](https://www.semanticscholar.org/product/api)

**"PDF extraction failed"**
- Some PDFs have complex layouts
- Server returns open access URLs as fallback

### Getting Help

- 📖 **Documentation**: See `SETUP_GUIDE.md` for detailed instructions
- 💬 **Issues**: [GitHub Issues](https://github.com/your-username/scholarly-mcp/issues)
- 📧 **Email**: Support via repository issues

## 🙏 Acknowledgments

Built with:
- [FastMCP](https://fastmcp.cloud) - MCP framework
- [scholarly](https://github.com/scholarly-python-package/scholarly) - Google Scholar API
- [PyMuPDF](https://pymupdf.readthedocs.io/) - PDF processing
- [Unpaywall](https://unpaywall.org/) - Open access detection
- [Semantic Scholar](https://www.semanticscholar.org/) - Academic search API

---

**Ready to transform academic research with AI? Deploy your server now! 🚀**

[![Deploy to FastMCP](https://img.shields.io/badge/Deploy%20to-FastMCP%20Cloud-blue?style=for-the-badge)](https://fastmcp.cloud)