# Enhanced Scholarly MCP Server - GitHub URL Deployment

> **Zero-installation deployment via GitHub repository URL**

This repository is configured for **instant deployment** from GitHub URL - no local installation required!

## 🚀 Quick Deployment Options

### Option 1: FastMCP Cloud (Recommended)

1. **Visit [FastMCP Cloud](https://fastmcp.cloud)**
2. **Sign in with GitHub**
3. **Create new project from URL**: `https://github.com/your-username/scholarly-mcp.git`
4. **Set entrypoint**: `scholarly_enhanced_server.py:mcp`
5. **Deploy** → Get your server URL instantly!

**Your server will be available at**: `https://your-project.fastmcp.app/mcp`

### Option 2: Claude Desktop Integration

Add this to your `claude_desktop_config.json`:

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

### Option 3: Claude Code Integration

Add this server configuration in Claude Code:

```
/mcp add scholarly-enhanced fastmcp run https://github.com/your-username/scholarly-mcp.git --entrypoint scholarly_enhanced_server.py:mcp
```

Or use the provided `claude_code_config.json` template.

### Option 4: Any MCP Client

Use the FastMCP CLI to run directly from GitHub:

```bash
fastmcp run https://github.com/your-username/scholarly-mcp.git --entrypoint scholarly_enhanced_server.py:mcp
```

## 🎯 What You Get

### 📚 Academic Research Tools
- **Google Scholar Integration** - Search 100M+ academic papers
- **Author Profiles** - Complete researcher information and metrics
- **Institution Search** - Find academic organizations worldwide
- **Citation Analysis** - Track paper impact and references

### 🔓 Full-Text Retrieval (No Local Setup Required!)
- **Multi-Source Detection** - Unpaywall, Semantic Scholar, arXiv, CORE
- **PDF Text Extraction** - Complete paper content from open access sources
- **20M+ Open Access Papers** - Instant access to full research content
- **arXiv Integration** - Direct preprint access and processing

### 🛠️ Advanced Features
- **Rate Limiting** - Production-ready API management
- **Error Handling** - Graceful fallbacks and retries
- **Multiple Formats** - BibTeX, citations, metadata
- **Async Processing** - High-performance concurrent requests

## 📋 Available Tools

### Basic Research
| Tool | Description |
|------|-------------|
| `search_author` | Find researchers by name with citations and h-index |
| `get_author_details` | Complete author profiles with publication lists |
| `search_publications` | Search papers by keywords across all fields |
| `search_organizations` | Find academic institutions and affiliations |

### Enhanced Full-Text Capabilities ⭐
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
```python
# Via any MCP client
await client.call_tool("search_publications", {
    "query": "transformer neural networks",
    "limit": 5
})
```

### Full-Text Retrieval
```python
# Get complete paper content
await client.call_tool("get_full_text_by_title", {
    "title": "Attention Is All You Need",
    "extract_text": True
})
```

### Natural Language with Claude
Simply ask Claude:
- *"Search for recent papers about quantum computing"*
- *"Get the full text of the BERT paper"*
- *"Find information about Geoffrey Hinton's research"*

## 🔧 Configuration (Optional)

### Environment Variables
Set these for enhanced functionality:

```json
{
  "env": {
    "UNPAYWALL_EMAIL": "your_email@example.com",
    "SEMANTIC_SCHOLAR_API_KEY": "your_key_here",
    "CORE_API_KEY": "your_key_here"
  }
}
```

### API Rate Limits
| Service | Free Tier | With API Key |
|---------|-----------|--------------|
| Unpaywall | 100,000/day | Same (no key needed) |
| Semantic Scholar | 1,000/hour | 10,000+/hour |
| CORE | Limited | Full access |
| arXiv | Unlimited | Same |

## 🌟 Why This Approach?

### ✅ Zero Installation
- No Python setup required
- No dependency management
- No local configuration files
- Works on any system with MCP support

### ✅ Always Updated
- Automatic updates from GitHub
- Latest features and bug fixes
- No maintenance required
- Community contributions included

### ✅ Secure & Reliable
- Sandboxed execution
- No local file system access
- Managed dependencies
- Production-ready scaling

### ✅ Universal Compatibility
- Works with Claude Desktop
- Works with Claude Code
- Works with any MCP client
- Works with FastMCP Cloud

## 🎯 Full-Text Coverage

The server automatically finds full text from:
- ✅ **20M+ Unpaywall papers** (institutional repositories, publisher sites)
- ✅ **arXiv preprints** (physics, math, CS, biology, etc.)
- ✅ **PubMed Central** (biomedical literature)
- ✅ **University repositories** (theses, working papers)
- ✅ **Author self-archives** (personal/department websites)

**Coverage**: ~30% of all academic literature has full text available

## 🚦 Performance

- **Metadata queries**: ~1-2 seconds
- **Open access detection**: ~2-3 seconds
- **Full PDF extraction**: ~5-15 seconds
- **Batch processing**: Concurrent execution
- **Rate limiting**: Built-in API management

## 📈 Use Cases

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

## 🆘 Support & Issues

- **Documentation**: This repository's README and guides
- **Issues**: [GitHub Issues](https://github.com/your-username/scholarly-mcp/issues)
- **Community**: FastMCP Discord and forums

---

## 🎉 Ready to Deploy?

**Choose your deployment method:**

### 🌐 Public Deployment (FastMCP Cloud)
1. Fork this repository
2. Deploy to [FastMCP Cloud](https://fastmcp.cloud)
3. Share your server URL with the world!

### 💻 Personal Use (Claude Desktop/Code)
1. Copy the configuration from `claude_desktop_config.json`
2. Update with your email address
3. Add to your Claude configuration
4. Restart Claude and start researching!

**Transform your AI assistant into a powerful academic research tool - deployed in under 2 minutes! 🚀**