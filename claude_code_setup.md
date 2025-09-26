# Claude Code MCP Server Setup

This guide helps you configure the Enhanced Scholarly MCP Server to work with Claude Code.

## Quick Setup

### 1. Install Dependencies (if not already done)

```bash
# In the scholarly-mcp directory
pip install -r requirements_enhanced.txt
```

### 2. Configure MCP Server in Claude Code

You have several options to configure the MCP server:

#### Option A: Using Claude Code Settings (Recommended)

1. Open Claude Code
2. Run the command: `/mcp add`
3. When prompted, use these settings:
   - **Server Name**: `scholarly-enhanced`
   - **Command**: `python3`
   - **Arguments**: `["scholarly_enhanced_server.py"]`
   - **Working Directory**: `/mnt/d/repos/scholarly-mcp`

#### Option B: Manual Configuration File

Create or edit the Claude Code MCP configuration file:

**Location**: `~/.config/claude-code/mcp_servers.json` (Linux/Mac) or `%APPDATA%\claude-code\mcp_servers.json` (Windows)

```json
{
  "scholarly-enhanced": {
    "command": "python3",
    "args": ["scholarly_enhanced_server.py"],
    "cwd": "/mnt/d/repos/scholarly-mcp",
    "env": {
      "UNPAYWALL_EMAIL": "research@example.com",
      "MAX_PDF_SIZE_MB": "50",
      "PDF_TIMEOUT": "60",
      "PROXY_TYPE": "none"
    }
  }
}
```

#### Option C: Using Project-level MCP Configuration

If Claude Code supports project-level `.mcp.json` files, it should automatically detect the configuration in this directory.

### 3. Verify Installation

After configuration, restart Claude Code and check:

```
/mcp list
```

You should see `scholarly-enhanced` in the list of available servers.

### 4. Test the Server

Try these commands in Claude Code:

```
/mcp call scholarly-enhanced search_author '{"name": "Geoffrey Hinton", "limit": 1}'
```

```
/mcp call scholarly-enhanced search_publications '{"query": "machine learning", "limit": 2}'
```

## Available Tools

Once configured, you can use these tools in Claude Code:

### Basic Search
- `search_author` - Search for authors by name
- `search_publications` - Search for publications
- `get_author_details` - Get detailed author information

### Enhanced Full-Text Tools
- `get_full_text_by_doi` - Get full text of papers by DOI
- `get_full_text_by_title` - Get full text of papers by title
- `find_open_access_versions` - Find open access versions
- `search_with_full_text` - Search with full text extraction
- `extract_pdf_text_from_url` - Extract text from PDF URLs

### Other Tools
- `search_organizations` - Search for academic institutions
- `get_bibtex_citation` - Generate BibTeX citations

## Example Usage in Claude Code

### Search for Papers and Get Full Text

```
Please search for papers about "transformer neural networks" and try to get the full text of the most cited one.
```

### Get Author Information

```
Find information about researcher "Yann LeCun" including his publications and citation metrics.
```

### Extract Text from a Research Paper

```
I have this arXiv paper URL: https://arxiv.org/pdf/1706.03762.pdf - can you extract and summarize the full text?
```

## Troubleshooting

### Server Not Found
- Check that the working directory path is correct
- Ensure Python dependencies are installed
- Verify that `python3` is available in your PATH

### Permission Errors
- Make sure Claude Code has read/write permissions for the project directory
- On Windows, try running Claude Code as administrator

### Import Errors
- Run `pip install -r requirements_enhanced.txt` in the project directory
- Check that all required Python packages are installed

### Rate Limiting
- The server includes built-in rate limiting
- For higher limits, consider getting API keys for Semantic Scholar and CORE

## Environment Variables (Optional)

For enhanced functionality, you can set these environment variables:

```bash
# API Keys for higher rate limits
export SEMANTIC_SCHOLAR_API_KEY="your_key"
export CORE_API_KEY="your_key"

# Email for Unpaywall (recommended)
export UNPAYWALL_EMAIL="your_email@example.com"

# PDF Processing Configuration
export MAX_PDF_SIZE_MB="50"
export PDF_TIMEOUT="60"

# Proxy Configuration (if needed)
export PROXY_TYPE="none"  # Options: none, free, scraperapi, luminati
```

## Advanced Configuration

### Custom Python Environment

If you're using a virtual environment or conda:

```json
{
  "scholarly-enhanced": {
    "command": "/path/to/your/venv/bin/python",
    "args": ["scholarly_enhanced_server.py"],
    "cwd": "/mnt/d/repos/scholarly-mcp"
  }
}
```

### Multiple Server Configurations

You can configure both the enhanced and basic servers:

```json
{
  "scholarly-enhanced": {
    "command": "python3",
    "args": ["scholarly_enhanced_server.py"],
    "cwd": "/mnt/d/repos/scholarly-mcp"
  },
  "scholarly-basic": {
    "command": "python3",
    "args": ["scholarly_server.py"],
    "cwd": "/mnt/d/repos/scholarly-mcp"
  }
}
```

## Next Steps

Once configured, you can:

1. **Search Academic Literature**: Ask Claude to find papers on any topic
2. **Analyze Research**: Get full text analysis of open access papers
3. **Generate Citations**: Create properly formatted bibliographies
4. **Track Authors**: Monitor researcher profiles and publications
5. **Access arXiv**: Get full text of preprints and technical papers

The Enhanced Scholarly MCP Server transforms Claude Code into a powerful academic research assistant with access to millions of scholarly publications!