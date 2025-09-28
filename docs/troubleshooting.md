# Troubleshooting Guide

## Common Issues & Solutions

### 1. "No Results Found" from Search

**Problem**: Query not finding papers across databases.

**Solutions:**
- **Use specific queries**: Use exact titles, author names, or DOIs when possible
- **Check API status**: Use "Check system status" to see which sources are available
- **Biomedical papers**: System automatically includes PubMed for medical terms
- **Try different categories**: Use force_category for specific source types

**Example:**
```
Instead of: "AI papers"
Try: "Attention Is All You Need" or "Vaswani transformer"
```

### 2. HTTP 429 (Rate Limited) Errors

**Problem**: Hitting API rate limits.

**Solutions:**
- **Automatic handling**: Server implements exponential backoff and retry logic
- **API keys**: Set `SEMANTIC_SCHOLAR_API_KEY` for higher Semantic Scholar limits
- **Multi-source fallback**: Rate limits on one source trigger automatic fallback
- **Smart caching**: Repeat queries served from 1GB local cache

**Configuration:**
```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CROSSREF_EMAIL="your_email@example.com"
```

### 3. PDF Extraction Issues

**Problem**: Cannot extract text from PDF URLs.

**Solutions:**
- **Check accessibility**: Some PDFs may be behind paywalls or access restrictions
- **Local processing**: Download PDF first, then use local conversion tools
- **Batch processing**: Use `batch_convert_pdfs` for multiple files
- **Alternative sources**: System automatically finds alternative PDF sources

**Workflow:**
1. First try: "Download machine learning papers"
2. If blocked: Download PDFs manually, then "Convert PDFs in folder"

### 4. MCP Server Not Detected

**Problem**: Configuration or path issues.

**Solutions:**

1. **Verify installation:**
   ```bash
   claude mcp list
   ```

2. **Restart Claude Code** after installation

3. **Check uvx path** - use absolute path if needed:
   ```json
   "command": "/home/node/.local/bin/uvx"
   ```

4. **Verify project scope**:
   ```bash
   claude mcp add -s project paperez-mcp -- uvx --from git+https://github.com/JosiahSiegel/paperez-mcp.git paperez-mcp
   ```

### 5. Large PDF Processing

**Problem**: Very large PDFs taking too long or failing.

**Solutions:**
- **Unlimited processing**: Server handles papers of any size (no character/page limits)
- **Zero-token conversion**: Efficient processing without AI context usage
- **Local storage**: Download first, process locally to avoid network timeouts
- **Batch operations**: Use `batch_convert_pdfs` for multiple large files

### 6. Configuration Issues

**Problem**: Custom configuration not loading.

**Solutions:**
- **Check file path**: Ensure config at `.paperez/config/config.yaml`
- **Validate YAML syntax**: Use online YAML validator
- **Restart Claude Code** after configuration changes
- **Use get_status**: Check if config loaded successfully

**Debug steps:**
1. "Check system status" - see current configuration
2. "Help me configure paperez-mcp" - get setup guidance
3. Verify file permissions on config directory

### 7. Empty or Missing Results

**Problem**: Searches return no papers or incomplete results.

**Solutions:**
- **Check source status**: Some academic APIs may be temporarily down
- **Try different queries**: Rephrase search terms or use author names
- **Force different categories**: Try `"open_access"` or `"preprints"`
- **Multi-source approach**: System automatically tries multiple databases

**Debugging:**
1. "Check system status" - see which APIs are working
2. Try specific author: "papers by Geoffrey Hinton"
3. Use DOI if available: "doi:10.1000/xyz123"

## Best Practices

### 1. Search Strategy
- **Start specific**: Use exact titles, author names, or DOIs
- **Then broaden**: Use keywords if specific searches fail
- **Check status first**: Use "Check system status" if having issues

### 2. API Configuration
- **Set email**: `CROSSREF_EMAIL` for better rate limits
- **Get API key**: `SEMANTIC_SCHOLAR_API_KEY` for higher limits
- **Use caching**: Leverage 1GB smart cache for repeat queries

### 3. Processing Pipeline
1. **Search** → find papers
2. **Browse** → review metadata
3. **Download** → get full papers
4. **Convert** → process to preferred format

### 4. Troubleshooting Workflow
1. **Check status**: "Check system status"
2. **Try simple query**: "papers by Einstein"
3. **Check configuration**: "Help me configure paperez-mcp"
4. **Restart if needed**: Restart Claude Code

## Performance Tips

- **Use specific queries** for faster, more accurate results
- **Leverage caching** - repeat queries are much faster
- **Set API keys** for better rate limits and performance
- **Local processing** is faster than repeated URL extraction
- **Batch operations** handle multiple papers efficiently

## Getting Help

1. **Built-in help**: "Help me configure paperez-mcp"
2. **System status**: "Check system status"
3. **Documentation**: Check [Configuration Guide](configuration.md)
4. **GitHub Issues**: [Report issues](https://github.com/JosiahSiegel/paperez-mcp/issues)

## Common Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Rate limited" | API quota exceeded | Wait or set API keys |
| "No results found" | Query too broad/specific | Adjust search terms |
| "PDF not accessible" | Paywall/restricted access | Try different sources |
| "Config not found" | Missing configuration | Create config file |
| "Server timeout" | Network/API issue | Check status, retry |