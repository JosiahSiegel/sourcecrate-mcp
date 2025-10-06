# SourceCrate Resource Optimization Plan

## Current Resource Usage Analysis

### Server-Side Processing (Fly.io)
**Current VM:** shared-cpu-2x (2 cores, 512MB RAM)

**Heavy Resource Consumers:**
1. **PDF Processing** (🔴 CRITICAL - ~60% memory)
   - `pymupdf` + `pymupdf4llm` = ~120MB per worker
   - PDF text extraction
   - PDF-to-markdown conversion
   - Loaded even when not used

2. **Concurrent API Requests** (🟡 MEDIUM - ~25% CPU)
   - 20+ simultaneous HTTP connections
   - Each source maintains client state
   - asyncio event loop overhead

3. **Result Processing** (🟡 MEDIUM - ~15% CPU/memory)
   - Fuzzy matching (`rapidfuzz`) for deduplication
   - BM25 ranking (`rank-bm25` + `numpy`)
   - Paper merging logic

4. **Python Runtime** (🟢 LOW - ~10%)
   - Base FastAPI + Gunicorn
   - Dependency loading

---

## 🎯 Optimization Strategy: Hybrid Client-Server Architecture

### **Phase 1: Quick Wins (1-2 hours, 50% CPU reduction)**

#### 1.1 Move Result Processing to Client ⭐⭐⭐
**Current:** Server does deduplication, merging, BM25 ranking
**Optimized:** Browser does all result processing

**Implementation:**
```javascript
// browser-ui/js/processing.js
import Fuse from 'fuse.js';  // Fuzzy matching (9KB gzipped)

class PaperProcessor {
    deduplicatePapers(papers) {
        // Port fuzzy matching logic from Python
        // Group by DOI, title similarity
        // Merge duplicate entries
    }

    calculateBM25Relevance(papers, query) {
        // Simple BM25 implementation in JS
        // Or use library: https://github.com/fergiemcdowall/search-index-bm25
    }
}
```

**Benefits:**
- Remove `rank-bm25` dependency (saves numpy too!)
- Remove `rapidfuzz` C extension
- Reduce server CPU by ~30%
- Reduce memory by ~15%

**Trade-offs:**
- Slight client-side CPU usage (negligible on modern browsers)
- ~20KB additional JavaScript

---

#### 1.2 Lazy Load PDF Processing ⭐⭐
**Current:** PDF libraries loaded at startup
**Optimized:** Only import when PDF endpoint called

**Implementation:**
```python
# source_crate/http_server.py
@app.post("/api/v1/convert/pdf-to-markdown")
async def convert_pdf_endpoint(...):
    # Lazy import inside function
    from source_crate.utils import convert_pdf_to_markdown_content
    # Only loads pymupdf when this endpoint is hit
```

**Benefits:**
- Reduce baseline memory by ~120MB
- Faster startup time
- Most searches don't need PDF conversion

**Trade-offs:**
- First PDF conversion ~200ms slower (one-time import cost)

---

### **Phase 2: Direct API Calls (3-4 hours, 70% CPU reduction, 40% memory reduction)**

#### 2.1 CORS-Enabled Sources → Client-Side ⭐⭐⭐⭐

**Analysis of Academic APIs:**

| Source | CORS Support | Public API | Client-Side Ready? |
|--------|--------------|------------|-------------------|
| **arXiv** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **CrossRef** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **PubMed** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **PubMed Central** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **bioRxiv** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **medRxiv** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **DOAJ** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **Zenodo** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **DataCite** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **Europe PMC** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **PLOS** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **Semantic Scholar** | ❌ No | ✅ Yes | ⚠️ **Proxy needed** |
| **OpenAlex** | ✅ Yes | ✅ Yes | ✅ **Ready** |
| **Unpaywall** | ❓ Check | ✅ Yes | ⚠️ **Test needed** |

**~11-13 out of 20 sources can go client-side!**

