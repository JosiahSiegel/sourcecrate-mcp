# SourceCrate Test Suite

This directory contains automated tests for SourceCrate functionality.

## Dynamic Category Testing

### `test_all_categories_dynamic.py`

**Comprehensive dynamic test script** that automatically:

🔍 **Discovers all configured categories** - No manual updates needed when categories change
🧪 **Tests all MCP tools** for every category:
- `browse_papers` → Requires search results output
- `download_papers` → Requires file creation (PDFs/markdown)
- `convert_pdf_to_text` → Requires text file output
- `convert_pdf_to_markdown` → Requires markdown file output
- `batch_convert_pdfs` → Requires batch file conversion
- `get_status` → Requires system status output
- `get_help` → Requires help documentation output

📊 **Validates both text and file outputs** with appropriate expectations per tool type

## Usage

### Run All Tests
```bash
# From project root
python tests/test_all_categories_dynamic.py
```

### Expected Output
```text
🧪 SourceCrate Dynamic Tool Testing
=====================================
✓ Successfully imported SourceCrate modules
🚀 Starting comprehensive MCP tool testing...
📊 Configuration: 16 sources, 10 categories
🔍 Discovered 10 categories: ['business', 'historical', 'medical', ...]

🧪 Testing category: 'medical'
  📖 Testing browse_papers for 'medical'...
  💾 Testing download_papers for 'medical'...

🧪 Testing category: 'scientific'
  📖 Testing browse_papers for 'scientific'...
  💾 Testing download_papers for 'scientific'...

📋 TEST RESULTS SUMMARY
=======================================
📁 Category: medical
  ✅ browse_papers: 3 results from 2 sources
  ✅ download_papers: 2 papers, 4 files created

🛠️ System Tools:
  ✅ get_status: Success
  ✅ get_help: Success

📊 OVERALL RESULTS:
  • Total tests: 22
  • Successful: 18
  • Success rate: 81.8%
  🎉 Excellent! Most tools are working correctly.
```

## Features

### ✅ **Fully Dynamic**
- Automatically discovers categories from configuration files
- No hardcoded category names - works with any YAML config structure
- Self-updating when new categories/sources are added

### ✅ **Comprehensive Testing**
- Tests both text output tools (browse, status, help)
- Tests file output tools (download, convert, batch)
- Validates actual file creation and content
- Category-specific test queries for realistic testing

### ✅ **Smart Test Management**
- Creates temporary directories for file outputs
- Automatic cleanup after testing
- Rate limiting between tests to avoid API issues
- Detailed error reporting and categorization

### ✅ **Rich Results**
- Human-readable summary with success rates
- Detailed JSON output saved to `test_results.json`
- Color-coded status indicators
- Specific metrics per tool type (result counts, file counts, etc.)

## Test Categories

The script automatically uses appropriate test queries per category:

| Category | Test Query |
|----------|------------|
| `medical` | "diabetes treatment clinical trial" |
| `scientific` | "machine learning neural networks" |
| `business` | "economics finance market analysis" |
| `historical` | "government archives historical documents" |
| `social_sciences` | "psychology education research" |
| `humanities` | "literature philosophy cultural studies" |
| `legal_research` | "court case law legal opinion" |
| `government_policy` | "federal regulation policy document" |
| *fallback* | "research academic paper" |

## Output Files

- **`test_results.json`** - Detailed test results in JSON format
- **Temporary files** - Created during testing, automatically cleaned up
- **Downloaded papers** - Test PDFs/markdown files (cleaned up after testing)

## Error Handling

The script handles various error conditions:
- **No results found** - Distinguishes from actual failures
- **API errors** - Network issues, rate limiting, authentication
- **File system errors** - Permissions, disk space, invalid paths
- **Configuration errors** - Missing categories, invalid source configs

## Integration

This test can be integrated into:
- **CI/CD pipelines** - Returns appropriate exit codes
- **Pre-commit hooks** - Validate functionality before commits
- **Development workflow** - Quick validation during development
- **Deployment verification** - Confirm everything works in production

The dynamic nature means it never needs updating when the configuration structure changes!
