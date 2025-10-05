# MCP Server Validation Scripts

This directory contains validation scripts for the MCP server to ensure it builds and functions correctly.

## Scripts

### `simple_mcp_check.py`
Simple pre-commit validation script that checks:
- Python syntax compilation
- Basic import functionality
- Graceful handling of optional dependencies

Usage:
```bash
python3 scripts/simple_mcp_check.py
```

### `validate_mcp_server.py`
Comprehensive validation script that checks:
- Python syntax (AST parsing)
- Import resolution
- MCP server structure (decorators, async functions)

Usage:
```bash
python3 scripts/validate_mcp_server.py
```

## Pre-commit Integration

The validation is integrated with pre-commit hooks in `.pre-commit-config.yaml`:

1. **MCP Server Validation** - Runs on `sourcecrate_mcp_server.py` changes
2. **Python Syntax Check** - Runs on all `.py` files

### Setup Pre-commit

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

### Manual Testing

```bash
# Test MCP server validation
python3 scripts/simple_mcp_check.py

# Test syntax compilation
python3 -m py_compile sourcecrate_mcp_server.py
```

## What Gets Validated

- ✅ Python syntax errors
- ✅ Import statement validation
- ✅ MCP server can be imported
- ✅ Basic structure integrity
- ⚠️ Graceful handling of missing optional dependencies (fastmcp, scholarly, etc.)

## Integration with Git

These hooks automatically run before commits to prevent broken code from being committed to the repository.