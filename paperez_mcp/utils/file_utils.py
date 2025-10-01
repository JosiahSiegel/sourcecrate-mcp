"""
File utilities for downloading PDFs and saving markdown files.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


async def download_pdf(
    pdf_url: str,
    output_dir: str = ".paperez",
    title: str | None = None,
    paper_url: str | None = None,
    doi: str | None = None,
) -> dict[str, Any]:
    """
    Download a PDF from URL to local directory with enhanced headers and retry logic.

    Implements intelligent fallback chain:
    1. Try direct HTTP download with multiple header strategies
    2. If blocked by Cloudflare/403 → try Unpaywall for open access version
    3. If still fails → provide helpful error with manual alternatives

    Args:
        pdf_url: URL of the PDF to download
        output_dir: Directory to save the PDF
        title: Optional paper title for readable filename
        paper_url: Optional main paper URL for referrer header
        doi: Optional DOI for Unpaywall fallback

    Returns:
        Dictionary with download results
    """
    try:
        # Apply URL transformations and rate limiting based on configuration
        try:
            from paperez_mcp.config import get_current_config

            config = get_current_config()

            # Check each configured source for URL transformation rules
            for source_name, source_config in config.sources.items():
                if not source_config.enabled or not source_config.config:
                    continue

                # Check if this URL matches this source's patterns
                if source_name in pdf_url or (
                    source_config.config.get("url_patterns")
                    and any(
                        pattern in pdf_url
                        for pattern in source_config.config.get("url_patterns", [])
                    )
                ):

                    # Apply PDF URL transformation if configured
                    if source_config.config.get("pdf_url_transform"):
                        transform = source_config.config["pdf_url_transform"]
                        # Simple string replacement transformations
                        for old_val, new_val in transform.items():
                            pdf_url = pdf_url.replace(old_val, new_val)
                        logger.info(
                            f"Transformed PDF URL using {source_name} config: {pdf_url}"
                        )

                    # Apply rate limiting if configured
                    rate_limit_seconds = source_config.config.get(
                        "rate_limit_seconds", 0
                    )
                    if rate_limit_seconds > 0:
                        import asyncio

                        logger.info(
                            f"Applying {rate_limit_seconds}s rate limit for {source_name} PDF download"
                        )
                        await asyncio.sleep(rate_limit_seconds)
                    break
        except Exception as e:
            logger.debug(f"Could not apply config transformations: {e}")
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename - prefer title, fallback to technical ID
        if title:
            # Use paper title for readable filename
            filename = title[:50]  # Truncate to reasonable length
            filename = "".join(
                c for c in filename if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            filename = re.sub(r"\s+", " ", filename)  # Normalize whitespace
            if not filename:  # If title sanitization results in empty string
                filename = "unknown_paper"
        else:
            # Fallback to technical ID extraction
            paper_id = None
            if "arxiv.org" in pdf_url:
                # Extract arXiv ID
                match = re.search(r"(\d{4}\.\d{4,5})", pdf_url)
                if match:
                    paper_id = f"arxiv_{match.group(1)}"
            elif "doi.org" in pdf_url:
                # Extract DOI
                match = re.search(r"10\.\d+/(.+)", pdf_url)
                if match:
                    paper_id = f"doi_{match.group(1).replace('/', '_')}"

            if not paper_id:
                # Use URL path as fallback
                parsed = urlparse(pdf_url)
                paper_id = Path(parsed.path).stem or "unknown_paper"

            # Clean filename
            filename = re.sub(r"[^\w\-_\.]", "_", paper_id)

        pdf_path = os.path.join(output_dir, f"{filename}.pdf")

        # Enhanced browser headers to avoid 403 errors
        headers: dict[str, str | None] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/octet-stream,*/*;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Cache-Control": "max-age=0",
        }

        # Add referrer header if paper URL is provided
        if paper_url:
            headers["Referer"] = paper_url

        # Retry mechanism with different strategies
        max_retries = 3
        retry_strategies: list[dict[str, str | None]] = [
            # Strategy 1: Standard browser headers
            headers,
            # Strategy 2: Minimal headers (some sites block too many headers)
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/pdf,*/*;q=0.8",
                "Referer": paper_url if paper_url else None,
            },
            # Strategy 3: Basic headers only
            {
                "User-Agent": "Mozilla/5.0 (compatible; Academic Research Bot)",
                "Accept": "*/*",
            },
        ]

        last_error = None
        last_response = None

        for attempt in range(max_retries):
            # Remove None values from headers
            current_headers = {
                k: v for k, v in retry_strategies[attempt].items() if v is not None
            }

            try:
                async with httpx.AsyncClient(
                    timeout=60.0, follow_redirects=True, headers=current_headers
                ) as client:
                    response = await client.get(pdf_url)
                    last_response = response  # Save for Cloudflare detection

                    if response.status_code == 200:
                        with open(pdf_path, "wb") as f:
                            f.write(response.content)

                        return {
                            "success": True,
                            "pdf_path": pdf_path,
                            "file_size": len(response.content),
                            "filename": filename,
                            "retry_attempt": attempt + 1,
                            "headers_used": list(current_headers.keys()),
                        }
                    else:
                        last_error = f"HTTP {response.status_code}"
                        if attempt < max_retries - 1:
                            # Wait before retry (exponential backoff)
                            import asyncio

                            await asyncio.sleep(2**attempt)
                        continue

            except Exception as e:
                last_error = str(e)
                if attempt < max_retries - 1:
                    import asyncio

                    await asyncio.sleep(2**attempt)
                continue

        # All direct download retries failed - try fallback strategies
        logger.warning(
            f"❌ Direct download failed after {max_retries} attempts: {last_error}"
        )

        # Check if failure is due to Cloudflare/access control
        from paperez_mcp.utils.cloudflare_detector import (
            get_cloudflare_info,
            suggest_alternatives,
        )

        is_cloudflare = False
        if last_response:
            cf_info = get_cloudflare_info(last_response)
            is_cloudflare = cf_info["is_cloudflare"]
            if is_cloudflare:
                logger.info(
                    f"🛡️  Cloudflare protection detected: {cf_info['likely_reason']}"
                )

        # Try Unpaywall fallback if DOI is available
        unpaywall_tried = False
        if doi and (is_cloudflare or "403" in str(last_error)):
            logger.info(f"🔄 Trying Unpaywall fallback for DOI: {doi}")
            from paperez_mcp.utils.unpaywall_client import get_unpaywall_client

            unpaywall_client = get_unpaywall_client()
            oa_info = await unpaywall_client.find_open_access_pdf(doi)

            unpaywall_tried = True

            if oa_info and oa_info.get("is_oa"):
                best_location = oa_info["best_oa_location"]
                oa_pdf_url = best_location.get("url_for_pdf")

                if oa_pdf_url:
                    logger.info(f"✅ Found open access PDF via Unpaywall: {oa_pdf_url}")

                    # Try downloading from open access URL
                    try:
                        async with httpx.AsyncClient(
                            timeout=60.0, follow_redirects=True
                        ) as client:
                            response = await client.get(oa_pdf_url)

                            if response.status_code == 200:
                                with open(pdf_path, "wb") as f:
                                    f.write(response.content)

                                return {
                                    "success": True,
                                    "pdf_path": pdf_path,
                                    "file_size": len(response.content),
                                    "filename": filename,
                                    "source": "unpaywall",
                                    "oa_version": best_location.get("version"),
                                    "oa_license": best_location.get("license"),
                                }
                    except Exception as e:
                        logger.warning(f"❌ Unpaywall download also failed: {e}")

        # All strategies failed - provide helpful error
        error_msg = f"Failed to download PDF after {max_retries} attempts: {last_error}"
        suggestions = suggest_alternatives(pdf_url, doi)

        return {
            "success": False,
            "error": error_msg,
            "pdf_url": pdf_url,
            "final_attempt": max_retries,
            "cloudflare_detected": is_cloudflare,
            "unpaywall_tried": unpaywall_tried,
            "suggestions": suggestions,
        }

    except Exception as e:
        return {"success": False, "error": f"Download failed: {str(e)}"}


def save_markdown_file(markdown_content: str, file_path: str) -> dict[str, Any]:
    """
    Save markdown content to file.

    Args:
        markdown_content: The markdown text to save
        file_path: Path where to save the file

    Returns:
        Dictionary with save results
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save markdown
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return {
            "success": True,
            "markdown_path": file_path,
            "markdown_characters": len(markdown_content),
        }

    except Exception as e:
        return {"success": False, "error": f"Failed to save markdown: {str(e)}"}
