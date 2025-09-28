"""
Paper processing service - handles downloading and converting papers.
Eliminates duplication between download_papers and get_papers functions.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


async def process_papers(
    query: str,
    limit: int,
    output_dir: str,
    search_funcs: dict[str, Any],
    utils: dict[str, Any],
    api_status: dict[str, bool],
    force_category: str | None = None,
    convert_to_markdown: bool = True
) -> dict[str, Any]:
    """
    Core paper processing logic used by both download_papers and get_papers.

    Args:
        query: Search query
        limit: Maximum number of papers
        output_dir: Directory to save files
        search_funcs: Dictionary of search functions
        utils: Dictionary of utility functions
        api_status: API status tracking dict
        force_category: Force specific source category
        convert_to_markdown: If True, convert PDFs to markdown. If False, keep as PDFs.

    Returns:
        Dictionary with results, download counts, and metadata
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Use enhanced routing for intelligent source selection and download
    downloadable_papers, search_log = await utils['smart_downloadable_search'](
        query, limit, search_funcs, utils, api_status, force_category
    )

    downloaded_count = 0

    # Process each downloadable paper
    for paper in downloadable_papers:
        pdf_url = paper.get("pdf_url") or paper.get("open_access_pdf")
        if pdf_url:
            try:
                # Generate safe filename
                title = paper.get("title", "paper")[:50]
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                output_path = Path(output_dir) / f"{safe_title}.md"

                # Download PDF to file with paper title for readable filename
                paper_title = paper.get("title")
                logger.info(f"Downloading PDF with title: '{paper_title}'")
                download_result = await utils['download_pdf'](pdf_url, output_dir, paper_title)
                if download_result.get("success"):
                    logger.info(f"PDF downloaded to: {download_result.get('pdf_path')}")
                    pdf_file_path = download_result["pdf_path"]

                    if convert_to_markdown:
                        # Convert PDF to markdown
                        markdown_result = utils['convert_pdf_to_markdown_content'](
                            pdf_file_path,
                            paper.get("title", ""),
                            paper.get("authors", [])
                        )

                        if markdown_result.get("success"):
                            markdown_content = markdown_result["markdown"]

                            # Save markdown file
                            save_result = utils['save_markdown_file'](markdown_content, str(output_path))
                            if save_result.get("success"):
                                paper["local_markdown"] = str(output_path)
                                paper["markdown_characters"] = len(markdown_content)
                                downloaded_count += 1

                                # Clean up PDF file since we only need the markdown
                                try:
                                    import os
                                    if os.path.exists(pdf_file_path):
                                        os.remove(pdf_file_path)
                                        logger.info(f"Cleaned up PDF file: {pdf_file_path}")
                                except Exception as e:
                                    logger.warning(f"Failed to clean up PDF file {pdf_file_path}: {e}")
                            else:
                                paper["download_error"] = f"Failed to save markdown: {save_result.get('error')}"
                        else:
                            paper["download_error"] = f"Failed to convert to markdown: {markdown_result.get('error')}"
                    else:
                        # PDF-only mode: keep the PDF file
                        paper["local_pdf"] = pdf_file_path
                        paper["pdf_file_size"] = download_result.get("file_size", 0)
                        downloaded_count += 1
                else:
                    paper["download_error"] = f"Failed to download PDF: {download_result.get('error')}"
            except Exception as e:
                paper["download_error"] = str(e)

    # Check for fallback usage
    fallback_used = any(paper.get('_fallback_used', False) for paper in downloadable_papers)
    original_category = None
    if fallback_used and downloadable_papers:
        original_category = downloadable_papers[0].get('_original_category')

    result = {
        "results": downloadable_papers,
        "total_found": len(downloadable_papers),
        "downloaded_count": downloaded_count,
        "output_directory": output_dir,
        "query": query
    }

    # Add fallback notification if used
    if fallback_used:
        result["fallback_notification"] = {
            "message": f"Papers found using comprehensive sources (original {'smart routing' if not original_category else original_category} found no results)",
            "original_category": original_category or "smart_routing",
            "fallback_category": "comprehensive"
        }

    # Add intelligent error suggestions if no results found
    if len(downloadable_papers) == 0 and search_log.get("intelligent_error_suggestions"):
        error_info = search_log["intelligent_error_suggestions"]
        result["error_suggestions"] = {
            "message": error_info["message"],
            "domain_detected": error_info.get("domain_detected"),
            "suggestions": error_info["suggestions"][:3],  # Top 3 suggestions
            "suggested_categories": error_info.get("suggested_categories", []),
            "help_text": error_info.get("help_text"),
            "query_refinements": error_info.get("query_refinements", [])[:2]  # Top 2 refinements
        }

    return result
