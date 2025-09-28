# Validation System

## Overview

This repository uses a comprehensive shared validation system that ensures identical checks between local development and CI environments. **All validation checks are mandatory** - there are no optional checks or warnings that allow broken code to pass.

## Shared Validation Scripts

All validation is performed using shared scripts in the `scripts/` directory:

- **`scripts/validate_dependencies.py`** - Validates ALL dependencies (core, PDF, dev)
- **`scripts/validate_imports.py`** - Tests imports and MCP server structure
- **`scripts/validate_code_quality.py`** - Runs syntax, ruff, mypy, black checks
- **`scripts/validate_all.py`** - Master script that runs all validations

## Required Dependencies

### Core Dependencies
```bash
pip install fastmcp scholarly httpx aiohttp requests tenacity diskcache asyncio-throttle fake-useragent arxiv pymed semanticscholar free-proxy
```

### PDF Processing Dependencies
```bash
pip install PyMuPDF pymupdf4llm pdfplumber lxml beautifulsoup4
```

### Development Dependencies
```bash
pip install pytest pytest-asyncio black ruff mypy types-PyYAML types-requests types-beautifulsoup4
```

## Validation Checks

### 1. Dependency Validation
- **ALL** core dependencies must be installed
- **ALL** PDF processing dependencies must be installed
- **ALL** development dependencies must be installed
- **NO** optional dependencies - everything is required

### 2. Import & Structure Validation
- All core modules must import successfully
- Configuration system must load properly
- All 7 MCP tools must be available and structured correctly

### 3. Code Quality Validation
- **Python syntax** must be valid for all `.py` files
- **Ruff linting** must pass with zero issues
- **MyPy type checking** must pass with zero errors
- **Black formatting** must be correct

## Precommit Hook Behavior

The precommit hook runs `scripts/validate_all.py` which performs ALL validation checks:

```bash
# This runs automatically on git commit
python3 scripts/validate_all.py
```

**If ANY validation check fails, the commit is rejected.**

## CI Workflow Behavior

The CI workflow uses the same validation scripts to ensure identical behavior:

```yaml
- name: Validate dependencies using shared script
  run: python scripts/validate_dependencies.py

- name: Validate imports and functionality using shared script
  run: python scripts/validate_imports.py

- name: Validate code quality using shared script
  run: python scripts/validate_code_quality.py
```

## Benefits

✅ **No false positives** - If validation passes locally, it passes in CI
✅ **No missing dependencies** - All required packages are checked
✅ **No formatting issues** - Black formatting is enforced
✅ **No type errors** - MyPy checking is mandatory
✅ **No linting issues** - Ruff linting must pass
✅ **Consistent environments** - Local and CI use identical validation

## Troubleshooting

### Missing Dependencies
```bash
❌ Missing required core dependencies: free-proxy
Install with: pip install free-proxy
```

### Black Formatting Issues
```bash
❌ Black formatting issues found:
Run 'black paperez_mcp/ scripts/' to fix formatting
```

### Ruff Linting Issues
```bash
❌ Ruff linting failed!
Run 'ruff check paperez_mcp/ --fix' to auto-fix issues
```

### MyPy Type Issues
```bash
❌ MyPy type checking failed!
Run 'mypy paperez_mcp/ --ignore-missing-imports' to see details
```

## Manual Validation

Run validation manually at any time:

```bash
# Run all validations
python3 scripts/validate_all.py

# Run individual validations
python3 scripts/validate_dependencies.py
python3 scripts/validate_imports.py
python3 scripts/validate_code_quality.py
```

This strict validation system ensures high code quality and prevents issues from reaching production.