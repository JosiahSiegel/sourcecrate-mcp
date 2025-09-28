# Troubleshooting Guide

## Common Issues

### No Results Found
**Problem**: Search returns no papers
**Solutions**:
- Use specific queries: author names, exact titles
- Try different categories: "Get medical papers about..."
- Check API status: "Check system status"

### Rate Limited
**Problem**: API quota exceeded
**Solutions**:
- Set API keys: `export SEMANTIC_SCHOLAR_API_KEY="your_key"`
- Wait and retry (automatic backoff included)
- Use caching for repeat queries

### PDF Access Issues
**Problem**: Cannot extract text from PDFs
**Solutions**:
- Try open access sources first
- Download PDFs manually, then convert locally
- Use batch conversion: "Convert PDFs in folder"

### Server Not Detected
**Problem**: MCP server not found
**Solutions**:
- Restart Claude Code after installation
- Check installation: `claude mcp list`
- Use absolute path if needed: `/home/node/.local/bin/uvx`

### Large PDF Timeout
**Problem**: Large PDFs fail to process
**Solutions**:
- Download locally first, then convert
- Use batch processing for multiple files
- Check file permissions

## Quick Fixes

| Error | Solution |
|-------|----------|
| "Rate limited" | Set API keys or wait |
| "No results" | Use specific search terms |
| "PDF blocked" | Try different sources |
| "Config error" | Check YAML syntax |
| "Permission denied" | `chmod 755 ~/.local/share/mcp-servers/` |

## Get Help

1. "Check system status" - see API health
2. "Help me configure paperez-mcp" - setup guidance
3. Try simple query: "papers by Einstein"
4. Restart Claude Code if issues persist