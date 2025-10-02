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
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
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

# Import reliability tracking
from paperez_mcp.utils.download_reliability import (
    get_domain,
    get_download_reliability,
    record_download_attempt,
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
            "proxy_download": "GET /api/v1/proxy-download",
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

    Note: This returns a single aggregated response. For true progressive
    streaming in browsers, use GET /api/v1/search/stream instead.
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


@app.get("/api/v1/search/stream")
async def search_papers_sse(
    query: str,
    limit: int = 10,
    force_category: str | None = None,
    debug: bool = False,
) -> StreamingResponse:
    """
    Search academic papers with true Server-Sent Events (SSE) streaming.

    This endpoint provides real-time progressive updates as each source completes,
    delivering results incrementally instead of waiting for all sources.

    **Benefits:**
    - Papers appear progressively as sources complete (2-5 seconds for first results)
    - Real-time progress updates showing which sources are being searched
    - Live result count and source completion status
    - Better perceived performance vs waiting for all sources

    **Event types:**
    - `search_start`: Search initiated with query details
    - `source_start`: A source has started searching
    - `results`: New papers found from a source
    - `source_complete`: A source finished (with count)
    - `progress`: Overall progress update
    - `complete`: Search finished with final stats
    - `error`: Error occurred (continues searching other sources)

    **Usage:**
    ```javascript
    const eventSource = new EventSource(`/api/v1/search/stream?query=machine+learning&limit=10`);
    eventSource.addEventListener('results', (e) => {
        const data = JSON.parse(e.data);
        // Add data.papers to UI
    });
    eventSource.addEventListener('complete', (e) => {
        eventSource.close();
    });
    ```

    Args:
        query: Search query (keywords, DOI, author, title)
        limit: Maximum number of results (default: 10)
        force_category: Force specific source category (optional)
        debug: Include diagnostic information (default: False)

    Returns:
        StreamingResponse with text/event-stream content type
    """

    async def event_generator() -> AsyncIterator[str]:
        """Generate Server-Sent Events for progressive search results."""
        import json
        import time

        try:
            # Send search start event
            yield f"event: search_start\ndata: {json.dumps({'query': query, 'limit': limit, 'timestamp': time.time()})}\n\n"

            # Get search functions and API status
            from paperez_mcp.server import _lazy_import_search_functions, get_api_status
            from paperez_mcp.utils.result_streaming import (
                create_streaming_search,
                result_streamer,
            )

            # CRITICAL: Reset streaming state for each new request to prevent cache pollution
            # This ensures results from previous searches don't leak into new searches
            result_streamer.reset_streaming_state()
            logger.info(f"🔄 Reset streaming state for new search: query='{query}'")

            search_funcs = _lazy_import_search_functions()
            if not search_funcs:
                yield f"event: error\ndata: {json.dumps({'error': 'No search functions available'})}\n\n"
                return

            api_status = get_api_status()

            # Filter sources by category if specified
            if force_category:
                from paperez_mcp.config import get_current_config

                config = get_current_config()
                category_config = config.categories.get(force_category)
                if category_config:
                    allowed_sources = set(category_config.sources)
                    search_funcs = {
                        k: v for k, v in search_funcs.items() if k in allowed_sources
                    }

            # Track results
            all_results = []
            sources_completed = 0
            total_sources = len(search_funcs)
            delivered_result_ids: set[int] = (
                set()
            )  # Track delivered results to avoid duplicates

            # Stream results as they arrive
            async for update in create_streaming_search(
                search_functions=search_funcs,
                query=query,
                limit=limit,
                api_status=api_status,
            ):
                update_type = update.type

                if update_type == "result":
                    # Early delivery - sorted top results
                    if update.results:
                        for result in update.results:
                            result_id = id(result.data)
                            if result_id not in delivered_result_ids:
                                all_results.append(result.data)
                                delivered_result_ids.add(result_id)
                                yield f"event: results\ndata: {json.dumps({'source': result.source, 'papers': [result.data], 'total_so_far': len(all_results)})}\n\n"

                elif update_type == "source_complete":
                    # Source finished - only send notification (sorted results delivered via "result" and "final" updates)
                    sources_completed += 1
                    source_name = update.source

                    # Send source completion notification
                    result_count = (
                        len(result_streamer.source_results.get(source_name, []))
                        if source_name
                        else 0
                    )
                    yield f"event: source_complete\ndata: {json.dumps({'source': source_name, 'count': result_count, 'completed': sources_completed, 'total': total_sources})}\n\n"

                    # Send progress update
                    if total_sources > 0:
                        progress_pct = (sources_completed / total_sources) * 100
                        yield f"event: progress\ndata: {json.dumps({'completed': sources_completed, 'total': total_sources, 'percentage': progress_pct, 'results_count': len(all_results)})}\n\n"

                elif update_type == "error":
                    # Source error (non-fatal, continue with other sources)
                    error_msg = update.error or "Unknown error"
                    yield f"event: error\ndata: {json.dumps({'source': update.source, 'error': error_msg, 'fatal': False})}\n\n"

                elif update_type == "final":
                    # All sources complete - send any remaining results
                    if update.results:
                        for result in update.results:
                            result_id = id(result.data)
                            if result_id not in delivered_result_ids:
                                all_results.append(result.data)
                                delivered_result_ids.add(result_id)
                                yield f"event: results\ndata: {json.dumps({'source': result.source, 'papers': [result.data], 'total_so_far': len(all_results)})}\n\n"
                    break

            # Send completion event
            yield f"event: complete\ndata: {json.dumps({'total_results': len(all_results), 'sources_searched': total_sources, 'query': query, 'timestamp': time.time()})}\n\n"

        except Exception as e:
            logger.error(f"SSE streaming error: {e}")
            import traceback

            traceback.print_exc()
            yield f"event: error\ndata: {json.dumps({'error': str(e), 'fatal': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


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
async def get_status(
    force_reload: bool = False, active_health_check: bool = False
) -> dict[str, Any]:
    """
    Get comprehensive system status.

    Returns API health, configuration details, cache stats, and performance metrics.

    Args:
        force_reload: Force reload configuration
        active_health_check: Perform real-time health checks on all sources (30+ seconds).
                            Default False returns instant cached metrics.
    """
    try:
        result = await get_status_core(
            force_reload=force_reload, active_health_check=active_health_check
        )
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


@app.get("/api/v1/proxy-download")
async def proxy_download(url: str, filename: str | None = None) -> StreamingResponse:
    """
    Proxy download endpoint - fetches PDF from external source and streams it with download headers.

    This ensures PDFs are downloaded rather than displayed in browser, regardless of source CORS policies.

    Args:
        url: The external PDF URL to download
        filename: Optional filename for the download (defaults to 'paper.pdf')

    Returns:
        StreamingResponse with Content-Disposition: attachment header
    """
    try:
        # Validate URL
        if not url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Invalid URL protocol")

        # Default filename if not provided
        if not filename:
            filename = "paper.pdf"

        logger.info(f"Proxying download: {url} -> {filename}")

        # Adaptive retry strategy for handling publisher restrictions
        from urllib.parse import urlparse, urlunparse

        parsed_url = urlparse(url)

        # Strategy 1: Try with browser-like headers and HTTPS upgrade if needed
        def build_request_headers(referer_url: str) -> dict[str, str]:
            """Build comprehensive browser-like headers."""
            return {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/pdf,application/x-pdf,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": referer_url,
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0",
            }

        # Automatically upgrade HTTP to HTTPS (most publishers require it)
        if parsed_url.scheme == "http":
            logger.info(f"Auto-upgrading HTTP to HTTPS for {parsed_url.hostname}")
            parsed_url = parsed_url._replace(scheme="https")
            url = urlunparse(parsed_url)

        referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"
        headers = build_request_headers(referer)

        # Try multiple strategies if we encounter 403 errors
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)

            # Strategy 2: If 403, try without query parameters (some publishers block versioned URLs)
            if response.status_code == 403 and parsed_url.query:
                logger.info(
                    f"Got 403, retrying without query parameters: {parsed_url.query}"
                )
                clean_url = urlunparse(parsed_url._replace(query="", fragment=""))
                response = await client.get(clean_url, headers=headers)
                if response.status_code == 200:
                    url = clean_url  # Update URL for logging

            # Strategy 3: If still 403, try with minimal headers (some sites block Sec-Fetch headers)
            if response.status_code == 403:
                logger.info("Got 403, retrying with minimal headers")
                minimal_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "*/*",
                }
                response = await client.get(url, headers=minimal_headers)

            if response.status_code != 200:
                logger.warning(f"PDF fetch failed: {response.status_code} for {url}")
                record_download_attempt(url, success=False)
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch PDF from source: HTTP {response.status_code}",
                )

            # Success - record it
            record_download_attempt(url, success=True)

            # Stream the PDF back with download headers
            return StreamingResponse(
                iter([response.content]),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{quote(filename)}"',
                    "Content-Length": str(len(response.content)),
                },
            )

    except httpx.TimeoutException:
        logger.error(f"Timeout downloading PDF: {url}")
        record_download_attempt(url, success=False)
        raise HTTPException(status_code=504, detail="Timeout downloading PDF") from None
    except httpx.HTTPError as e:
        logger.error(f"HTTP error downloading PDF: {e}")
        record_download_attempt(url, success=False)
        raise HTTPException(
            status_code=502, detail=f"Error fetching PDF: {str(e)}"
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in proxy download: {e}")
        record_download_attempt(url, success=False)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/download-reliability")
async def check_download_reliability(url: str) -> dict[str, Any]:
    """
    Get download reliability metadata (stateless, optimistic response).

    ARCHITECTURE NOTE:
    This endpoint no longer tracks server-side statistics. For scalability to 1M users,
    clients should implement their own download tracking using localStorage or similar:

    ```javascript
    // Client-side tracking example:
    const domain = new URL(pdfUrl).hostname;
    const stats = JSON.parse(localStorage.getItem(`dl_${domain}`)) || {attempts: 0, successes: 0};

    // After download attempt:
    stats.attempts++;
    if (success) stats.successes++;
    stats.success_rate = stats.successes / stats.attempts;
    localStorage.setItem(`dl_${domain}`, JSON.stringify(stats));

    // Use stats.success_rate to show warnings in UI
    ```

    Args:
        url: PDF URL to check

    Returns:
        - status: Always "downloadable" (optimistic, client should track)
        - stats: Empty stats (no server-side tracking)
        - message: User-friendly description
        - domain: Extracted domain for client-side tracking key
    """
    try:
        status, stats = get_download_reliability(url)
        domain = get_domain(url)

        return {
            "url": url,
            "domain": domain,  # For client-side tracking key
            "status": status,
            "stats": stats,
            "message": "PDF should download successfully (client should track reliability)",
        }
    except Exception as e:
        logger.error(f"Error checking download reliability: {e}")
        return {
            "url": url,
            "domain": "unknown",
            "status": "downloadable",
            "stats": {"attempts": 0, "successes": 0, "success_rate": 0.0},
            "message": "PDF should download successfully",
        }


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
