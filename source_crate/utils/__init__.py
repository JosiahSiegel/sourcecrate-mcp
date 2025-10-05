"""Utility modules for PDF processing and text extraction."""

from .cloudflare_detector import (
    get_cloudflare_info,
    is_cloudflare_challenge,
    suggest_alternatives,
)
from .file_utils import download_pdf, save_markdown_file
from .pdf_processor import convert_pdf_to_markdown_content, extract_pdf_text
from .smart_search import smart_downloadable_search
from .unpaywall_client import UnpaywallClient, get_unpaywall_client

__all__ = [
    "extract_pdf_text",
    "convert_pdf_to_markdown_content",
    "download_pdf",
    "save_markdown_file",
    "smart_downloadable_search",
    "UnpaywallClient",
    "get_unpaywall_client",
    "is_cloudflare_challenge",
    "get_cloudflare_info",
    "suggest_alternatives",
]
