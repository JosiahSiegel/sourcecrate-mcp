#!/usr/bin/env python3
"""
PaperezMCP HTTP Server - REST API for Academic Paper Research

This HTTP server exposes the same functionality as the MCP server via REST API,
allowing browser-based and HTTP-based clients to access PaperezMCP.

All 8 core functions are available:
- POST /api/v1/search - Browse papers (metadata only)
- POST /api/v1/search/streaming - Streaming search
- POST /api/v1/download - Download papers
- POST /api/v1/convert/pdf-to-text - Convert PDF to text
- POST /api/v1/convert/pdf-to-markdown - Convert PDF to markdown
- POST /api/v1/convert/batch - Batch convert PDFs
- GET /api/v1/status - System status
- GET /api/v1/help - Configuration help

Usage:
    python -m paperez_mcp.http_server
    # or
    paperez-http  (if installed)

The server runs on http://localhost:8000 by default.
OpenAPI docs available at http://localhost:8000/docs
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import core business logic
from paperez_mcp.core import (
    batch_convert_pdfs_core,
    browse_papers_core,
    browse_papers_streaming_core,
    convert_pdf_to_markdown_core,
    convert_pdf_to_text_core,
    download_papers_core,
    get_help_core,
    get_status_core,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PaperezMCP HTTP API",
    description="Academic paper research made easy - REST API for searching, downloading, and converting research papers",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Request/Response Models ====================


class SearchRequest(BaseModel):
    """Request model for paper search"""

    query: str = Field(..., description="Search query (keywords, DOI, author, title)")
    limit: int = Field(10, ge=1, le=50, description="Maximum number of results")
    force_category: str | None = Field(
        None, description="Force specific source category"
    )
    debug: bool = Field(False, description="Include diagnostic information")


class DownloadRequest(BaseModel):
    """Request model for paper download"""

    query: str = Field(..., description="Search query (keywords, DOI, author, title)")
    limit: int = Field(5, ge=1, le=20, description="Maximum papers to download")
    output_dir: str = Field(".paperez", description="Output directory for files")
    force_category: str | None = Field(
        None, description="Force specific source category"
    )
    convert_to_markdown: bool = Field(
        True, description="Convert PDFs to markdown (vs keep as PDF)"
    )
    debug: bool = Field(False, description="Include diagnostic information")


class ConvertPdfToTextRequest(BaseModel):
    """Request model for PDF to text conversion"""

    file_path: str = Field(..., description="Path to local PDF file")
    output_path: str | None = Field(None, description="Output path for text file")
    title: str = Field("", description="Document title for header")
    authors: list[str] | None = Field(None, description="List of authors")


class ConvertPdfToMarkdownRequest(BaseModel):
    """Request model for PDF to markdown conversion"""

    file_path: str = Field(..., description="Path to local PDF file")
    title: str = Field("", description="Document title for header")
    authors: list[str] | None = Field(None, description="List of authors")
    output_path: str | None = Field(None, description="Output path for markdown file")


class BatchConvertRequest(BaseModel):
    """Request model for batch PDF conversion"""

    directory: str = Field("articles", description="Directory containing PDFs")
    output_dir: str | None = Field(None, description="Output directory for markdown")


class StatusRequest(BaseModel):
    """Request model for system status"""

    force_reload: bool = Field(False, description="Force reload configuration")


# ==================== API Endpoints ====================


@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint with API information"""
    return {
        "service": "PaperezMCP HTTP API",
        "version": "1.1.0",
        "description": "Academic paper research made easy",
        "docs": "/docs",
        "endpoints": {
            "search": "POST /api/v1/search",
            "search_streaming": "POST /api/v1/search/streaming",
            "download": "POST /api/v1/download",
            "convert_pdf_to_text": "POST /api/v1/convert/pdf-to-text",
            "convert_pdf_to_markdown": "POST /api/v1/convert/pdf-to-markdown",
            "batch_convert": "POST /api/v1/convert/batch",
            "status": "GET /api/v1/status",
            "help": "GET /api/v1/help",
        },
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "paperez-mcp"}