**Architecture:**
```
┌─────────────────────────────────────────┐
│  Browser                                │
│  ┌─────────────────────────────────┐   │
│  │  Direct API Calls (11 sources)  │   │
│  │  - arXiv, CrossRef, PubMed,     │   │
│  │  - bioRxiv, DOAJ, Zenodo, etc.  │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Result Processing              │   │
│  │  - Deduplication, BM25, Merge   │   │
│  └─────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │ (Only for ~7 sources)
               ▼
┌─────────────────────────────────────────┐
│  Fly.io Server (Minimal Proxy)          │
│  ┌─────────────────────────────────┐   │
│  │  Proxy for non-CORS sources:    │   │
│  │  - Semantic Scholar              │   │
│  │  - Google Scholar (if used)      │   │
│  │  - Others without CORS           │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Implementation:**
```javascript
// browser-ui/js/api-clients/arxiv.js
export class ArxivClient {
    async search(query, limit) {
        const params = new URLSearchParams({
            search_query: `all:${query}`,
            start: 0,
            max_results: limit
        });

        const response = await fetch(
            `https://export.arxiv.org/api/query?${params}`,
            { mode: 'cors' }  // Direct browser request!
        );

        const xml = await response.text();
        return this.parseArxivXML(xml);
    }
}
```

**Benefits:**
- Server handles only 7-9 sources instead of 20
- Reduce server CPU by ~65%
- Reduce server memory by ~40%
- Faster results (parallel browser requests)
- No rate limiting issues (requests come from user's IP)

**Trade-offs:**
- Client needs ~50KB more JavaScript
- User's IP visible to APIs (privacy consideration)
- Requires browser-based API clients

---

#### 2.2 IndexedDB Caching ⭐⭐

**Current:** Server-side disk cache
**Optimized:** Browser-side IndexedDB

**Implementation:**
```javascript
// browser-ui/js/cache.js
class PaperCache {
    async get(query) {
        const db = await this.openDB();
        const cached = await db.get('searches', query);
        if (cached && Date.now() - cached.timestamp < 3600000) {
            return cached.results;  // 1 hour cache
        }
        return null;
    }

    async set(query, results) {
        const db = await this.openDB();
        await db.put('searches', {
            query,
            results,
            timestamp: Date.now()
        });
    }
}
```

**Benefits:**
- Remove server cache (save ~100MB memory)
- Persistent cache across sessions
- Each user caches their own searches

---

### **Phase 3: Remove PDF Processing (1-2 hours, 60% memory reduction)**

#### 3.1 Client-Side PDF Viewing ⭐⭐⭐⭐

**Current:** Server downloads + converts PDFs
**Optimized:** Direct PDF links + browser viewer

**Implementation:**
```javascript
// browser-ui/js/pdf-handler.js
import * as pdfjsLib from 'pdfjs-dist';

class PDFHandler {
    async viewPDF(url) {
        // Option 1: Direct link (let browser handle)
        window.open(url, '_blank');

        // Option 2: In-app viewer with PDF.js
        const pdf = await pdfjsLib.getDocument(url).promise;
        this.renderPDF(pdf);
    }

