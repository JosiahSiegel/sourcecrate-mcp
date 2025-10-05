# PaperezMCP Dev Container

Optimized development container for the PaperezMCP project with all necessary tools and configurations.

## Features

### Core Tools
- **Python 3.11+** - Runtime for PaperezMCP
- **Node 20** - Base image with npm/npx
- **uv/uvx** - Fast Python package management (critical for MCP servers)
- **Git** - Version control with delta for better diffs
- **GitHub CLI (gh)** - GitHub operations
- **Fly.io CLI (flyctl)** - Deployment management

### Development Tools
- **zsh + fzf** - Enhanced shell with fuzzy finding
- **Claude Code CLI** - AI-powered development
- **Black + Ruff** - Python formatting and linting
- **VS Code Extensions** - Pre-configured Python tooling

## Port Configuration

| Container Port | Windows Port | Service | URL |
|---------------|--------------|---------|-----|
| 9000 | 9000 | HTTP API | http://localhost:9000 |
| 3000 | 3000 | Claude Auth Callback | http://localhost:3000/auth/callback |
| 3001 | 3001 | Browser UI | http://localhost:3001 |

**Note:** VS Code automatically forwards these ports from the container to Windows localhost.
**WSL2 Limitation:** `--network=host` does not work on WSL2/Docker Desktop. Port forwarding is handled by VS Code's `forwardPorts` configuration.

## Claude Code OAuth Authentication

Claude Code uses browser-based OAuth authentication. The devcontainer is configured to:

1. **Persist Authentication**: Volume mount at `/home/node/.claude` stores OAuth session data
2. **OAuth Callback**: Port 3000 handles authentication callbacks from Claude's OAuth flow
3. **First-Time Setup**:
   - Run `claude auth login` in the terminal
   - Click the OAuth link that appears
   - Complete authentication in your browser
   - Session persists across container restarts via the volume mount

**Environment Variables:**
- `CLAUDE_CONFIG_DIR=/home/node/.claude` - Config directory location
- `CLAUDE_AUTH_CALLBACK_URL=http://localhost:3000/auth/callback` - OAuth callback URL

## Python Dependencies

**Dependencies are NOT pre-installed in the Docker image.** This keeps the image lean and ensures dependencies always match `pyproject.toml`.

Install dependencies as needed:

```bash
# For MCP server (Claude Code)
uvx --from git+https://github.com/JosiahSiegel/paperez-mcp.git paperez-mcp

# For HTTP server (local development)
uvx --from .[http] paperez-http --port 9000

# For development (editable install)
uv pip install -e .[dev,http]
```

## Local Development Workflow

### Start Services
```bash
# Interactive menu
bash scripts/local-manager.sh

# Or use direct commands:
bash scripts/local-manager.sh start-all    # Start HTTP API + Browser UI
bash scripts/local-manager.sh http-start   # Start HTTP API only
bash scripts/local-manager.sh ui-start     # Start Browser UI only
```

### Stop Services
```bash
bash scripts/local-manager.sh stop-all     # Stop all services
bash scripts/local-manager.sh http-stop    # Stop HTTP API only
bash scripts/local-manager.sh ui-stop      # Stop Browser UI only
```

### Check Status
```bash
bash scripts/local-manager.sh status       # Show all service status
bash scripts/local-manager.sh logs         # Tail all logs
bash scripts/local-manager.sh http-logs    # Tail HTTP API logs
bash scripts/local-manager.sh ui-logs      # Tail UI logs
```

## Deployment Workflow (Fly.io)

### Start Services
```bash
# Interactive menu with fly status
bash scripts/fly-manager.sh

# Quick actions:
bash scripts/fly-manager.sh start-all      # Start both API and frontend
bash scripts/fly-manager.sh stop-all       # Stop all machines
bash scripts/fly-manager.sh restart-all    # Restart all machines
```

### Deploy Updates
```bash
bash scripts/fly-manager.sh deploy         # Deploy latest code
bash scripts/fly-manager.sh deploy-frontend  # Deploy frontend only
bash scripts/fly-manager.sh deploy-backend   # Deploy backend only
```

## Code Quality

### Format & Lint
```bash
black paperez_mcp_server.py paperez_mcp/   # Format code
ruff check paperez_mcp_server.py paperez_mcp/  # Lint code
mypy paperez_mcp_server.py paperez_mcp/    # Type checking
```

### Testing
```bash
pytest                                      # Run all tests
pytest -v                                   # Verbose output
pytest --cov=paperez_mcp                   # With coverage
```

### Pre-commit Validation
```bash
python3 -m py_compile paperez_mcp_server.py  # Syntax check
git commit                                    # Runs pre-commit hooks
```

## Rebuild Container

After modifying `.devcontainer/` files:

1. **Rebuild Container:**
   - Press `Ctrl+Shift+P` (Windows) / `Cmd+Shift+P` (Mac)
   - Select: "Dev Containers: Rebuild Container"

2. **Or Reload Window:**
   - Press `Ctrl+Shift+P` / `Cmd+Shift+P`
   - Select: "Developer: Reload Window"

## Network Configuration

**WSL2/Docker Desktop Environment:**
- VS Code's `forwardPorts` automatically forwards container ports to Windows
- Container ports are accessible via `localhost` on Windows
- Port mapping is automatic (container:9000 → Windows:9000)
- ⚠️ `--network=host` does NOT work on WSL2 (Linux-only feature)
- ✅ No manual port configuration needed - VS Code handles it automatically

## Differences from `hmm` Devcontainer

| Feature | hmm | paperez-mcp |
|---------|-----|-------------|
| Python dependencies | Pre-installed in image | Installed via uv as needed |
| Firewall (iptables) | Yes | No (not needed) |
| Network capabilities | NET_ADMIN, NET_RAW | Standard |
| VS Code extensions | General development | Python-specific |
| Focus | Multi-purpose sandbox | PaperezMCP development |

**Why no pre-installed Python deps?**
- Keeps Docker image small and fast to build
- Ensures dependencies always match `pyproject.toml`
- uv/uvx are extremely fast (3-5s install time)
- Prevents version drift between image and code