@app.post("/api/v1/search")
async def search_papers(request: SearchRequest) -> dict[str, Any]:
    """
    Search academic papers and return metadata/abstracts.

    Returns titles, authors, abstracts, DOIs, and PDF URLs.
    Does not download full papers - use /api/v1/download for that.
    """
    try:
        logger.info(f"Search request: query='{request.query}', limit={request.limit}")
        result = await browse_papers_core(
            query=request.query,
            limit=request.limit,
            force_category=request.force_category,
            debug=request.debug,
        )
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/search/streaming")
async def search_papers_streaming(request: SearchRequest) -> dict[str, Any]:
    """
    Search academic papers with real-time streaming as sources complete.

    Returns results incrementally as each source completes, providing
    faster initial response times and real-time progress updates.
    """
    try:
        logger.info(
            f"Streaming search request: query='{request.query}', limit={request.limit}"
        )
        result = await browse_papers_streaming_core(
            query=request.query,
            limit=request.limit,
            force_category=request.force_category,
            debug=request.debug,
        )
        return result
    except Exception as e:
        logger.error(f"Streaming search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/download")
async def download_papers(request: DownloadRequest) -> dict[str, Any]:
    """
    Download academic papers and convert to markdown/PDF.

    Downloads full papers, saves them to files, and optionally converts to markdown.
    Returns local file paths - files are saved on the server.
    """
    try:
        logger.info(f"Download request: query='{request.query}', limit={request.limit}")
        result = await download_papers_core(
            query=request.query,
            limit=request.limit,
            output_dir=request.output_dir,
            force_category=request.force_category,
            convert_to_markdown=request.convert_to_markdown,
            debug=request.debug,
        )
        return result
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/convert/pdf-to-text")
async def convert_pdf_to_text(request: ConvertPdfToTextRequest) -> dict[str, Any]:
    """
    Convert a local PDF file to plain text.

    Extracts text from PDF and saves to .txt file.
    File must exist on server filesystem.
    """
    try:
        # Validate file exists
        if not Path(request.file_path).exists():
            raise HTTPException(status_code=404, detail="PDF file not found")

        logger.info(f"PDF to text conversion: {request.file_path}")
        result = await convert_pdf_to_text_core(
            file_path=request.file_path,
            output_path=request.output_path,
            title=request.title,
            authors=request.authors,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF to text conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/convert/pdf-to-markdown")
async def convert_pdf_to_markdown(
    request: ConvertPdfToMarkdownRequest,
) -> dict[str, Any]:
    """
    Convert a local PDF file to formatted markdown.

    Uses pymupdf4llm for zero-token conversion preserving document structure.
    File must exist on server filesystem.
    """
    try:
        # Validate file exists
        if not Path(request.file_path).exists():
            raise HTTPException(status_code=404, detail="PDF file not found")

        logger.info(f"PDF to markdown conversion: {request.file_path}")
        result = await convert_pdf_to_markdown_core(
            file_path=request.file_path,
            title=request.title,
            authors=request.authors,
            output_path=request.output_path,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF to markdown conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/convert/batch")
async def batch_convert_pdfs(request: BatchConvertRequest) -> dict[str, Any]:
    """
    Convert all PDFs in a directory to markdown format.

    Processes entire directories of PDFs in batch.
    Directory must exist on server filesystem.
    """
    try:
        # Validate directory exists
        if not Path(request.directory).exists():
            raise HTTPException(status_code=404, detail="Directory not found")

        logger.info(f"Batch PDF conversion: {request.directory}")
        result = await batch_convert_pdfs_core(
            directory=request.directory, output_dir=request.output_dir
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch conversion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/status")
async def get_status(force_reload: bool = False) -> dict[str, Any]:
    """
    Get comprehensive system status.

    Returns API health, configuration details, cache stats, and performance metrics.
    """
    try:
        result = await get_status_core(force_reload=force_reload)
        return result
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/help")
async def get_help() -> dict[str, Any]:
    """
    Get configuration guidance and help.

    Returns comprehensive instructions on how to configure PaperezMCP,
    including file paths, schemas, and examples.
    """
    try:
        result = await get_help_core()
        return result
    except Exception as e:
        logger.error(f"Help retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# ==================== Error Handlers ====================


@app.exception_handler(404)
async def not_found_handler(request: Any, exc: Any) -> JSONResponse:
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "detail": "The requested resource was not found",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Any, exc: Any) -> JSONResponse:
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
        },
    )


# ==================== Main Entry Point ====================


def main() -> None:
    """Main entry point for HTTP server"""
    import uvicorn

    logger.info("Starting PaperezMCP HTTP server...")
    logger.info("OpenAPI docs: http://localhost:8000/docs")
    logger.info("ReDoc docs: http://localhost:8000/redoc")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
