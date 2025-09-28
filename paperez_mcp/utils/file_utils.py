"""
File utilities for downloading PDFs and saving markdown files.
"""

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx


async def download_pdf(pdf_url: str, output_dir: str = ".paperez", title: str = None) -> dict[str, Any]:
    """
    Download a PDF from URL to local directory.

    Args:
        pdf_url: URL of the PDF to download
        output_dir: Directory to save the PDF
        title: Optional paper title for readable filename

    Returns:
        Dictionary with download results
    """
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename - prefer title, fallback to technical ID
        if title:
            # Use paper title for readable filename
            filename = title[:50]  # Truncate to reasonable length
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = re.sub(r'\s+', ' ', filename)  # Normalize whitespace
            if not filename:  # If title sanitization results in empty string
                filename = "unknown_paper"
        else:
            # Fallback to technical ID extraction
            paper_id = None
            if "arxiv.org" in pdf_url:
                # Extract arXiv ID
                match = re.search(r'(\d{4}\.\d{4,5})', pdf_url)
                if match:
                    paper_id = f"arxiv_{match.group(1)}"
            elif "doi.org" in pdf_url:
                # Extract DOI
                match = re.search(r'10\.\d+/(.+)', pdf_url)
                if match:
                    paper_id = f"doi_{match.group(1).replace('/', '_')}"

            if not paper_id:
                # Use URL path as fallback
                parsed = urlparse(pdf_url)
                paper_id = Path(parsed.path).stem or "unknown_paper"

            # Clean filename
            filename = re.sub(r'[^\w\-_\.]', '_', paper_id)

        pdf_path = os.path.join(output_dir, f"{filename}.pdf")

        # Download PDF with redirect handling
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(pdf_url)

            if response.status_code == 200:
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)

                return {
                    "success": True,
                    "pdf_path": pdf_path,
                    "file_size": len(response.content),
                    "filename": filename
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to download PDF: HTTP {response.status_code}"
                }

    except Exception as e:
        return {
            "success": False,
            "error": f"Download failed: {str(e)}"
        }


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
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        return {
            "success": True,
            "markdown_path": file_path,
            "markdown_characters": len(markdown_content)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to save markdown: {str(e)}"
        }
