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
    debug: bool = False,
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
        debug: If True, return detailed diagnostic fields. If False (default), minimal output.

    Returns:
        Dictionary with download results (minimal in non-debug mode, detailed in debug mode)
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

                        result = {
                            "success": True,
                            "pdf_path": pdf_path,
                            "file_size": len(response.content),
                            "filename": filename,
                        }

                        # Add diagnostic fields only in debug mode
                        if debug:
                            result["retry_attempt"] = attempt + 1
                            result["headers_used"] = list(current_headers.keys())

                        return result
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

        # Debug: Log condition evaluation for Unpaywall fallback
        logger.info(
            f"🔍 Unpaywall condition check - DOI: {doi}, is_cloudflare: {is_cloudflare}, "
            f"last_error: {last_error}, last_response_status: {last_response.status_code if last_response else None}"
        )

        # Initialize Unpaywall diagnostic variables
        unpaywall_tried = False
        unpaywall_api_response = "not_tried"
        unpaywall_oa_url = None
        unpaywall_oa_version = None
        unpaywall_oa_license = None
        unpaywall_download_attempted = False
        unpaywall_download_status = None
        unpaywall_download_error = None
        unpaywall_alternatives_count = 0
        unpaywall_urls_tried = []

        # Try Unpaywall fallback if DOI is available
        if doi and (
            is_cloudflare
            or "403" in str(last_error)
            or "404" in str(last_error)
            or (last_response and last_response.status_code in [403, 404])
        ):
            logger.info(f"🔄 Trying Unpaywall fallback for DOI: {doi}")
            from paperez_mcp.utils.unpaywall_client import get_unpaywall_client

            unpaywall_client = get_unpaywall_client()
            oa_info = await unpaywall_client.find_open_access_pdf(doi)

            unpaywall_tried = True

            # Track API response type
            if oa_info is None:
                unpaywall_api_response = "api_error"
            elif oa_info.get("is_oa") is False:
                unpaywall_api_response = "no_oa"
            elif oa_info.get("is_oa") is True:
                unpaywall_api_response = "found_oa"

            if oa_info and oa_info.get("is_oa"):
                # Get ALL open access locations (not just best)
                all_oa_locations = oa_info.get("oa_locations", [])
                unpaywall_alternatives_count = len(all_oa_locations)

                logger.info(
                    f"🔄 Unpaywall found {unpaywall_alternatives_count} open access locations, trying each..."
                )

                # Try each location with enhanced headers
                for idx, location in enumerate(all_oa_locations):
                    oa_pdf_url = location.get("url_for_pdf")
                    oa_version = location.get("version")
                    oa_license = location.get("license")

                    if not oa_pdf_url:
                        # Log why this alternative is being skipped
                        logger.info(
                            f"  ⏭️  Skipping Unpaywall location {idx+1}: No url_for_pdf "
                            f"(has url: {location.get('url', 'N/A')}, version: {oa_version})"
                        )
                        continue

                    # Capture first location metadata for diagnostics
                    if idx == 0:
                        unpaywall_oa_url = oa_pdf_url
                        unpaywall_oa_version = oa_version
                        unpaywall_oa_license = oa_license

                    unpaywall_urls_tried.append(oa_pdf_url)
                    unpaywall_download_attempted = True

                    logger.info(
                        f"  Trying Unpaywall location {idx+1}/{unpaywall_alternatives_count}: {oa_pdf_url}"
                    )

                    # Enhanced browser-like headers (more realistic than basic httpx)
                    enhanced_headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "application/pdf,application/x-pdf,*/*",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Referer": paper_url if paper_url else pdf_url,
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Cache-Control": "max-age=0",
                    }

                    try:
                        async with httpx.AsyncClient(
                            timeout=60.0, follow_redirects=True
                        ) as client:
                            response = await client.get(
                                oa_pdf_url, headers=enhanced_headers
                            )
                            unpaywall_download_status = response.status_code

                            if response.status_code == 200:
                                with open(pdf_path, "wb") as f:
                                    f.write(response.content)

                                logger.info(
                                    f"✅ Success! Downloaded from Unpaywall location {idx+1}"
                                )

                                result = {
                                    "success": True,
                                    "pdf_path": pdf_path,
                                    "file_size": len(response.content),
                                    "filename": filename,
                                    "source": "unpaywall",
                                }

                                # Add diagnostic fields only in debug mode
                                if debug:
                                    result["oa_version"] = oa_version
                                    result["oa_license"] = oa_license
                                    result["unpaywall_location_index"] = idx + 1
                                    result["unpaywall_alternatives_tried"] = len(
                                        unpaywall_urls_tried
                                    )

                                return result
                            else:
                                unpaywall_download_error = (
                                    f"HTTP {response.status_code}"
                                )
                                logger.info(
                                    f"  ❌ Location {idx+1} failed: HTTP {response.status_code}"
                                )

                    except Exception as e:
                        unpaywall_download_error = str(e)
                        logger.warning(f"  ❌ Location {idx+1} failed: {e}")

                    # Add small delay before trying next URL (avoid rate limiting)
                    if idx < len(all_oa_locations) - 1:
                        import asyncio

                        await asyncio.sleep(0.5)

                # All Unpaywall locations failed
                logger.info(
                    f"❌ All {unpaywall_alternatives_count} Unpaywall locations failed"
                )

        # Log if Unpaywall was tried but didn't find open access version
        if unpaywall_tried and doi:
            logger.info(
                f"ℹ️  Unpaywall fallback completed for DOI: {doi} (no open access version found or download failed)"
            )

        # All strategies failed - provide helpful error
        error_msg = f"Failed to download PDF after {max_retries} attempts: {last_error}"

        # Collect Unpaywall URLs for manual download suggestions
        unpaywall_urls_for_suggestions = (
            unpaywall_urls_tried if unpaywall_urls_tried else []
        )

        suggestions = suggest_alternatives(pdf_url, doi, unpaywall_urls_for_suggestions)

        result = {
            "success": False,
            "error": error_msg,
        }

        # Add diagnostic fields only in debug mode
        if debug:
            result["pdf_url"] = pdf_url
            result["final_attempt"] = max_retries
            result["cloudflare_detected"] = is_cloudflare
            result["unpaywall_tried"] = unpaywall_tried
            result["suggestions"] = suggestions
            # Detailed Unpaywall diagnostics
            result["unpaywall_api_response"] = unpaywall_api_response
            result["unpaywall_oa_url"] = unpaywall_oa_url
            result["unpaywall_oa_version"] = unpaywall_oa_version
            result["unpaywall_oa_license"] = unpaywall_oa_license
            result["unpaywall_download_attempted"] = unpaywall_download_attempted
            result["unpaywall_download_status"] = unpaywall_download_status
            result["unpaywall_download_error"] = unpaywall_download_error
            # Multi-URL retry diagnostics
            result["unpaywall_alternatives_count"] = unpaywall_alternatives_count
            result["unpaywall_urls_tried"] = unpaywall_urls_tried

        return result

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
