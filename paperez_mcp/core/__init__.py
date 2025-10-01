"""
Core business logic for PaperezMCP.

This module contains the core functionality that can be used by both
the MCP server (stdio) and the HTTP server (REST API).

Architecture:
- search.py: Core search and browse functionality
- download.py: Core paper download functionality
- pdf_conversion.py: Core PDF processing functionality
- status.py: Core status and help functionality

All functions in this module are protocol-agnostic and can be called
from any interface (MCP, HTTP, CLI, etc.).
"""

from paperez_mcp.core.download import download_papers_core
from paperez_mcp.core.pdf_conversion import (
    batch_convert_pdfs_core,
    convert_pdf_to_markdown_core,
    convert_pdf_to_text_core,
)
from paperez_mcp.core.search import browse_papers_core, browse_papers_streaming_core
from paperez_mcp.core.status import get_help_core, get_status_core

__all__ = [
    "browse_papers_core",
    "browse_papers_streaming_core",
    "download_papers_core",
    "convert_pdf_to_text_core",
    "convert_pdf_to_markdown_core",
    "batch_convert_pdfs_core",
    "get_status_core",
    "get_help_core",
]