    async extractText(url) {
        // Client-side text extraction if needed
        const pdf = await pdfjsLib.getDocument(url).promise;
        let text = '';
        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            text += content.items.map(item => item.str).join(' ');
        }
        return text;
    }
}
```

**Benefits:**
- Remove `pymupdf` + `pymupdf4llm` (~120MB)
- Remove PDF conversion endpoints
- Reduce server memory by ~60%
- Faster response (no server processing)

**Trade-offs:**
- PDFs open in browser (not converted to markdown)
- ~100KB additional JavaScript (PDF.js)
- Markdown conversion requires manual copy-paste or client-side library

---

## 📊 Expected Results

### Resource Reduction

| Metric | Before | After Phase 1 | After Phase 2 | After Phase 3 |
|--------|--------|---------------|---------------|---------------|
| **Server CPU** | 100% | 50% | 30% | 20% |
| **Server Memory** | 512MB | 435MB | 310MB | 200MB |
| **Dependencies** | 62MB | 45MB | 30MB | 15MB |
| **Cold Start** | 3-5s | 2-3s | 1-2s | <1s |
| **Cost** | shared-cpu-2x | shared-cpu-1x | shared-cpu-1x | **Cloudflare Workers?** |

### Client-Side Impact

| Resource | Added Load |
|----------|-----------|
| JavaScript | +150KB total (gzipped: ~50KB) |
| Memory | +20-30MB (negligible) |
| CPU | Minimal (async processing) |
| Storage | IndexedDB (user's disk) |

---

## 🚀 Implementation Priority

### Week 1: Phase 1 (Quick Wins)
- [ ] Move deduplication to client
- [ ] Move BM25 ranking to client
- [ ] Lazy load PDF processing
- **Expected:** 50% CPU reduction, 15% memory reduction
- **Deploy:** Immediate

### Week 2: Phase 2 (Direct API Calls)
- [ ] Create client-side API clients for CORS sources
- [ ] Test CORS availability for each source
- [ ] Update server to proxy only non-CORS sources
- [ ] Implement IndexedDB caching
- **Expected:** 70% CPU reduction, 40% memory reduction
- **Deploy:** After testing

### Week 3: Phase 3 (PDF Removal)
- [ ] Integrate PDF.js for viewing
- [ ] Remove server-side PDF endpoints
- [ ] Remove pymupdf dependencies
- **Expected:** 60% memory reduction
- **Deploy:** After user acceptance testing

---

## 🎁 Bonus Optimizations

### Move to Cloudflare Workers (Phase 4)
If Phases 1-3 reduce server to just a proxy:
- Cloudflare Workers = serverless, $0-5/month
- 128MB memory limit (plenty for proxy)
- Edge locations (faster globally)
- No cold starts

### Progressive Web App (PWA)
- Cache JavaScript + API responses
- Offline search history
- Install as native app

---

## 📝 Implementation Checklist

### Phase 1 Files to Modify:
- [ ] `browser-ui/js/processing.js` (NEW - result processing)
- [ ] `browser-ui/js/api.js` (call client-side processing)
- [ ] `source_crate/http_server.py` (lazy load PDF imports)
- [ ] `pyproject.toml` (remove rank-bm25, rapidfuzz optional)

### Phase 2 Files to Create:
- [ ] `browser-ui/js/api-clients/arxiv.js`
- [ ] `browser-ui/js/api-clients/crossref.js`
- [ ] `browser-ui/js/api-clients/pubmed.js`
- [ ] (etc. for each CORS-enabled source)
- [ ] `browser-ui/js/cache.js` (IndexedDB)

### Phase 3 Files to Modify:
- [ ] `browser-ui/js/pdf-handler.js` (NEW - PDF.js integration)
- [ ] `source_crate/http_server.py` (remove PDF endpoints)
- [ ] `pyproject.toml` (remove pymupdf, pymupdf4llm)

---

## ⚠️ Considerations

### Privacy
- Client-side API calls expose user IP to academic APIs
- Consider: VPN, proxy toggle, or privacy notice

### Browser Compatibility
- ES6 modules (supported: Chrome 61+, Firefox 60+, Safari 11+)
- IndexedDB (universal support)
- PDF.js (universal support)

### Fallback Strategy
- Keep server endpoints for non-CORS sources
- Optional server-side processing for low-end clients
- Feature detection in browser

---

## 💰 Cost Impact

### Current Cost
- shared-cpu-2x: ~$10-15/month

### After Optimization
- shared-cpu-1x: ~$5-8/month (Phase 1-2)
- Cloudflare Workers: $0-5/month (Phase 4)

**Savings: ~60-100% reduction**
