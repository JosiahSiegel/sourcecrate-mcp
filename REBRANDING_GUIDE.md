# Complete Rebranding Guide: PaperezMCP → [NEW_NAME]

> **Comprehensive guide to rebrand the entire repository, MCP server, API, and UI**

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Preparation Phase](#preparation-phase)
4. [Phase 1: Core Package Rename](#phase-1-core-package-rename)
5. [Phase 2: Configuration Updates](#phase-2-configuration-updates)
6. [Phase 3: Code Reference Updates](#phase-3-code-reference-updates)
7. [Phase 4: Documentation Updates](#phase-4-documentation-updates)
8. [Phase 5: Deployment & Infrastructure](#phase-5-deployment--infrastructure)
9. [Phase 6: Git & Version Control](#phase-6-git--version-control)
10. [Phase 7: External Services](#phase-7-external-services)
11. [Verification & Testing](#verification--testing)
12. [Rollback Plan](#rollback-plan)

---

## Overview

### What's Being Rebranded

- **Package name**: `paperez-mcp` → `[new-name]`
- **Python module**: `paperez_mcp` → `[new_name]`
- **Display name**: `PaperezMCP` → `[NewName]`
- **MCP server**: Tool names, descriptions, server identity
- **HTTP API**: Endpoints, server names, CORS origins
- **Browser UI**: Branding, titles, descriptions
- **Deployment**: Fly.io app, Docker images, domains

### Impact Analysis

- **424 occurrences** of "paperez" across 63 files
- **150 occurrences** of "Paperez/PAPEREZ" across 40 files
- **Core files affected**: ~80+ files
- **External dependencies**: PyPI, GitHub, Fly.io, Claude Code configs

---

## Prerequisites

### Required Tools

```bash
# Install required tools
pip install -e ".[dev,http]"  # Development dependencies
npm install -g replace-in-files  # Optional: for bulk replacements

# Verify git is clean
git status
# Commit any pending changes before starting
```

### Backup Strategy

```bash
# 1. Create a rebranding branch
git checkout -b rebrand-to-[new-name]

# 2. Tag current state
git tag pre-rebrand-$(date +%Y%m%d)

# 3. Create backup directory
mkdir -p ../paperez-mcp-backup
cp -r . ../paperez-mcp-backup/
```

### Name Selection

Before proceeding, decide on:

- **Package name** (lowercase, hyphen): `source-crate`
- **Module name** (lowercase, underscore): `source_crate`
- **Display name** (proper case): `SourceCrate`
- **Abbreviated name** (if applicable): `SC` or keep full

**Example mapping for this guide:**
- `paperez-mcp` → `source-crate`
- `paperez_mcp` → `source_crate`
- `PaperezMCP` → `SourceCrate`
- `Paperez` → `SourceCrate`

---

## Preparation Phase

### Step 1: Create Search/Replace Mapping

Create `rebrand_mapping.json`:

```json
{
  "package_name": "source-crate",
  "module_name": "source_crate",
  "display_name": "SourceCrate",
  "display_name_lower": "sourcecrate",
  "github_user": "YourUsername",
  "github_repo": "source-crate",
  "fly_app": "sourcecrate-api",
  "pypi_name": "source-crate"
}
```

### Step 2: Identify Critical Files

**Files requiring manual review** (order matters):

1. `pyproject.toml` - Package metadata
2. `fly.toml` - Fly.io deployment
3. `Dockerfile.flyio` - Container config
4. `paperez_mcp/` directory - Rename to new module name
5. All import statements
6. README.md and docs/
7. Configuration files
8. Scripts and tools

---

## Phase 1: Core Package Rename

### 1.1 Rename Python Module Directory

```bash
# Critical: Do this FIRST before any code changes
mv paperez_mcp source_crate

# Verify the move
ls -la source_crate/
```

### 1.2 Update pyproject.toml

**File**: `/workspace/pyproject.toml`

**Changes needed** (lines to update):

```toml
# Line 2: Package name
name = "source-crate"

# Line 4: Description
description = "SourceCrate - Academic paper research made easy with full-text retrieval and multi-source search"

# Lines 46-50: URLs
[project.urls]
Homepage = "https://github.com/YourUsername/source-crate"
Repository = "https://github.com/YourUsername/source-crate"
Issues = "https://github.com/YourUsername/source-crate/issues"
Documentation = "https://github.com/YourUsername/source-crate#readme"

# Lines 52-54: Entry points
[project.scripts]
source-crate = "source_crate.install_and_run:main"
sourcecrate-http = "source_crate.http_server:main"

# Line 76: Hatch packages
packages = ["source_crate"]

# Lines 80-83: Include patterns
include = [
    "source_crate/**/*.py",
    "source_crate/**/*.yaml",
    "source_crate/**/*.yml",
]

# Lines 87-91: Setuptools config
[tool.setuptools.packages.find]
include = ["source_crate*"]

[tool.setuptools.package-data]
"source_crate.default_configs" = ["*.yaml", "*.yml"]
"source_crate" = ["default_configs/*.yaml", "default_configs/*.yml"]
```

### 1.3 Update Package Imports

**Critical files with imports** (update in this order):

1. **`source_crate/__init__.py`**
2. **`source_crate/server.py`** (MCP server entry)
3. **`source_crate/http_server.py`** (HTTP API entry)
4. **`source_crate/install_and_run.py`** (Installer)

**Search/replace pattern for ALL Python files**:

```bash
# Find all import statements
grep -r "from paperez_mcp" --include="*.py" .
grep -r "import paperez_mcp" --include="*.py" .

# Replace imports
find . -type f -name "*.py" -exec sed -i 's/from paperez_mcp/from source_crate/g' {} +
find . -type f -name "*.py" -exec sed -i 's/import paperez_mcp/import source_crate/g' {} +
```

**Manual verification required for**:

- Dynamic imports: `importlib.import_module()`
- String references: `"paperez_mcp"`
- Documentation strings in imports

### 1.4 Update Entry Points

**File**: `source_crate/install_and_run.py`

```python
# Line 11: Update package name
PACKAGE_NAME = "source-crate"

# Update any hardcoded references
```

**File**: `source_crate/server.py`

```python
# Line 56: Update server name
mcp = FastMCP("SourceCrate", dependencies=["httpx", "aiohttp", ...])
```

**File**: `source_crate/http_server.py`

```python
# Line 10: Update app title/description
app = FastAPI(
    title="SourceCrate HTTP API",
    description="HTTP/REST API for SourceCrate - Academic paper research made easy",
    version="1.1.0"
)
```

---

## Phase 2: Configuration Updates

### 2.1 Fly.io Configuration

**File**: `/workspace/fly.toml`

```toml
# Line 1: Update comment
# fly.toml app configuration file generated for sourcecrate-api on [date]

# Line 6: App name
app = 'sourcecrate-api'

# Line 38: Static files path (if module renamed)
guest_path = "/app/browser-ui"
```

### 2.2 Dockerfile Updates

**File**: `/workspace/Dockerfile.flyio`

```dockerfile
# Update COPY commands if module name changed
COPY source_crate/ /app/source_crate/

# Update CMD/ENTRYPOINT
CMD ["python", "-m", "source_crate.http_server"]
```

### 2.3 Config Files

**File**: `/workspace/config.example.yaml`

Update all comments and references:

```yaml
# Line 2: Update header comment
# SourceCrate Configuration File
```

**Files**: `source_crate/default_configs/*.yaml`

Update metadata in each config file:

```yaml
# base.yaml, humanities.yaml, etc.
# Line 1: Update header
# SourceCrate - [Category] Configuration
```

### 2.4 DevContainer Configuration

**File**: `.devcontainer/devcontainer.json`

```json
{
  "name": "SourceCrate Development",
  // Update other references
}
```

---

## Phase 3: Code Reference Updates

### 3.1 MCP Server Tool Descriptions

**File**: `source_crate/server.py`

Update tool docstrings (critical for token optimization):

```python
# Each @mcp.tool() function docstring
"""
🔍 BROWSE: Find research papers...
(Keep existing content, just verify branding)
"""
```

**Note**: Tool docstrings are heavily optimized for minimal tokens. Only update if absolutely necessary.

### 3.2 HTTP API Updates

**File**: `source_crate/http_server.py`

```python
# CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://sourcecrate-api.fly.dev",  # Update
        "https://yourdomain.com"  # Your domain
    ]
)

# Health check endpoint
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "SourceCrate HTTP API",  # Update
        "version": "1.1.0"
    }
```

### 3.3 Configuration Manager

**File**: `source_crate/config/manager.py`

```python
# Line 32: Update config directory references
CONFIG_DIRS = [
    Path.home() / ".sourcecrate" / "config",  # Update
    Path.cwd() / "sourcecrate" / "config",     # Update
    # ...
]
```

**File**: `source_crate/config/singleton.py`

```python
# Line 5: Update singleton references
# Update any class names or docstrings
```

### 3.4 Core Module Updates

**Files**: `source_crate/core/*.py`

Update all docstrings and comments:

```python
# search.py, download.py, pdf_conversion.py, status.py
"""SourceCrate core functionality for [feature]"""
```

### 3.5 Utility Modules

**Files**: `source_crate/utils/*.py`

Search for hardcoded references:

```bash
grep -r "paperez" source_crate/utils/ --include="*.py"
```

Update:
- Logger names: `logger = logging.getLogger("source_crate.utils.smart_search")`
- Error messages
- Cache keys
- File paths

### 3.6 Plugin System

**File**: `source_crate/plugins/__init__.py`

```python
# Line 2-3: Update references
"""SourceCrate plugin system for extensibility"""
```

**File**: `source_crate/plugins/simple.py`

```python
# Line 4-8: Update example plugin
"""
Example SourceCrate plugin
"""
```

---

## Phase 4: Documentation Updates

### 4.1 Main README

**File**: `/workspace/README.md`

**Critical updates** (line numbers from current file):

```markdown
# Line 1: Title
# SourceCrate 📚🚀

# Line 3: Tagline
> **Academic paper research made easy through the Model Context Protocol (MCP)**

# Line 5: Description
SourceCrate is a comprehensive MCP server...

# Line 7: Badges
[![GitHub](https://img.shields.io/badge/GitHub-YourUsername%2Fsource--crate-blue)](https://github.com/YourUsername/source-crate)

# Line 19: Installation
claude mcp add -s project source-crate -- uvx --from git+https://github.com/YourUsername/source-crate.git source-crate

# Line 27: Clone example
git clone https://github.com/YourUsername/source-crate.git
cd source-crate

# Line 31: Installation command
claude mcp add -s project source-crate -- python /path/to/source-crate/install_and_run.py

# Line 34: uvx command
claude mcp add -s project source-crate -- uvx --from /path/to/source-crate source-crate

# Line 48-51: Usage examples
- "Download 3 machine learning papers"
- "Convert this PDF to markdown: /path/to/paper.pdf"
- "Help me configure source-crate"

# Line 76: HTTP server
uvx --from 'git+https://github.com/YourUsername/source-crate.git[http]' sourcecrate-http

# Line 82-84: Clone commands
git clone https://github.com/YourUsername/source-crate.git
cd source-crate
uvx --from '.[http]' sourcecrate-http

# Line 98: Start command
sourcecrate-http
```

**Search for all occurrences**:

```bash
sed -i 's/paperez-mcp/source-crate/g' README.md
sed -i 's/PaperezMCP/SourceCrate/g' README.md
sed -i 's/paperez/sourcecrate/g' README.md
```

### 4.2 Documentation Files

**Files to update**:

1. **`CLAUDE.md`** (Project instructions)
   - Line 1: `# CLAUDE.md`
   - Line 9: `PaperezMCP is a Model Context Protocol...` → `SourceCrate is a...`
   - Search: `paperez` → `sourcecrate`

2. **`docs/configuration.md`**
   ```bash
   sed -i 's/paperez/sourcecrate/g' docs/configuration.md
   sed -i 's/PaperezMCP/SourceCrate/g' docs/configuration.md
   ```

3. **`docs/HTTP_API.md`**
   - Update all API examples
   - Update URLs: `https://sourcecrate-api.fly.dev`

4. **`docs/DEPLOYMENT.md`**
   - Update Fly.io app names
   - Update repository URLs
   - Update commands

5. **`docs/CUSTOM_SOURCE_GUIDE.md`** & **`docs/CUSTOM_SOURCE_QUICKSTART.md`**
   - Update examples
   - Update file paths

6. **`docs/RELEVANCE_SCORING.md`**
   - Update references

### 4.3 Legal Documents

**File**: `docs/legal/TERMS_OF_SERVICE.md`

```markdown
# SourceCrate Terms of Service

Last Updated: [DATE]

## Service Description
SourceCrate ("we", "our", "the Service")...
```

**File**: `docs/legal/ToS_COMPLIANCE.md`

Update all references to the service name.

### 4.4 DevContainer Documentation

**Files**:
- `.devcontainer/README.md`
- `.devcontainer/TROUBLESHOOTING.md`

```bash
sed -i 's/PaperezMCP/SourceCrate/g' .devcontainer/*.md
sed -i 's/paperez-mcp/source-crate/g' .devcontainer/*.md
```

### 4.5 Browser UI Documentation

**File**: `browser-ui/README.md`

```markdown
# SourceCrate Browser UI

Web interface for the SourceCrate HTTP API.
```

**File**: `browser-ui/MODULARIZATION.md`

Update all references.

### 4.6 Scripts Documentation

**File**: `scripts/README.md`

```bash
sed -i 's/paperez/sourcecrate/g' scripts/README.md
```

### 4.7 Test Documentation

**File**: `tests/README.md`

```bash
sed -i 's/PaperezMCP/SourceCrate/g' tests/README.md
```

---

## Phase 5: Deployment & Infrastructure

### 5.1 Scripts Updates

**File**: `scripts/fly-manager.sh`

```bash
# Update default app name
DEFAULT_APP="sourcecrate-api"

# Update references in echo statements
echo "SourceCrate Fly.io Manager"
```

**File**: `scripts/local-manager.sh`

```bash
# Line 13: Update references
echo "SourceCrate Local Development Manager"

# Update any paperez references
sed -i 's/paperez/sourcecrate/g' scripts/local-manager.sh
```

**Files**: `scripts/validate_*.py`

Update imports and references:

```python
# validate_code_quality.py, validate_imports.py, etc.
from source_crate import ...

# Update docstrings
"""SourceCrate validation script for..."""
```

### 5.2 Docker & Containerization

**File**: `Dockerfile.flyio`

```dockerfile
# Update LABEL metadata
LABEL org.opencontainers.image.title="SourceCrate HTTP API"
LABEL org.opencontainers.image.description="Academic paper research API"
LABEL org.opencontainers.image.source="https://github.com/YourUsername/source-crate"

# Update COPY commands
COPY source_crate/ /app/source_crate/
COPY browser-ui/ /app/browser-ui/

# Update CMD
CMD ["python", "-m", "source_crate.http_server"]
```

### 5.3 Environment Configuration

**File**: `.env.example` (if exists)

```bash
# SourceCrate Configuration
SOURCECRATE_API_KEY=your-api-key
SOURCECRATE_LOG_LEVEL=INFO
```

### 5.4 GitHub Actions / CI

**Files**: `.github/workflows/*.yml` (if they exist)

```yaml
name: SourceCrate CI

jobs:
  test:
    steps:
      - name: Install SourceCrate
        run: pip install -e ".[dev]"
```

---

## Phase 6: Git & Version Control

### 6.1 Update Git Configuration

**File**: `.git/config`

```ini
[remote "origin"]
    url = https://github.com/YourUsername/source-crate.git
```

Or via command:

```bash
git remote set-url origin https://github.com/YourUsername/source-crate.git
```

### 6.2 GitHub Repository Settings

**On GitHub.com**:

1. Go to repository Settings
2. Repository name: `source-crate`
3. Description: Update to new name
4. Topics/tags: Update
5. Social preview: Update image/text

### 6.3 Create Migration Commit

```bash
# Stage all changes
git add -A

# Commit with clear message
git commit -m "Rebrand: Rename PaperezMCP to SourceCrate

Major changes:
- Rename package: paperez-mcp → source-crate
- Rename module: paperez_mcp → source_crate
- Update all documentation
- Update deployment configs
- Update MCP server identity

BREAKING CHANGE: Package name and import paths have changed.
Users must reinstall with new package name."

# Tag the version
git tag v2.0.0-rebrand
```

### 6.4 Branch Strategy

```bash
# Push rebrand branch
git push -u origin rebrand-to-sourcecrate

# Create PR on GitHub
# After review and approval, merge to main
```

---

## Phase 7: External Services

### 7.1 Fly.io Deployment

**Create new Fly.io app**:

```bash
# Install flyctl if needed
curl -L https://fly.io/install.sh | sh

# Create new app
fly apps create sourcecrate-api

# Update secrets (copy from old app)
fly secrets list -a paperez-api > secrets.txt
# Review secrets.txt and set for new app
fly secrets set KEY=VALUE -a sourcecrate-api

# Deploy
fly deploy -a sourcecrate-api

# Update DNS/domains if applicable
fly domains list -a sourcecrate-api
```

**Migration path**:

```bash
# Option 1: Rename existing app (if possible)
fly apps rename paperez-api sourcecrate-api

# Option 2: Deploy new, then delete old
fly deploy -a sourcecrate-api
# Test thoroughly
fly apps destroy paperez-api
```

### 7.2 PyPI Package

**Publish to PyPI**:

```bash
# Build package
python -m build

# Test with TestPyPI first
python -m twine upload --repository testpypi dist/*

# Verify installation
pip install -i https://test.pypi.org/simple/ source-crate

# Publish to PyPI
python -m twine upload dist/*
```

**Reserve old package name**:

```bash
# Create redirect package (optional)
# Create paperez-mcp package that depends on source-crate
# This helps users transition
```

### 7.3 Claude Code / MCP Registry

**Update MCP installations**:

```bash
# Remove old
claude mcp remove paperez-mcp

# Add new
claude mcp add -s project source-crate -- uvx --from git+https://github.com/YourUsername/source-crate.git source-crate

# Restart Claude Code to apply changes
```

### 7.4 Claude Agent Files

**File**: `.claude/agents/paperez-mcp-expert.md`

Rename and update:

```bash
mv .claude/agents/paperez-mcp-expert.md .claude/agents/sourcecrate-expert.md
```

Update content:

```markdown
# SourceCrate Expert Agent

Use this agent when working with the SourceCrate codebase...
```

---

## Verification & Testing

### Phase 1: Import & Syntax Verification

```bash
# 1. Verify Python imports
python -c "import source_crate; print(source_crate.__name__)"

# 2. Check for syntax errors
python -m py_compile source_crate/**/*.py

# 3. Run type checking
mypy source_crate/

# 4. Run linting
black --check source_crate/
ruff check source_crate/
```

### Phase 2: Package Installation Test

```bash
# Clean environment test
python -m venv test-venv
source test-venv/bin/activate

# Test installation
pip install -e ".[dev,http]"

# Verify entry points
which source-crate
which sourcecrate-http

# Test imports
python -c "from source_crate import server"
python -c "from source_crate import http_server"

deactivate
rm -rf test-venv
```

### Phase 3: MCP Server Testing

```bash
# Test MCP server directly
python -m source_crate.install_and_run

# Expected output:
# - Server starts without errors
# - Tools are registered
# - No import errors
```

### Phase 4: HTTP API Testing

```bash
# Start HTTP server
sourcecrate-http &
HTTP_PID=$!

# Test health endpoint
curl http://localhost:8000/health

# Test search endpoint
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "limit": 5}'

# Kill server
kill $HTTP_PID
```

### Phase 5: Unit Tests

```bash
# Run all tests
pytest -v

# Run specific test suites
pytest tests/test_fuzzy_matching.py -v
pytest tests/test_search_analytics.py -v
pytest tests/test_integration_streaming.py -v

# Check coverage
pytest --cov=source_crate --cov-report=term-missing
```

### Phase 6: Integration Tests

```bash
# Test full workflow
python -c "
from source_crate.core.search import search_papers
import asyncio

results = asyncio.run(search_papers('quantum computing', limit=3))
print(f'Found {len(results)} papers')
"

# Test PDF conversion
python -c "
from source_crate.core.pdf_conversion import convert_pdf_to_markdown
result = convert_pdf_to_markdown('test.pdf')
print(result)
"
```

### Phase 7: Browser UI Testing

```bash
# Start HTTP server
sourcecrate-http &

# Open browser to http://localhost:8000
# Test:
# - UI loads
# - Search works
# - Results display
# - No console errors
```

### Phase 8: Deployment Testing

```bash
# Deploy to Fly.io
fly deploy -a sourcecrate-api

# Test deployed API
curl https://sourcecrate-api.fly.dev/health

# Test MCP integration
claude mcp add -s project source-crate -- uvx --from git+https://github.com/YourUsername/source-crate.git source-crate

# Ask Claude: "Test source-crate by searching for papers on transformers"
```

---

## Verification Checklist

### ✅ Core Functionality

- [ ] Python package installs without errors
- [ ] All imports work correctly
- [ ] Entry points (`source-crate`, `sourcecrate-http`) are accessible
- [ ] MCP server starts and registers tools
- [ ] HTTP API responds to health checks
- [ ] Configuration files load properly

### ✅ Code Quality

- [ ] No syntax errors: `python -m py_compile source_crate/**/*.py`
- [ ] Type checking passes: `mypy source_crate/`
- [ ] Linting passes: `black --check source_crate/`
- [ ] Ruff checks pass: `ruff check source_crate/`
- [ ] All tests pass: `pytest`

### ✅ Documentation

- [ ] README.md updated and renders correctly
- [ ] All docs/ files updated
- [ ] CLAUDE.md reflects new name
- [ ] API documentation accurate
- [ ] No broken links in documentation

### ✅ Configuration

- [ ] `pyproject.toml` has correct package metadata
- [ ] `fly.toml` has correct app name
- [ ] Config files reference correct paths
- [ ] Environment variables updated
- [ ] DevContainer config updated

### ✅ Deployment

- [ ] Fly.io app deployed successfully
- [ ] HTTP API accessible at production URL
- [ ] Static files (browser UI) served correctly
- [ ] CORS settings allow frontend access
- [ ] Health checks passing

### ✅ External Services

- [ ] PyPI package published (if applicable)
- [ ] GitHub repository renamed
- [ ] Claude Code MCP integration works
- [ ] Old package name redirects (if implemented)

### ✅ Search & Replace Verification

Run these searches to find any missed references:

```bash
# Search for old package name
grep -r "paperez-mcp" --exclude-dir=".git" --exclude-dir="node_modules" .
grep -r "paperez_mcp" --exclude-dir=".git" --exclude-dir="node_modules" .
grep -r "PaperezMCP" --exclude-dir=".git" --exclude-dir="node_modules" .
grep -r "Paperez" --exclude-dir=".git" --exclude-dir="node_modules" .

# Expected: Only false positives or intentional references (like this guide)
```

---

## Rollback Plan

### If Issues Occur During Migration

#### Immediate Rollback (Before Commit)

```bash
# Discard all changes
git reset --hard HEAD

# Restore from backup
rm -rf source_crate
mv paperez_mcp source_crate  # Wrong, should restore original
# Actually:
rm -rf source_crate
git checkout paperez_mcp
```

#### After Commit (But Before Push)

```bash
# Reset to previous commit
git reset --hard HEAD~1

# Or reset to tag
git reset --hard pre-rebrand-$(date +%Y%m%d)
```

#### After Push (Deployed to Production)

```bash
# Revert the rebrand commit
git revert <rebrand-commit-sha>
git push

# Redeploy old version
fly deploy -a paperez-api
```

#### Fly.io Rollback

```bash
# List releases
fly releases -a sourcecrate-api

# Rollback to previous version
fly releases rollback <version> -a sourcecrate-api
```

#### PyPI Rollback

```bash
# You cannot delete PyPI packages, but you can:
# 1. Yank the version (hides from pip, but still accessible)
python -m twine upload --repository pypi dist/* --skip-existing

# 2. Upload a new version with fixes
# Bump version in pyproject.toml
python -m build
python -m twine upload dist/*
```

---

## Post-Migration Tasks

### Communication

1. **Announce rebrand**:
   - GitHub release notes
   - README update banner
   - PyPI project description

2. **Migration guide for users**:
   ```markdown
   ## Migration from PaperezMCP to SourceCrate

   ### For MCP Users:
   1. Remove old: `claude mcp remove paperez-mcp`
   2. Install new: `claude mcp add -s project source-crate -- uvx --from git+https://github.com/YourUsername/source-crate.git source-crate`
   3. Restart Claude Code

   ### For Python Users:
   1. Uninstall old: `pip uninstall paperez-mcp`
   2. Install new: `pip install source-crate`
   3. Update imports: `from paperez_mcp` → `from source_crate`
   ```

3. **Update external references**:
   - Blog posts
   - Social media
   - Documentation sites
   - Tutorial videos

### Monitoring

Monitor for issues in first 48 hours:

```bash
# Check Fly.io logs
fly logs -a sourcecrate-api

# Monitor error rates
fly status -a sourcecrate-api

# Check download stats
# PyPI: https://pypistats.org/packages/source-crate
```

### Deprecation of Old Name

1. **Archive old repository** (if renamed):
   - Add deprecation notice to README
   - Point to new repository
   - Archive on GitHub

2. **Maintain redirect package** (optional):
   - Create `paperez-mcp` package that imports from `source-crate`
   - Add deprecation warning on import
   - Maintain for 6-12 months

---

## Troubleshooting

### Common Issues

#### Issue: Import Errors After Rename

**Symptom**: `ModuleNotFoundError: No module named 'paperez_mcp'`

**Solution**:
```bash
# Verify module directory was renamed
ls -la | grep source_crate

# Check imports in files
grep -r "from paperez_mcp" --include="*.py" .

# Re-run find/replace
find . -type f -name "*.py" -exec sed -i 's/from paperez_mcp/from source_crate/g' {} +
```

#### Issue: MCP Server Not Found

**Symptom**: Claude Code says "source-crate not found"

**Solution**:
```bash
# Verify entry point in pyproject.toml
grep "source-crate" pyproject.toml

# Reinstall package
pip install -e .

# Restart Claude Code completely
```

#### Issue: HTTP API 404 on Static Files

**Symptom**: Browser UI not loading

**Solution**:
```bash
# Check Dockerfile COPY paths
grep "browser-ui" Dockerfile.flyio

# Verify fly.toml static config
grep -A2 "statics" fly.toml

# Redeploy
fly deploy -a sourcecrate-api
```

#### Issue: Tests Failing After Rename

**Symptom**: ImportError in tests

**Solution**:
```bash
# Update test imports
find tests/ -type f -name "*.py" -exec sed -i 's/from paperez_mcp/from source_crate/g' {} +

# Clear pytest cache
rm -rf .pytest_cache

# Reinstall package
pip install -e ".[dev]"

# Run tests
pytest -v
```

---

## Final Verification Script

Create `verify_rebrand.sh`:

```bash
#!/bin/bash

echo "🔍 SourceCrate Rebranding Verification Script"
echo "=============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0

# Function to check and report
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAIL++))
    fi
}

# 1. Check module exists
echo ""
echo "📦 Checking Package Structure..."
[ -d "source_crate" ] && check "source_crate directory exists" || check "source_crate directory missing"

# 2. Check imports
echo ""
echo "🔗 Checking Imports..."
python -c "import source_crate" 2>/dev/null
check "source_crate imports successfully"

python -c "from source_crate import server" 2>/dev/null
check "source_crate.server imports"

python -c "from source_crate import http_server" 2>/dev/null
check "source_crate.http_server imports"

# 3. Check for old references
echo ""
echo "🔍 Checking for Old References..."
OLD_PKG=$(grep -r "paperez-mcp" --exclude-dir=".git" --exclude="*.md" --exclude="verify_rebrand.sh" . | wc -l)
if [ "$OLD_PKG" -eq 0 ]; then
    check "No 'paperez-mcp' references found"
else
    echo -e "${RED}✗${NC} Found $OLD_PKG references to 'paperez-mcp'"
    ((FAIL++))
fi

OLD_MOD=$(grep -r "paperez_mcp" --exclude-dir=".git" --exclude="*.md" --exclude="verify_rebrand.sh" . | wc -l)
if [ "$OLD_MOD" -eq 0 ]; then
    check "No 'paperez_mcp' references found"
else
    echo -e "${RED}✗${NC} Found $OLD_MOD references to 'paperez_mcp'"
    ((FAIL++))
fi

# 4. Check entry points
echo ""
echo "🚀 Checking Entry Points..."
which source-crate > /dev/null 2>&1
check "source-crate command available"

which sourcecrate-http > /dev/null 2>&1
check "sourcecrate-http command available"

# 5. Check configuration
echo ""
echo "⚙️  Checking Configuration..."
grep -q "name = \"source-crate\"" pyproject.toml
check "pyproject.toml has correct package name"

grep -q "packages = \[\"source_crate\"\]" pyproject.toml
check "pyproject.toml has correct module name"

# 6. Run tests
echo ""
echo "🧪 Running Tests..."
pytest --tb=short -q > /dev/null 2>&1
check "All tests pass"

# 7. Check documentation
echo ""
echo "📚 Checking Documentation..."
grep -q "SourceCrate" README.md
check "README.md references SourceCrate"

grep -q "source-crate" README.md
check "README.md has correct package name"

# Summary
echo ""
echo "=============================================="
echo "Summary: $PASS passed, $FAIL failed"
if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Review output above.${NC}"
    exit 1
fi
```

Run verification:

```bash
chmod +x verify_rebrand.sh
./verify_rebrand.sh
```

---

## Timeline Estimate

**Total estimated time**: 4-6 hours for complete rebrand

- **Preparation**: 30 min
- **Phase 1 (Core Package)**: 1 hour
- **Phase 2 (Configuration)**: 30 min
- **Phase 3 (Code Updates)**: 1 hour
- **Phase 4 (Documentation)**: 1 hour
- **Phase 5 (Deployment)**: 1 hour
- **Phase 6 (Git)**: 30 min
- **Phase 7 (External)**: 1 hour
- **Verification**: 30 min

**With testing and review**: Add 2-3 hours

---

## Success Criteria

✅ **Rebrand is complete when**:

1. All tests pass
2. Package installs with new name
3. MCP server works in Claude Code
4. HTTP API deployed and functional
5. Browser UI accessible
6. No references to old name (except docs/migration guides)
7. Documentation updated
8. External services updated
9. Users can install and use with new name

---

## Support & Questions

If you encounter issues during rebranding:

1. Check this guide's Troubleshooting section
2. Review the verification checklist
3. Check git history: `git log --oneline`
4. Review backup: `../paperez-mcp-backup/`
5. Rollback if necessary (see Rollback Plan)

---

**Last Updated**: 2025-10-05
**Version**: 1.0
**For**: PaperezMCP → SourceCrate (or any rebrand)
