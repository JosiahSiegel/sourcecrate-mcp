# Installation Guide

## Zero-Installation Deployment

### For Claude Code (Recommended)

```bash
claude mcp add -s project paperez-mcp -- uvx --from git+https://github.com/JosiahSiegel/paperez-mcp.git paperez-mcp
```

### For Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "paperez-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JosiahSiegel/paperez-mcp.git",
        "paperez-mcp"
      ],
      "env": {
        "UNPAYWALL_EMAIL": "your_email@example.com"
      }
    }
  }
}
```

## Why uvx Deployment?

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

## Development Installation

For development work:

```bash
# Clone repository
git clone https://github.com/JosiahSiegel/paperez-mcp.git
cd paperez-mcp

# Install development dependencies
pip install -e .[dev]

# Run local MCP server
python paperez_mcp_server.py
```

## Environment Variables

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

## Troubleshooting

### MCP Server Not Detected

1. Verify `.mcp.json` syntax and location
2. Restart Claude Code/Desktop after changes
3. Use absolute uvx path if needed:
   ```json
   "command": "/home/node/.local/bin/uvx"
   ```

### Permission Issues

Ensure the MCP server directory is writable:
```bash
chmod 755 ~/.local/share/mcp-servers/
```