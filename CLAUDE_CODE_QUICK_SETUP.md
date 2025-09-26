# Claude Code MCP Server Setup - Quick Guide

## 🚀 Quick Setup for Claude Code

### Step 1: Install Dependencies

```bash
# In the scholarly-mcp directory
pip install -r requirements_enhanced.txt
```

### Step 2: Add MCP Server to Claude Code

Use Claude Code's built-in MCP configuration. Run this command in Claude Code:

```
/mcp add scholarly-enhanced python3 scholarly_enhanced_server.py --cwd /mnt/d/repos/scholarly-mcp
```

**Or manually add to your Claude Code MCP settings:**

**Server Name**: `scholarly-enhanced`
**Command**: `python3`
**Arguments**: `["scholarly_enhanced_server.py"]`
**Working Directory**: `/mnt/d/repos/scholarly-mcp`

### Step 3: Verify Installation

After adding the server, check if it's working:

```
/mcp list
```

You should see `scholarly-enhanced` listed.

### Step 4: Test the Server

Try a simple test:

```
/mcp call scholarly-enhanced search_author '{"name": "Geoffrey Hinton", "limit": 1}'
```

## 🎯 Available Tools

Once configured, you can use these MCP tools:

### Basic Research Tools
- `search_author` - Find researchers by name
- `search_publications` - Search papers by keywords
- `get_author_details` - Get detailed author profiles
- `search_organizations` - Find academic institutions

### Advanced Full-Text Tools ⭐
- `get_full_text_by_doi` - **Get complete paper text using DOI**
- `get_full_text_by_title` - **Get complete paper text using title**
- `find_open_access_versions` - **Find open access versions across multiple sources**
- `search_with_full_text` - **Search papers with optional full-text extraction**
- `extract_pdf_text_from_url` - **Extract text from any PDF URL**

### Citation Tools
- `get_bibtex_citation` - Generate BibTeX citations

## 💡 How to Use in Claude Code

### Natural Language Usage

You can simply ask Claude to use these tools naturally:

**"Search for papers about transformer neural networks"**
→ Uses `search_publications` tool

**"Find information about researcher Yann LeCun"**
→ Uses `search_author` and `get_author_details` tools

**"Get the full text of the paper 'Attention Is All You Need'"**
→ Uses `get_full_text_by_title` with PDF extraction

**"Find open access versions of papers about quantum computing"**
→ Uses `find_open_access_versions` and `search_publications`

### Direct Tool Calls

For specific tool calls:

```bash
# Search for an author
/mcp call scholarly-enhanced search_author '{"name": "Geoffrey Hinton", "limit": 2}'

# Search for papers
/mcp call scholarly-enhanced search_publications '{"query": "machine learning", "limit": 3}'

# Get full text of a paper (open access only)
/mcp call scholarly-enhanced get_full_text_by_title '{"title": "Attention Is All You Need", "extract_text": true}'

# Find open access versions
/mcp call scholarly-enhanced find_open_access_versions '{"title": "BERT: Pre-training of Deep Bidirectional Transformers"}'
```

## 🔧 Environment Variables (Optional)

For enhanced functionality, set these environment variables:

```bash
# For higher API rate limits (optional)
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CORE_API_KEY="your_key_here"

# Required for Unpaywall API
export UNPAYWALL_EMAIL="your_email@example.com"

# PDF processing settings
export MAX_PDF_SIZE_MB="50"
export PDF_TIMEOUT="60"
```

## ⚡ Quick Test Commands

After setup, test with these commands in Claude Code:

```bash
# Test 1: Basic author search
/mcp call scholarly-enhanced search_author '{"name": "Yoshua Bengio", "limit": 1}'

# Test 2: Paper search
/mcp call scholarly-enhanced search_publications '{"query": "deep learning", "limit": 2}'

# Test 3: Full text retrieval (arXiv paper - should work)
/mcp call scholarly-enhanced get_full_text_by_doi '{"doi": "10.48550/arXiv.1706.03762", "extract_text": true}'

# Test 4: Open access detection
/mcp call scholarly-enhanced find_open_access_versions '{"title": "Attention Is All You Need"}'
```

## 🛠️ Troubleshooting

### "Server not found" error
- Check that the working directory path is correct: `/mnt/d/repos/scholarly-mcp`
- Ensure dependencies are installed: `pip install -r requirements_enhanced.txt`
- Verify `python3` is available in your PATH

### "Import error" when calling tools
- Make sure all dependencies are installed
- Check that the server file `scholarly_enhanced_server.py` exists in the working directory

### "No full text found"
- Not all papers are open access (~30% coverage)
- The tool will return open access URLs when available
- arXiv papers (like `10.48550/arXiv.xxxx`) usually have full text available

### Rate limits
- The server has built-in rate limiting
- For higher limits, get API keys for Semantic Scholar and CORE

## 🎉 What You Can Do

With this MCP server, Claude Code becomes a powerful academic research assistant:

- **📚 Literature Reviews**: Search and analyze papers on any topic
- **👨‍🔬 Author Analysis**: Track researchers and their work
- **📄 Full-Text Analysis**: Get complete text of open access papers
- **📊 Citation Analysis**: Generate proper citations and bibliographies
- **🔍 Discovery**: Find related papers and open access versions
- **📈 Research Trends**: Analyze publication patterns and impacts

The Enhanced Scholarly MCP Server gives you access to millions of academic papers directly through Claude Code!