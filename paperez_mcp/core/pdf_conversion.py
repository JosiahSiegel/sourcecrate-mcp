"""
Core PDF conversion functionality for PaperezMCP.

This module contains protocol-agnostic PDF processing functions that can be called
from any interface (MCP, HTTP, CLI, etc.).

Note: Currently these are wrappers that delegate to the implementations in server.py.
Future refactoring will move the full implementation here.
"""

import logging
from typing import Any, cast

logger = logging.getLogger(__name__)


async def convert_pdf_to_text_core(
    file_path: str,
    output_path: str | None = None,
    title: str = "",
    authors: list[str] | None = None,
) -> dict[str, Any]:
    """
    Convert a local PDF file to plain text.

    Args:
        file_path: Path to local PDF file
        output_path: Output path for text file (default: auto-generated)
        title: Optional document title for header
        authors: Optional list of authors for header

    Returns:
        Dict containing:
        - success: Boolean indicating if extraction succeeded
        - text_path: Path to saved text file
        - text_length: Character count of extracted text
        - original_file: Original PDF file path
        - pages_extracted: Number of pages processed
    """
    # Import here to avoid circular dependencies
    from paperez_mcp import server

    # Access the underlying function from the FunctionTool wrapper
    result = await server.convert_pdf_to_text.fn(file_path, output_path, title, authors)
    return cast(dict[str, Any], result)


async def convert_pdf_to_markdown_core(
    file_path: str,
    title: str = "",
    authors: list[str] | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    """
    Convert a local PDF file to formatted markdown.

    Uses pymupdf4llm for zero-token conversion preserving document structure.

    Args:
        file_path: Path to the PDF file to convert
        title: Optional title for the document header
        authors: Optional list of authors for the document header
        output_path: Output path for markdown file (default: auto-generated)

    Returns:
        Dict containing:
        - success: Boolean indicating if conversion succeeded
        - markdown_length: Character count of markdown content
        - markdown_path: Path to saved markdown file
        - original_file: Original PDF file path
        - pages_extracted: Number of pages processed
    """
    # Import here to avoid circular dependencies
    from paperez_mcp import server

    # Access the underlying function from the FunctionTool wrapper
    result = await server.convert_pdf_to_markdown.fn(
        file_path, title, authors, output_path
    )
    return cast(dict[str, Any], result)


async def batch_convert_pdfs_core(
    directory: str = "articles", output_dir: str | None = None
) -> dict[str, Any]:
    """
    Convert all PDFs in a directory to markdown format.

    Uses zero AI tokens - employs pymupdf4llm for direct PDF-to-markdown conversion.

    Args:
        directory: Directory containing PDFs (default: "articles")
        output_dir: Output directory for markdown files (default: current directory)

    Returns:
        Dict containing:
        - success: Boolean indicating overall batch operation success
        - directory: Input directory path that was processed
        - output_directory: Output directory where files were saved
        - total_files: Total number of PDF files found
        - successful_conversions: Number of PDFs successfully converted
        - failed_conversions: Number of PDFs that failed to convert
        - files: List of conversion results for each file
    """
    # Import here to avoid circular dependencies
    from paperez_mcp import server

    # Access the underlying function from the FunctionTool wrapper
    result = await server.batch_convert_pdfs.fn(directory, output_dir)
    return cast(dict[str, Any], result)
