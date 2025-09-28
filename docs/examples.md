# Usage Examples

## Basic Research Workflows

### Quick Paper Download

**Goal**: Get a few papers on a topic quickly

**Natural Language:**
- "Download 3 machine learning papers"
- "Get papers about quantum computing"
- "Save transformer papers to my research folder"

**What happens:**
1. Searches multiple academic databases
2. Downloads PDFs with readable filenames
3. Converts to markdown format automatically
4. Saves to specified directory

### Browse Before Download

**Goal**: Explore available papers before downloading

**Workflow:**
1. "Browse papers about neural networks" (metadata only)
2. Review titles and abstracts
3. "Download papers about specific transformer architectures"

**Benefits:**
- Quick overview without using storage
- Better selection of relevant papers
- Efficient use of API quotas

### PDF Processing

**Goal**: Convert existing PDFs to usable formats

**Natural Language:**
- "Convert this PDF to markdown: /path/to/paper.pdf"
- "Extract text from research_paper.pdf"
- "Convert all PDFs in my downloads folder"

**Use Cases:**
- Process locally saved papers
- Extract text for analysis
- Create searchable archives

## Advanced Research Scenarios

### Literature Review

**Goal**: Comprehensive research on a topic

**Step-by-step:**
1. "Browse 20 papers about attention mechanisms" (overview)
2. "Download 5 key transformer papers"
3. "Get papers by Vaswani, Hinton, and Bengio"
4. "Convert PDFs in literature_review folder to markdown"
5. "Check system status" (monitor API usage)

### Systematic Research

**Goal**: Organized, methodical paper collection

**Workflow:**
```
1. Create research directories
2. "Download preprint papers about large language models"
3. "Get peer-reviewed papers about transformer efficiency"
4. "Browse historical papers about attention mechanisms"
5. "Batch convert all collected PDFs"
```

### Domain-Specific Research

**Goal**: Focus on specific academic fields

**Medical Research:**
- "Download medical papers about COVID-19 treatments"
- "Get clinical trial papers about cancer immunotherapy"

**Computer Science:**
- "Download AI papers from arXiv"
- "Get machine learning papers from top conferences"

**Physics:**
- "Browse quantum computing papers"
- "Download physics papers about quantum entanglement"

## Configuration Examples

### Enhanced Performance Setup

**Goal**: Optimize for heavy research use

**Environment Variables:**
```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key_here"
export CROSSREF_EMAIL="researcher@university.edu"
export MAX_RETRIES=5
```

**Custom Configuration:**
```yaml
version: "1.0"
use_default_sources: true
max_concurrent_searches: 20
global_cache_enabled: true
global_cache_expire: 14400  # 4 hours
default_output_dir: ./research_papers
```

### Minimal Setup

**Goal**: Simple, focused research setup

**Configuration:**
```yaml
version: "1.0"
use_default_sources: false
default_category: academic_premium
sources:
  crossref:
    enabled: true
  semantic_scholar:
    enabled: true
categories:
  simple:
    sources:
      - crossref
      - semantic_scholar
```

## Specific Use Cases

### 1. Course Preparation

**Scenario**: Professor preparing course materials

**Workflow:**
1. "Browse 50 papers about machine learning fundamentals"
2. Select 10 key papers from results
3. "Download papers about neural network basics"
4. "Convert course_papers folder to markdown"
5. Use markdown files for lecture preparation

### 2. Research Proposal

**Scenario**: Graduate student writing research proposal

**Steps:**
1. "Get recent papers about graph neural networks"
2. "Download historical papers about graph algorithms"
3. "Browse papers by key researchers in the field"
4. "Convert all papers to text for citation extraction"

### 3. Industry Research

**Scenario**: Company researching new technologies

**Process:**
1. "Download business papers about AI adoption"
2. "Get recent papers about practical machine learning"
3. "Browse papers about AI in specific industry"
4. Create organized archive for team access

### 4. Meta-Analysis

**Scenario**: Researcher conducting systematic review

**Methodology:**
1. "Browse 100+ papers about study topic" (broad overview)
2. Filter results based on criteria
3. "Download selected papers for detailed analysis"
4. "Extract text from all papers for content analysis"
5. Use extracted text for statistical analysis

## Troubleshooting Examples

### Rate Limiting

**Problem**: Getting rate limited during heavy usage

**Solution:**
```bash
# Set API keys for higher limits
export SEMANTIC_SCHOLAR_API_KEY="your_key"

# Spread requests over time
"Browse papers first, then download in batches"
```

### PDF Access Issues

**Problem**: Some papers behind paywalls

**Workaround:**
1. "Browse papers to see what's available"
2. Focus on open access sources
3. Use institutional access to download PDFs manually
4. "Convert downloaded PDFs to markdown"

### Large Dataset Processing

**Problem**: Processing hundreds of papers

**Efficient Approach:**
1. Create organized directory structure
2. "Download papers in small batches"
3. "Batch convert PDFs folder by folder"
4. Use caching to avoid re-downloading

## Integration Examples

### With Data Analysis

**Python Integration:**
```python
# After using PaperezMCP to download papers
import os
import pandas as pd

# Process markdown files for analysis
papers_dir = "./research_papers"
paper_data = []

for file in os.listdir(papers_dir):
    if file.endswith('.md'):
        # Extract metadata and content
        # Add to analysis dataset
        pass

df = pd.DataFrame(paper_data)
# Analyze trends, citations, etc.
```

### With Reference Management

**Workflow:**
1. "Download papers about research topic"
2. Extract DOIs and citations from markdown files
3. Import into reference manager (Zotero, Mendeley)
4. Use organized library for writing

### With AI Analysis

**Process:**
1. "Download relevant papers"
2. "Convert to text format for AI processing"
3. Use text files with LLMs for:
   - Summarization
   - Key concept extraction
   - Research gap identification
   - Hypothesis generation

## Best Practices Summary

### Efficient Research
1. **Start broad, narrow down**: Browse first, then download specific papers
2. **Use specific queries**: Author names, exact titles, DOIs work best
3. **Leverage caching**: Repeat similar queries are much faster
4. **Batch operations**: Process multiple papers together

### API Management
1. **Set environment variables** for better performance
2. **Monitor status** during heavy usage periods
3. **Use multiple sources** for comprehensive coverage
4. **Respect rate limits** with automatic backoff

### Organization
1. **Create clear directory structures** for different projects
2. **Use descriptive filenames** (automatically generated)
3. **Convert to searchable formats** (markdown/text)
4. **Maintain local archives** for offline access