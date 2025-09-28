"""
PDF processing utilities for text extraction and markdown conversion.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup

from ..config import cache

logger = logging.getLogger(__name__)


async def extract_pdf_text(pdf_url: str) -> dict[str, Any]:
    """Extract text from PDF with redirect handling and fallback methods"""
    cache_key = f"pdf_text:{pdf_url}"
    cached = cache.get(cache_key)
    if cached:
        return cached  # type: ignore[no-any-return]

    # Try arXiv HTML extraction first (most reliable for arXiv papers)
    if "arxiv.org" in pdf_url:
        try:
            # Convert PDF URL to abstract page URL
            if "/pdf/" in pdf_url:
                abstract_url = pdf_url.replace("/pdf/", "/abs/").replace(".pdf", "")
            else:
                abstract_url = pdf_url.replace(".pdf", "")

            response = requests.get(abstract_url, timeout=30)

            if response.status_code == 200:
                html_content = response.text
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract title
                title_elem = soup.find('h1', class_='title')
                title = title_elem.get_text().replace('Title:', '').strip() if title_elem else "Unknown Title"

                # Extract abstract
                abstract_elem = soup.find('blockquote', class_='abstract')
                abstract = abstract_elem.get_text().replace('Abstract:', '').strip() if abstract_elem else ""

                # Extract authors
                authors_elem = soup.find('div', class_='authors')
                authors = authors_elem.get_text().replace('Authors:', '').strip() if authors_elem else ""

                # Check for source files link
                source_link = soup.find('a', string='Other formats')
                source_available = bool(source_link)

                if abstract or title:
                    full_text = f"Title: {title}\n\nAuthors: {authors}\n\nAbstract:\n{abstract}"
                    if source_available:
                        full_text += f"\n\nNote: LaTeX source files are available at {abstract_url.replace('/abs/', '/format/')}"

                    result = {
                        "text": full_text,
                        "extraction_method": "arXiv HTML",
                        "pdf_url": pdf_url,
                        "abstract_url": abstract_url,
                        "source_available": source_available,
                        "success": True
                    }
                    cache.set(cache_key, result, expire=86400 * 30)
                    return result

        except Exception:
            pass  # Fall back to other methods

    # Try simple PDF text extraction
    try:
        response = requests.get(pdf_url, timeout=60)

        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            # Extract text using PyMuPDF
            doc = fitz.open(tmp_path)
            full_text = ""
            num_pages = len(doc)

            for page_num in range(num_pages):  # Extract all pages
                page = doc.load_page(page_num)
                text = page.get_text()
                if text.strip():
                    full_text += f"\n--- Page {page_num + 1} ---\n{text}\n"

            doc.close()
            os.unlink(tmp_path)  # Cleanup

            if full_text.strip() and len(full_text.strip()) > 100:
                result = {
                    "text": full_text,  # No character limit
                    "num_pages": num_pages,
                    "extraction_method": "PyMuPDF",
                    "pdf_url": pdf_url,
                    "success": True
                }
                cache.set(cache_key, result, expire=86400 * 30)
                return result

    except Exception:
        pass

    # If all methods failed
    return {
        "success": False,
        "error": "PDF extraction failed - trying fallback methods",
        "pdf_url": pdf_url
    }


def extract_pdf_text_from_local_file(file_path: str) -> dict[str, Any]:
    """Extract text from a local PDF file with unlimited pages and characters"""
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "file_path": file_path
        }

    try:
        # Get file stats
        file_size = os.path.getsize(file_path)

        # Extract text using PyMuPDF
        doc = fitz.open(file_path)
        full_text = ""
        num_pages = len(doc)

        # Extract ALL pages without limit
        for page_num in range(num_pages):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text.strip():
                full_text += f"\n--- Page {page_num + 1} ---\n{text}\n"

        doc.close()

        # Return results without character limits
        if full_text.strip():
            return {
                "success": True,
                "text": full_text,  # Complete text, no truncation
                "num_pages": num_pages,
                "file_size": file_size,
                "text_length": len(full_text),
                "extraction_method": "PyMuPDF Local",
                "file_path": file_path
            }
        else:
            return {
                "success": False,
                "error": "PDF extraction failed - no text found",
                "file_path": file_path
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"PDF extraction failed: {str(e)}",
            "file_path": file_path
        }


def convert_pdf_to_markdown_content(file_path: str, title: str = "", authors: list[Any] | None = None) -> dict[str, Any]:
    """Convert a local PDF file to formatted markdown content"""

    # First extract the PDF text
    pdf_result = extract_pdf_text_from_local_file(file_path)

    if not pdf_result.get("success"):
        return pdf_result

    try:
        # Build structured markdown
        markdown = []

        # Title section
        if title:
            markdown.append(f"# {title}")
        else:
            # Try to extract title from first few lines
            text_lines = pdf_result["text"].split('\n')[:10]
            for line in text_lines:
                line = line.strip()
                if line and len(line) > 10 and len(line) < 200:
                    markdown.append(f"# {line}")
                    break
            else:
                filename = Path(file_path).stem.replace('_', ' ').title()
                markdown.append(f"# {filename}")

        # Authors section
        if authors:
            markdown.append("\n## Authors")
            for author in authors:
                markdown.append(f"- {author}")

        # Document metadata
        markdown.append("\n## Document Metadata")
        markdown.append(f"- **File**: {Path(file_path).name}")
        markdown.append(f"- **Pages**: {pdf_result.get('num_pages', 0)}")
        markdown.append(f"- **Text Length**: {pdf_result.get('text_length', 0):,} characters")
        markdown.append(f"- **Extraction Method**: {pdf_result.get('extraction_method', 'Unknown')}")

        # Full text content with page breaks
        markdown.append("\n## Full Text Content")

        # Split content by pages and add proper headers
        text_content = pdf_result["text"]
        pages = text_content.split("--- Page ")

        for _i, page_content in enumerate(pages[1:], 1):  # Skip first empty split
            page_number = page_content.split(" ---")[0]
            page_text = page_content.split(" ---", 1)[1] if " ---" in page_content else page_content

            markdown.append(f"\n### Page {page_number}")
            markdown.append(f"\n{page_text.strip()}")

        markdown_content = "\n".join(markdown)

        return {
            "success": True,
            "markdown": markdown_content,
            "markdown_length": len(markdown_content),
            "original_file": file_path,
            "pages_extracted": pdf_result.get('num_pages', 0),
            "text_length": pdf_result.get('text_length', 0)
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Markdown conversion failed: {str(e)}",
            "file_path": file_path
        }
