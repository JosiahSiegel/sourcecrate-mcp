# API Reference

## Available Tools

### 📄 download_papers

**Primary tool for getting full papers as files**

Get academic papers as PDF or Markdown files with readable filenames.

**Parameters:**
- `query` (string): Search query (keywords, DOI, title, or author)
- `limit` (int): Maximum papers to download (default: 5, recommended: 5-10)
- `output_dir` (string): Directory to save files (default: ".paperez")
- `force_category` (string, optional): Force specific source types
- `convert_to_markdown` (bool): Convert PDFs to markdown (default: true)

**Force Category Options:**
- `"preprints"`: arXiv, SocArXiv, OSF (latest research, not peer-reviewed)
- `"journals"`: CrossRef, PubMed, DOAJ (peer-reviewed publications)
- `"open_access"`: CORE, DOAJ, arXiv (free full-text available)
- `"historical"`: CORE, CrossRef (older documents, archives)
- `"recent"`: arXiv, Semantic Scholar (newest papers, last few years)
- `"comprehensive"`: Semantic Scholar, CrossRef (broad coverage)

**Usage:**
- "Download 3 machine learning papers"
- "Get climate change papers as PDFs"
- "Save neural network papers to research folder"

---

### 🔍 browse_papers

**Quick metadata overview without downloading**

Get titles, abstracts, and metadata for exploration before downloading.

**Parameters:**
- `query` (string): Search query (keywords, DOI, title, or author)
- `limit` (int): Maximum results to return (default: 10, recommended: 20)
- `force_category` (string, optional): Force specific source types

**Usage:**
- "Browse papers by Geoffrey Hinton"
- "Show me quantum computing papers"
- "Search for transformer papers, metadata only"

---

### 📝 convert_pdf_to_text

**Convert PDF to plain text files**

Extract text from PDF files using PyMuPDF with unlimited character support.

**Parameters:**
- `file_path` (string): Path to PDF file (supports absolute and relative paths)
- `output_path` (string, optional): Output path for text file
- `title` (string, optional): Optional title for document header
- `authors` (list, optional): Optional list of authors for document header

**Features:**
- Zero context window consumption (content saved to files)
- Preserves all text content with page separators
- Fast processing using optimized PyMuPDF engine

**Usage:**
- "Convert this PDF to text: /path/to/paper.pdf"
- "Extract text from research paper"

---

### 🔄 convert_pdf_to_markdown

**Convert PDF to formatted markdown**

Convert PDF files to structured markdown preserving document formatting.

**Parameters:**
- `file_path` (string): Path to PDF file
- `title` (string, optional): Optional title for document header
- `authors` (list, optional): Optional list of authors
- `output_path` (string, optional): Output path for markdown file

**Features:**
- Zero AI tokens used (direct PDF→markdown conversion)
- Preserves document structure and formatting
- Fast processing with pymupdf4llm

**Usage:**
- "Convert PDF to markdown: /path/to/paper.pdf"
- "Make this paper into markdown format"

---

### 📁 batch_convert_pdfs

**Convert entire directories of PDFs**

Bulk convert all PDFs in a directory to markdown format.

**Parameters:**
- `directory` (string): Directory containing PDFs (default: "articles")
- `output_dir` (string, optional): Output directory for markdown files

**Features:**
- Zero AI tokens consumed during conversion
- Memory efficient for large directories
- Recursively searches for PDF files

**Usage:**
- "Convert all PDFs in research_papers folder"
- "Batch convert PDFs to markdown"

---

### 🔧 get_status

**System health and monitoring**

Get comprehensive system status including API health, performance metrics, and configuration details.

**Parameters:** None

**Returns:**
- API status for all academic databases
- Cache usage and configuration information
- Health monitoring with performance metrics
- Recommendations for system improvements

**Usage:**
- "Check system status"
- "Show API health"
- "Get performance metrics"

---

### ❓ get_help

**Configuration guidance**

Get comprehensive guidance on creating config files, including paths, schemas, examples, and troubleshooting.

**Parameters:** None

**Returns:**
- Complete configuration setup guide
- File paths and directory structure
- Configuration schema and field descriptions
- Practical examples for different use cases
- Troubleshooting guidance

**Usage:**
- "Help me configure paperez-mcp"
- "Show configuration examples"
- "Get setup guidance"

## Multi-Source Coverage

### Search Sources (Automatic Fallback)
- 🥇 **CrossRef** - Primary source, 130M+ DOIs, most reliable
- 🧠 **Semantic Scholar** - 225M+ papers with AI-powered insights
- 📚 **arXiv** - Physics, math, CS, and technical preprints
- 🏥 **PubMed** - Comprehensive biomedical literature
- 🔍 **Google Scholar** - Broadest coverage, fallback source

### Performance Characteristics
- **Multi-source search**: ~1-3 seconds (with intelligent fallback)
- **Unlimited PDF extraction**: ~5-30 seconds (depending on paper size)
- **Zero-token markdown conversion**: ~2-10 seconds per paper
- **Batch processing**: Concurrent operations supported
- **Smart caching**: 1GB cache improves repeat queries dramatically

## API Rate Limits & Sources

| Service              | Free Tier           | Enhanced Access        | Notes                          |
| -------------------- | ------------------- | ---------------------- | ------------------------------ |
| **CrossRef**         | No explicit limits  | Same                   | Primary source, most reliable  |
| **Semantic Scholar** | 1,000 requests/hour | 10,000+ with API key   | 225M+ papers                   |
| **arXiv**            | No explicit limits  | Same                   | Preprints and technical papers |
| **PubMed**           | No explicit limits  | Same                   | Biomedical literature          |
| **Google Scholar**   | Rate limited        | Stable with ScraperAPI | Fallback source                |