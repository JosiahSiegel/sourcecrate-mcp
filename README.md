# Enhanced Scholarly MCP Server 🚀

> **Full-text academic paper retrieval through the Model Context Protocol (MCP)**

A comprehensive MCP server that combines Google Scholar search capabilities with advanced full-text retrieval from multiple open access sources. **True zero-installation deployment** via uvx.

[![GitHub](https://img.shields.io/badge/GitHub-JosiahSiegel%2Fscholarly--mcp-blue)](https://github.com/JosiahSiegel/scholarly-mcp)
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

## 🚀 Zero-Installation Deployment

### For Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "scholarly-enhanced": {
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
/mcp add scholarly-enhanced uvx --from git+https://github.com/JosiahSiegel/scholarly-mcp.git scholarly-mcp
```

## 📋 Available Tools

### Basic Research Tools
| Tool | Description |
|------|-------------|
| `search_author` | Find researchers by name with citations and h-index |
| `get_author_details` | Complete author profiles with publication lists |
| `search_publications` | Search papers by keywords across all fields |
| `search_organizations` | Find academic institutions and affiliations |

### Enhanced Full-Text Tools ⭐
| Tool | Description |
|------|-------------|
| `get_full_text_by_doi` | **Extract complete paper text using DOI** |
| `get_full_text_by_title` | **Extract complete paper text using title** |
| `find_open_access_versions` | **Find free versions across multiple sources** |
| `search_with_full_text` | **Search + full-text extraction in one call** |
| `extract_pdf_text_from_url` | **Extract text from any PDF URL** |

### Citation & Bibliography
| Tool | Description |
|------|-------------|
| `get_bibtex_citation` | Generate properly formatted BibTeX citations |

## 💡 Usage Examples

### Basic Usage
```bash
# Search for papers
/mcp call scholarly-enhanced search_publications '{"query": "machine learning", "limit": 3}'

# Find an author
/mcp call scholarly-enhanced search_author '{"name": "Geoffrey Hinton", "limit": 1}'
```

### Full-Text Retrieval
```bash
# Get complete paper text by title
/mcp call scholarly-enhanced get_full_text_by_title '{"title": "Attention Is All You Need", "extract_text": true}'

# Extract text from a PDF URL
/mcp call scholarly-enhanced extract_pdf_text_from_url '{"pdf_url": "https://arxiv.org/pdf/1706.03762.pdf"}'
```

### Natural Language with AI
Simply ask your AI assistant:
- *"Search for recent papers about quantum computing"*
- *"Get the full text of the BERT paper"*
- *"Find information about Yann LeCun's research"*

## 🔧 Configuration (Optional)

### Environment Variables
Set these for enhanced functionality:

```bash
# Required for Unpaywall API
export UNPAYWALL_EMAIL="your_email@example.com"

# Optional: API keys for higher rate limits
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CORE_API_KEY="your_key_here"
```

### API Rate Limits
| Service | Free Tier | With API Key |
|---------|-----------|--------------|
| **Unpaywall** | 100,000 calls/day | Same (no key needed) |
| **Semantic Scholar** | 1,000 requests/hour | 10,000+ requests/hour |
| **CORE** | Limited access | Full access (registration required) |
| **arXiv** | No explicit limits | Same |

## 📚 Full-Text Sources

The server automatically finds full text from:
- ✅ **arXiv** - Physics, math, CS, and other preprints
- ✅ **PubMed Central** - Biomedical literature
- ✅ **Institutional Repositories** - University-hosted papers
- ✅ **Publisher Open Access** - Journal-hosted open access
- ✅ **Author Self-Archives** - Personal/departmental websites

**Coverage**: ~30% of all academic literature has full text available

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

## 🆘 Support

- **Documentation**: This README
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
