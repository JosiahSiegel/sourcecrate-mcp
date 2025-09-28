# Installation Guide

## Quick Install

### Claude Code
```bash
claude mcp add -s project paperez-mcp -- uvx --from git+https://github.com/JosiahSiegel/paperez-mcp.git paperez-mcp
```

### Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "paperez-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/JosiahSiegel/paperez-mcp.git", "paperez-mcp"],
      "env": {"UNPAYWALL_EMAIL": "your_email@example.com"}
    }
  }
}
```

## Optional: Enhanced Performance

```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CROSSREF_EMAIL="your_email@example.com"
```

## Development Setup

```bash
git clone https://github.com/JosiahSiegel/paperez-mcp.git
cd paperez-mcp
pip install -e .[dev]
python paperez_mcp_server.py
```

## Common Issues

**Server not detected:** Restart Claude Code after installation
**Permission error:** `chmod 755 ~/.local/share/mcp-servers/`