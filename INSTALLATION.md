# PaperezMCP Installation Guide

## Quick Installation

### Option 1: Direct from GitHub (Recommended)
```bash
# Add to Claude Desktop or MCP client
claude mcp add -s project paperez-mcp -- uvx --from git+https://github.com/JosiahSiegel/paperez-mcp.git paperez-mcp
```

### Option 2: Local Development
```bash
# Clone repository
git clone https://github.com/JosiahSiegel/paperez-mcp.git
cd paperez-mcp

# Install dependencies
pip install -r requirements.txt

# Run server directly
python scholarly_enhanced_server.py
```

## Verification

### Check Available Tools
After installation, verify the tools are available:

```python
# In your MCP client, these tools should be available:
- mcp__paperez-mcp__search_papers
- mcp__paperez-mcp__search_authors
- mcp__paperez-mcp__extract_pdf_text
- mcp__paperez-mcp__convert_pdf_to_markdown
- mcp__paperez-mcp__batch_convert_pdfs
- mcp__paperez-mcp__get_status
```

### Test Basic Functionality
```python
# Test the server is working
mcp__paperez-mcp__get_status()

# Test basic search (returns metadata only)
mcp__paperez-mcp__search_papers(query="machine learning", limit=3)

# Test downloading papers as files
mcp__paperez-mcp__search_papers(query="transformers", limit=3, download_and_convert=True)
```

## Troubleshooting

### Tool Not Available Error
```
Error: No such tool available: mcp__paperez-mcp__search_papers
```

**Solutions:**
1. **Check MCP server is installed**: `claude mcp list`
2. **Restart Claude Desktop** after adding the server
3. **Verify server configuration** in Claude settings
4. **Check logs** for startup errors

### Import Errors
```
ImportError: No module named 'fastmcp'
```

**Solutions:**
1. **Install dependencies**: `pip install fastmcp scholarly pymupdf4llm`
2. **Use virtual environment**: `python -m venv venv && source venv/bin/activate`
3. **Check Python version**: Requires Python 3.8+

### Configuration Issues

#### Claude Desktop Configuration
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "paperez-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/JosiahSiegel/paperez-mcp.git", "paperez-mcp"]
    }
  }
}
```

#### Environment Variables (Optional)
```bash
# For enhanced functionality (optional)
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export SCRAPERAPI_KEY="your_key_here"
```

## Common Usage Patterns

### ⚠️ IMPORTANT: Getting Full Papers vs Metadata

**❌ Common Mistake - Only Gets Summaries:**
```python
search_papers("topic", limit=10)  # Returns only metadata/abstracts
```

**✅ Correct - Get Full Papers as Files:**
```python
search_papers("topic", limit=3, download_and_convert=True)  # Downloads PDFs as markdown
```

**✅ Correct - Get Full Text in Memory:**
```python
search_papers("topic", limit=10, include_full_text=True)  # Full text for analysis
```

### Research Workflows

#### Save 10 Papers on a Topic
```python
# Option 1: Multiple download calls (3 papers each)
papers1 = search_papers("topic A", limit=3, download_and_convert=True)
papers2 = search_papers("topic B", limit=3, download_and_convert=True)
papers3 = search_papers("topic C", limit=3, download_and_convert=True)

# Option 2: Search then individual download
metadata = search_papers("topic", limit=10)
for paper in metadata[0]["results"]:
    if paper.get("pdf_url"):
        convert_pdf_to_markdown(paper["pdf_url"], output_path=f"papers/{paper['title'][:50]}.md")
```

#### Batch Convert Existing PDFs
```python
batch_convert_pdfs("pdf_directory/", "markdown_output/")
```

## Support

- **Repository**: https://github.com/JosiahSiegel/paperez-mcp
- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Check README.md for detailed usage examples