# Usage Examples

## Basic Workflows

### Quick Research
```
"Download 3 machine learning papers"
"Browse papers about quantum computing"
"Get transformer papers by Vaswani"
```

### Browse Then Download
```
1. "Browse 10 papers about neural networks"
2. Review titles and abstracts
3. "Download papers about attention mechanisms"
```

### PDF Processing
```
"Convert this PDF to markdown: /path/to/paper.pdf"
"Extract text from research_paper.pdf"
"Convert all PDFs in downloads folder"
```

## Research Projects

### Literature Review
```
1. "Browse 20 papers about attention mechanisms"
2. "Download 5 key transformer papers"
3. "Get papers by key researchers: Hinton, Bengio"
4. "Convert PDFs in literature_review folder"
```

### Domain-Specific
```
Medical: "Download COVID-19 treatment papers"
Physics: "Get quantum computing papers from arXiv"
Business: "Browse economics papers about AI adoption"
Social Sciences: "Find psychology research on memory"
Humanities: "Get literature papers about Shakespeare"
Legal: "Search court cases about privacy rights"
Government: "Find federal regulations on AI"
Historical: "Browse government archives from 1950s"
```

## Configuration Examples

### Enhanced Performance
```bash
export SEMANTIC_SCHOLAR_API_KEY="your_key"
export CROSSREF_EMAIL="researcher@university.edu"
```

### Custom Config (Any YAML file in .paperez/config/)
```yaml
# .paperez/config/my_university.yaml
version: "1.0"
use_default_sources: true
sources:
  university_repository:
    name: university_repository
    type: http_api
    enabled: true
    config:
      base_url: https://repository.myuni.edu/api
      search_path: /search
      field_mappings:
        title: title
        authors: creators
categories:
  university_research:
    name: university_research
    sources:
      - university_repository
      - crossref
```

### Domain-Specific Organization
```yaml
# .paperez/config/chemistry.yaml - Chemistry-specific sources
# .paperez/config/engineering.yaml - Engineering databases
# .paperez/config/local.yaml - Institution-specific APIs
```

## Troubleshooting Workflow

```
1. "Check system status"
2. Try simple: "papers by Einstein"
3. "Help me configure paperez-mcp"
4. Restart Claude Code if needed
```

## Integration

### With Analysis
```
1. "Download papers about topic"
2. "Convert to text for analysis"
3. Use text files with data analysis tools
```

### Batch Processing
```
1. Create organized folders
2. "Download papers in batches"
3. "Batch convert PDFs folder by folder"
4. Maintain searchable archives
```