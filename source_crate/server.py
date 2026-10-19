"""MCP transport adapter for the protocol-independent research service."""

import logging

from fastmcp import FastMCP

from source_crate.core import research

mcp = FastMCP("SourceCrateMCP - Academic Paper Research Made Easy")

browse_papers = research.browse_papers
mcp.tool(
    browse_papers,
    description="Search academic sources for paper metadata. Start here for literature searches; does not download papers. Relevance scores are 0–100. Use get_status to discover categories and sources.",
)
browse_papers_streaming = research.browse_papers_streaming
mcp.tool(
    browse_papers_streaming,
    description="Search academic sources concurrently and return aggregated paper metadata with progress statistics. Relevance scores are 0–100. Does not download papers.",
)
download_papers = research.download_papers
mcp.tool(
    download_papers,
    description="Search for and download academic papers, optionally extracting text. Writes local files: specify an output directory and use only when downloads are requested.",
)
convert_pdf_to_text = research.convert_pdf_to_text
mcp.tool(
    convert_pdf_to_text,
    description="Extract text from an existing local PDF into a local output file. Supply the PDF path and optional output path.",
)
convert_pdf_to_markdown = research.convert_pdf_to_markdown
mcp.tool(
    convert_pdf_to_markdown,
    description="Convert an existing local PDF to Markdown, preserving document structure. Writes a local output file.",
)
batch_convert_pdfs = research.batch_convert_pdfs
mcp.tool(
    batch_convert_pdfs,
    description="Convert PDFs in a local directory to text or Markdown. Writes files to the specified output directory.",
)
get_status = research.get_status
mcp.tool(
    get_status,
    description="Inspect available academic sources, categories, configuration and cache status. Enable active_health_check only when live network diagnostics are needed.",
)
get_help = research.get_help
mcp.tool(
    get_help,
    description="Read usage and configuration guidance, YAML schemas and examples. Does not change configuration.",
)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
