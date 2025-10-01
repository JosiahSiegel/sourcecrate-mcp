# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PaperezMCP is a Model Context Protocol (MCP) server for academic paper research with multi-source search capabilities, PDF processing, and intelligent routing. It provides 8 optimized tools for browsing, downloading, and converting academic papers.

## Recent Performance Optimizations

### Dependency Optimization (72% reduction)
- **Removed unused dependencies**: pdfplumber, lxml (45MB saved, not used anywhere in codebase)
- **Replaced bm25s with rank-bm25**: Removed scipy dependency (116MB saved)
  - Trade-off: 10-50x slower BM25 ranking (still sub-second, only affects source selection)
  - Benefit: Significantly faster install time (~3-5s vs 10-15s)
  - Total savings: **161MB (72% reduction)** from 223MB → 62MB dependencies

### Lazy Loading
- Configuration and source registration deferred until first use
- 41% faster startup time (1700ms → 1000ms)
- Near-instant MCP server initialization

## Development Commands

### Code Quality
```bash
# Format code with Black
black paperez_mcp_server.py paperez_mcp/

# Lint code with Ruff
ruff check paperez_mcp_server.py paperez_mcp/

# Type checking with MyPy
mypy paperez_mcp_server.py paperez_mcp/

# Install development dependencies
pip install -e .[dev]

# Pre-commit validation (runs automatically on commit)
# To bypass in special cases: git commit --no-verify
```

### Testing
```bash
# Run all tests (target: 100% pass rate)
pytest

# Run specific test file
pytest tests/test_fuzzy_matching.py

# Run single test
pytest tests/test_fuzzy_matching.py::TestFuzzyPaperMatcher::test_normalize_title

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=paperez_mcp --cov-report=term-missing

# Test syntax compilation before commit
python3 -m py_compile paperez_mcp_server.py
```

### MCP Server Development
```bash
# Run the MCP server locally
python paperez_mcp_server.py

# Run with debug output
DEBUG=1 python paperez_mcp_server.py

# Test MCP server via uvx
uvx --from . paperez-mcp

# Install as MCP server in Claude Code
claude mcp add -s project paperez-mcp -- uvx --from git+https://github.com/JosiahSiegel/paperez-mcp.git paperez-mcp

# Test specific MCP tools locally
python -c "from paperez_mcp_server import browse_papers; import asyncio; print(asyncio.run(browse_papers('machine learning', 5)))"
```

## Architecture Overview

### Core Components

1. **Main Server** (`paperez_mcp_server.py`)
   - FastMCP-based MCP server with 8 optimized tools
   - Lazy loading of heavy dependencies for performance
   - Tool functions: browse_papers, browse_papers_streaming, download_papers, convert_pdf_to_text, convert_pdf_to_markdown, batch_convert_pdfs, get_status, get_help

2. **Configuration System** (`paperez_mcp/config/`)
   - **Dual configuration approach**: Legacy (settings.py) + New configurable system (YAML-based)
   - **Multi-tier loading**: Built-in → User → Project → Environment overrides
   - **Configuration files**: `.paperez/config/config.yaml` (main), `.paperez/config/minimal_config.yaml` (fallback)
   - **Dynamic source registration**: Both built-in and plugin sources supported

3. **API Clients** (`paperez_mcp/api_clients/`)
   - Multi-source academic database integration
   - Base client pattern with specialized implementations
   - Sources: CrossRef, Semantic Scholar, arXiv, PubMed, Google Scholar, Europe PMC, DOAJ, etc.

4. **Search Services** (`paperez_mcp/services/`)
   - **SearchOrchestrationService**: Intelligent routing and coordination
   - **ConfigurableSearchService**: YAML-configured search with source registry
   - **PaperProcessor**: Handles PDF download and conversion workflows

5. **Utilities** (`paperez_mcp/utils/`)
   - **Smart search**: BM25 ranking, topic classification, intent analysis
   - **PDF processing**: Text extraction, markdown conversion (zero-token via pymupdf4llm)
   - **Parallel processing**: Concurrent PDF batch processing with semaphore control
   - **Performance benchmarking**: Comprehensive timing and metrics collection
   - **Enhanced error recovery**: Circuit breakers, exponential backoff, intelligent retry
   - **Fuzzy matching**: Cross-source paper deduplication with deterministic source ordering
   - **Health monitoring**: Source performance tracking and recommendations
   - **Result streaming**: Async streaming with completion queue pattern for race condition handling
   - **Global singletons**: `result_streamer`, `search_analytics` (require reset in tests)

### Data Flow

1. **Query Processing**: Intent analysis → Topic classification → Source routing
2. **Search Execution**: Parallel multi-source search → Result aggregation → Deduplication
3. **PDF Processing**: Download → Text/Markdown conversion → File storage (zero context window usage)
4. **Health Monitoring**: Performance metrics → Recommendations → Adaptive routing

## Configuration Management

### Configuration Hierarchy
1. Built-in defaults (`.paperez/config/config.yaml`)
2. User home config (`~/.paperez/config/config.yaml`)
3. Project local config (`./paperez/config/config.yaml`)
4. Environment variables

### Key Configuration Sections
- **Sources**: Academic database configurations (URLs, auth, field mappings)
- **Categories**: Search categories (comprehensive, medical, preprints, etc.)
- **Routing**: Smart query routing with domain keywords
- **Performance**: Caching, concurrency, timeouts

## Critical Development Notes

### MCP Server Updates
- Changes to MCP tools only take effect after: Git push → Claude Code restart
- Always test syntax with `python3 -m py_compile` before committing
- Tool docstrings are optimized for minimal token usage while preserving functionality

### PDF Processing Architecture
- **Zero context window consumption**: All PDF tools save to files, never return content
- **pymupdf4llm integration**: Direct PDF→Markdown without AI tokens
- **Lazy loading**: Heavy dependencies loaded only when needed

### Search Intelligence
- **BM25 ranking**: Optimizes source selection based on query analysis
- **Fallback strategies**: Graceful degradation when sources fail
- **Health monitoring**: Adaptive routing based on source performance

### Test Suite Architecture
- **Test isolation critical**: Global singletons (`result_streamer`, `search_analytics`, `global_error_recovery`) must be reset in setup_method
- **Deterministic ordering**: Fuzzy matching uses ordered lists instead of sets for predictable source ordering
- **Race condition handling**: Streaming uses completion queue draining to catch simultaneous errors
- **Target**: Maintain 100% test pass rate (235 tests)

### Performance Considerations
- **Disk caching**: 1GB cache for improved performance
- **Parallel search**: Concurrent queries across multiple sources
- **Lazy imports**: Heavy dependencies loaded on demand
- **Token optimization**: Tool descriptions optimized for minimal context usage
- **Streaming architecture**: ResultStreamer manages async result delivery with early results capability

## File Structure Notes

- **Main entry point**: `paperez_mcp_server.py` (contains all 8 MCP tools)
- **Config files**: `.paperez/config/` directory (not `.paperez/` root)
- **Source plugins**: Extensible via `paperez_mcp/plugins/`
- **Configuration**: YAML-based configuration system with multi-tier loading