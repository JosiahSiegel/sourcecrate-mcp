# API Reference

## Main Tools

### download_papers
**Get full papers as files**

Parameters:
- `query`: Search query
- `limit`: Max papers (default: 5)
- `output_dir`: Save location (default: ".paperez")
- `convert_to_markdown`: Convert PDFs (default: true)

Usage: "Download 3 machine learning papers"

### browse_papers
**Quick metadata overview**

Parameters:
- `query`: Search query
- `limit`: Max results (default: 10)

Usage: "Browse papers by Geoffrey Hinton"

### convert_pdf_to_text
**Extract text from PDF**

Parameters:
- `file_path`: Path to PDF file
- `output_path`: Output location (optional)

Usage: "Convert PDF to text: /path/to/paper.pdf"

### convert_pdf_to_markdown
**Convert PDF to markdown**

Parameters:
- `file_path`: Path to PDF file
- `output_path`: Output location (optional)

Usage: "Convert PDF to markdown: /path/to/paper.pdf"

### batch_convert_pdfs
**Convert multiple PDFs**

Parameters:
- `directory`: PDF folder (default: "articles")
- `output_dir`: Output folder (optional)

Usage: "Convert all PDFs in research folder"

### get_status
**System health check**

Returns API status, performance metrics, and recommendations.

Usage: "Check system status"

### get_help
**Configuration guidance**

Returns setup instructions, examples, and troubleshooting.

Usage: "Help me configure paperez-mcp"

## Force Categories

Use `force_category` parameter:
- `"comprehensive"`: All sources (default)
- `"medical"`: Medical/biomedical sources
- `"preprints"`: Latest research (arXiv)
- `"open_access"`: Free full-text
- `"business"`: Economics/finance

## Sources

- **CrossRef**: 130M+ DOIs, most reliable
- **Semantic Scholar**: 225M+ papers, AI insights
- **arXiv**: Physics, CS preprints
- **PubMed**: Biomedical literature
- **Google Scholar**: Broadest coverage

## Performance

- Multi-source search: 1-3 seconds
- PDF extraction: 5-30 seconds
- Zero-token conversion: 2-10 seconds
- Smart caching: 1GB cache