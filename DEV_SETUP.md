# Development Environment Setup

This guide is for **local development** in this environment. For production deployment via GitHub URL, see `DEPLOYMENT.md`.

## 🔧 Local Development Configuration

### Current Environment Setup

The `.mcp.json` in this repository is configured for local development:

```json
{
  "mcpServers": {
    "scholarly-enhanced": {
      "command": "python3",
      "args": ["scholarly_enhanced_server.py"],
      "cwd": "/mnt/d/repos/scholarly-mcp",
      "env": {
        "UNPAYWALL_EMAIL": "research@example.com",
        "MAX_PDF_SIZE_MB": "50",
        "PDF_TIMEOUT": "60",
        "ENABLE_CACHING": "false",
        "PROXY_TYPE": "none",
        "RATE_LIMIT_DELAY": "1.0"
      }
    }
  }
}
```

### Quick Development Workflow

1. **Install Dependencies** (if needed):
   ```bash
   pip install -r requirements_enhanced.txt
   ```

2. **Test Local Configuration**:
   ```bash
   python3 local_test_client.py
   ```

3. **Run Server Locally**:
   ```bash
   python3 scholarly_enhanced_server.py
   ```

4. **Test with Examples**:
   ```bash
   python3 examples/basic_usage.py
   ```

### Claude Code Integration (Development)

For this development environment, Claude Code should automatically detect the `.mcp.json` configuration and load the `scholarly-enhanced` server.

**Verify it's working:**
```
/mcp list
```

**Test the server:**
```
/mcp call scholarly-enhanced search_author '{"name": "Geoffrey Hinton", "limit": 1}'
```

## 🌐 Production vs Development

### Development (This Environment)
- Uses local Python execution
- Direct file system access
- Local dependency management
- Fast iteration and debugging

### Production (GitHub URL Deployment)
- Uses FastMCP Cloud execution
- Managed dependencies
- Automatic scaling
- Zero local setup for users

The configurations in `claude_desktop_config.json` and `claude_code_config.json` are designed for end users who want to deploy from the GitHub URL without any local setup.

## 🧪 Testing in Development

### Quick Tests
```bash
# Test configuration
python3 local_test_client.py

# Test server functionality
python3 test_local.py

# Test basic usage
python3 examples/basic_usage.py
```

### Available Development Tools
- `test_local.py` - Comprehensive server testing
- `local_test_client.py` - MCP integration testing
- `examples/` - Usage examples and demos
- `setup_claude_code.py` - Configuration helpers

## 🚀 Publishing Changes

When ready to publish:

1. **Test locally** with development configuration
2. **Update GitHub repository**
3. **Users automatically get updates** via GitHub URL deployment
4. **No user action required** - FastMCP handles the rest

This dual-configuration approach ensures smooth development while maintaining zero-setup deployment for end users!