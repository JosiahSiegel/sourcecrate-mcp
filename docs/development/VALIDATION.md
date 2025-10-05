# Validation Guide

## Quick Validation
```bash
python3 scripts/validate_all.py
```

## Installing Dependencies in Restricted Environments

### Method 1: System Package Manager Override
```bash
pip install black ruff mypy pytest pytest-asyncio --break-system-packages
```

### Method 2: Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -e .[dev]
python3 scripts/validate_all.py
```

### Method 3: User Directory Installation
```bash
pip install --user black ruff mypy pytest pytest-asyncio
```

## Required Dependencies

### Development Tools
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support

### Core Dependencies
```bash
pip install fastmcp scholarly httpx aiohttp requests tenacity diskcache asyncio-throttle fake-useragent arxiv pymed semanticscholar free-proxy PyMuPDF pymupdf4llm pdfplumber lxml beautifulsoup4
```

**Note**: PyMuPDF is imported as `fitz` in Python code, not as `PyMuPDF`.

### Type Stubs
```bash
pip install types-PyYAML types-requests types-beautifulsoup4
```

## Individual Validation Commands

### Dependencies
```bash
python3 scripts/validate_dependencies.py
```

### Imports & Structure
```bash
python3 scripts/validate_imports.py
```

### Code Quality
```bash
python3 scripts/validate_code_quality.py
```

### Configuration Validation
```bash
python3 scripts/validate_configuration.py
```

### PDF Processing
```bash
python3 scripts/validate_pdf_processing.py
```

### MCP Server Functionality
```bash
python3 scripts/validate_mcp_server.py
```

## Manual Commands (if scripts fail)

### Syntax Check
```bash
python3 -m py_compile source_crate_server.py
python3 -c "import py_compile; [py_compile.compile(f, doraise=True) for f in __import__('pathlib').Path('source_crate').rglob('*.py')]"
```

### Linting
```bash
ruff check source_crate/
```

### Type Checking
```bash
mypy source_crate/ --ignore-missing-imports
```

### Formatting Check
```bash
black --check source_crate/ scripts/
```

### Auto-fix Formatting
```bash
black source_crate/ scripts/
```

## Troubleshooting

### "externally-managed-environment" Error
Use `--break-system-packages` or virtual environment.

### Import Errors
- Check dependency installation: `pip list | grep <package>`
- Verify Python path: `python3 -c "import sys; print(sys.path)"`

### Permission Errors
- Use `--user` flag for user installation
- Create virtual environment with `python3 -m venv`

## CI Integration

The validation scripts are used by:
- `.git/hooks/pre-commit` (local)
- `.github/workflows/test-mcp-install.yml` (CI)

Both environments run identical validation ensuring consistency.
