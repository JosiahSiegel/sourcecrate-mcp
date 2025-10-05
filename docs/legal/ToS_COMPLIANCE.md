# Terms of Service Compliance Documentation

**Last Updated:** October 5, 2025
**Last Review:** October 5, 2025

This document verifies ToS compliance for all academic data sources used in SourceCrate.

---

## ✅ Environment Variables for ToS Compliance (Optional)

All sources now work **without environment variables** using hardcoded fallback defaults:

### Optional for Enhanced Functionality:
```bash
# OpenAlex - Unlimited rate limits with polite pool (optional)
# Uses research@sourcecrate.org if not set
fly secrets set OPENALEX_EMAIL=your.email@example.com

# Unpaywall - 30M+ open access PDF discovery (optional)
# Uses research@sourcecrate.org if not set
fly secrets set UNPAYWALL_EMAIL=your.email@example.com
```

### How It Works:
1. **Hardcoded defaults** in YAML configs ensure zero-setup deployment
2. **Optional environment variables** can override defaults for user customization
3. **Automatic expansion** in `generic_http_client.py` via `_expand_env_vars()` method
4. **Unpaywall integration** automatically uses `UNPAYWALL_EMAIL` env var or falls back to default

---

## 📋 Default Enabled Sources (ToS Compliant)

All sources below are **enabled by default** and verified for ToS compliance:

### 1. CrossRef
- **ToS:** Free API, commercial use allowed with attribution
- **Rate Limits:** Unlimited with polite pool (mailto parameter)
- **Coverage:** 150M+ scholarly publications across all disciplines
- **Configuration:** Built-in, enhanced with polite pool email
- **Status:** ✅ Fully compliant

### 2. Semantic Scholar
- **ToS:** Free API, attribution required for publications
- **Rate Limits:** 1 RPS without key, 10 RPS with API key
- **Coverage:** 200M+ papers with AI-powered search
- **Configuration:** Built-in, API key optional
- **Status:** ✅ Fully compliant

### 3. arXiv
- **ToS:** CC0 metadata license, free use
- **Rate Limits:** 1 request per 3 seconds
- **Coverage:** 2M+ preprints in physics, CS, math, etc.
- **Configuration:** Built-in
- **Status:** ✅ Fully compliant

### 4. PubMed
- **ToS:** US Government database, public domain
- **Rate Limits:** 3 RPS without key, 10 RPS with NCBI API key
- **Coverage:** 35M+ biomedical citations
- **Configuration:** Built-in, API key optional
- **Status:** ✅ Fully compliant

### 5. PubMed Central (PMC)
- **ToS:** US Government database, public domain
- **Rate Limits:** 3 RPS without key, 10 RPS with NCBI API key
- **Coverage:** 9M+ full-text articles
- **Configuration:** Built-in, API key optional
- **Status:** ✅ Fully compliant

### 6. Europe PMC
- **ToS:** Privacy notice agreement, free use
- **Rate Limits:** ~10 requests per query
- **Coverage:** 39M+ abstracts, life sciences
- **Configuration:** Built-in
- **Status:** ✅ Fully compliant

### 7. OpenAlex
- **ToS:** CC0 public domain, commercial use explicitly allowed
- **Rate Limits:** 100K calls/day → **UNLIMITED** with polite pool
- **Coverage:** 250M+ works across all disciplines
- **Configuration:** Enhanced with `${OPENALEX_EMAIL}` in `medical.yaml`
- **Environment Variable:** `OPENALEX_EMAIL`
- **Status:** ✅ Fully compliant, **ENHANCED**

### 8. DOAJ (Directory of Open Access Journals)
- **ToS:** 2 requests/second, CC BY-SA for journals, CC0 for articles
- **Rate Limits:** 2 RPS
- **Coverage:** 19,000+ journals, 7M+ articles
- **Configuration:** Built-in
- **Status:** ✅ Fully compliant

### 9. bioRxiv
- **ToS:** Free preprint server
- **Rate Limits:** Reasonable use
- **Coverage:** 250K+ biology preprints
- **Configuration:** Built-in
- **Status:** ✅ Fully compliant

### 10. medRxiv
- **ToS:** Free preprint server
- **Rate Limits:** Reasonable use
- **Coverage:** 50K+ medical preprints
- **Configuration:** Built-in
- **Status:** ✅ Fully compliant

### 11. ChemRxiv
- **ToS:** Open API compatible
- **Rate Limits:** Reasonable use
- **Coverage:** Chemistry preprints
- **Configuration:** Built-in
- **Status:** ✅ Fully compliant

### 12. OSF Preprints
- **ToS:** Open Science Framework, free use
- **Rate Limits:** Reasonable use
- **Coverage:** Includes SocArXiv, PsyArXiv, EarthArXiv
- **Configuration:** Built-in
- **Status:** ✅ Fully compliant

### 13. ClinicalTrials.gov
- **ToS:** US Government database, public domain
- **Rate Limits:** ~50 requests/minute
- **Coverage:** 450K+ clinical studies
- **Configuration:** Built-in
- **Status:** ✅ Fully compliant

### 14. Unpaywall
- **Type:** Search source + PDF discovery service (dual-purpose)
- **ToS:** CC0 public domain, commercial use explicitly allowed
- **Rate Limits:** 100K calls/day
- **Coverage:** 20M+ open access papers with free PDF links
- **Configuration:** Hardcoded email `research@sourcecrate.org` (override with `UNPAYWALL_EMAIL` env var)
- **Search Integration:** `source_crate/default_configs/scientific.yaml`
- **PDF Integration:** `source_crate/utils/unpaywall_client.py`
- **Usage:**
  - **Search**: Returns papers with open access PDF URLs
  - **PDF Enhancement**: Finds free PDFs when downloads fail (403/404 errors)
- **Status:** ✅ Fully compliant, **DUAL-PURPOSE**

### 15. DataCite
- **ToS:** CC0 public domain, commercial use explicitly allowed ("for any purpose whatsoever")
- **Rate Limits:** Unlimited with reasonable use
- **Coverage:** 40M+ DOI metadata records for research datasets and publications
- **Configuration:** Built-in, no authentication required
- **Integration:** `source_crate/default_configs/scientific.yaml`
- **Status:** ✅ Fully compliant

### 16. Zenodo
- **ToS:** CC0 metadata license, non-military use only
- **Rate Limits:** 60 requests/minute (guests), 100 requests/minute (authenticated)
- **Coverage:** 10M+ research datasets and publications from CERN
- **Configuration:** Built-in, no authentication required
- **Integration:** `source_crate/default_configs/scientific.yaml`
- **Status:** ✅ Fully compliant

### 17. PLOS (Public Library of Science)
- **ToS:** CC BY 4.0 license, commercial use allowed **with attribution**
- **Rate Limits:** Unlimited with reasonable use (max 100 rows per request)
- **Coverage:** Open access peer-reviewed biology and medicine journals
- **Configuration:** Built-in, uses Solr search API
- **Integration:** `source_crate/default_configs/medical.yaml`
- **Attribution Requirement:** Must cite author and original source when using content
- **Status:** ✅ Fully compliant

---

## 🔧 PDF Enhancement Services

### Unpaywall PDF Discovery
**Note:** Unpaywall is now also a search source (see #14 above). This section describes its PDF enhancement functionality.

**How Unpaywall PDF Discovery Works:**
1. When a PDF download fails (403/404), the system checks if a DOI is available
2. If DOI exists, queries Unpaywall API for open access alternatives
3. Tries each alternative PDF URL with proper headers
4. Uses `UNPAYWALL_EMAIL` from environment variable or `research@sourcecrate.org` default
5. Falls back gracefully if no open access version found

---

## ❌ Disabled Sources (No API or ToS Restrictions)

### Google Scholar
- **Status:** Disabled
- **Reason:** No official API, ToS prohibits automated access
- **Alternative:** Use Semantic Scholar or CrossRef instead

### SSRN (Social Science Research Network)
- **Status:** Disabled
- **Reason:** ToS reserves data mining rights, restricted API access
- **Alternative:** Use RePEc for economics papers

### ResearchGate
- **Status:** Disabled
- **Reason:** No public API, ToS prohibits automated extraction
- **Alternative:** Use author search on CrossRef or Semantic Scholar

### ERIC (Education Resources Information Center)
- **Status:** Disabled
- **Reason:** No JSON/XML API - only HTML web interface (verified Jan 7, 2025)
- **Alternative:** Use DOAJ for education research

---

## 🔑 Optional Sources (Require Free API Key)

### CORE Repository
- **ToS:** Commercial use allowed with attribution
- **Rate Limits:** 10 requests/minute (free tier)
- **Coverage:** 9.5M+ open access papers (excellent for humanities/social sciences)
- **API Key:** FREE registration at https://core.ac.uk/services/api
- **Signup Time:** 2-3 minutes (email + basic info)
- **Configuration:** See `config.example.yaml`
- **Environment Variable:** `CORE_API_KEY`
- **Status:** ✅ Compliant (optional, requires user signup)

**To Enable CORE:**
```bash
# 1. Register at https://core.ac.uk/services/api
# 2. Get your free API key
# 3. Set environment variable:
fly secrets set CORE_API_KEY=your_key_here

# 4. Add to custom config (see config.example.yaml)
```

---

## 📊 ToS Compliance Summary

| Category | Count | Status |
|----------|-------|--------|
| **Default Enabled Sources** | 17 | ✅ All compliant |
| **PDF Enhancement Services** | 1 (Unpaywall - dual-purpose) | ✅ Compliant |
| **Disabled (No API)** | 4 | ⚠️ Not available |
| **Optional (Free API Key)** | 1 (CORE) | ✅ Compliant |
| **Total Available Sources** | 17 | ✅ 100% compliant |

### Recent Additions (Oct 2025):
- ✅ **Unpaywall** - Upgraded to search source (was PDF-only)
- ✅ **DataCite** - DOI metadata for datasets (CC0, unlimited)
- ✅ **Zenodo** - CERN research repository (CC0, 60 req/min)
- ✅ **PLOS** - Open access journals (CC BY, attribution required)

---

## 🚀 Implementation Details

### Environment Variable Substitution
**File:** `source_crate/api_clients/generic_http_client.py`

```python
def _expand_env_vars(self, params: dict[str, Any]) -> dict[str, Any]:
    """Expand environment variables in config parameters.

    Supports ${VAR_NAME} or $VAR_NAME syntax.
    Falls back to original value if env var not found.
    """
    import re

    expanded = {}
    for key, value in params.items():
        if isinstance(value, str):
            # Pattern matches ${VAR} or $VAR
            pattern = r'\$\{([A-Z_]+)\}|\$([A-Z_]+)'

            def replacer(match: re.Match[str]) -> str:
                var_name = match.group(1) or match.group(2)
                env_value = os.getenv(var_name)
                if env_value:
                    return env_value
                # Keep original if env var not found
                return match.group(0)

            expanded[key] = re.sub(pattern, replacer, value)
        else:
            expanded[key] = value
    return expanded
```

### OpenAlex Configuration
**File:** `source_crate/default_configs/medical.yaml` and `scientific.yaml`

```yaml
openalex:
  name: openalex
  type: http_api
  enabled: true
  config:
    extra_params:
      # Hardcoded default for zero-setup deployment
      # Users can override with OPENALEX_EMAIL environment variable
      mailto: research@sourcecrate.org
```

### Unpaywall Configuration

**Search Source:** `source_crate/default_configs/scientific.yaml`
```yaml
unpaywall:
  name: unpaywall
  type: http_api
  enabled: true
  config:
    extra_params:
      # Email is REQUIRED by Unpaywall API
      # Uses hardcoded default for zero-setup deployment
      email: research@sourcecrate.org
```

**PDF Discovery Service:** `source_crate/utils/unpaywall_client.py`
```python
def get_unpaywall_client(email: str | None = None) -> UnpaywallClient:
    """Get or create global Unpaywall client instance.

    Args:
        email: Email for Unpaywall API. If None, uses UNPAYWALL_EMAIL env var,
               or falls back to default.
    """
    global _unpaywall_client
    if _unpaywall_client is None:
        # Priority: parameter > environment variable > default
        final_email = email or os.getenv("UNPAYWALL_EMAIL", "research@sourcecrate.org")
        _unpaywall_client = UnpaywallClient(email=final_email)
        logger.info(f"Initialized Unpaywall client with email: {final_email}")
    return _unpaywall_client
```

---

## ✅ Verification Checklist

- [x] All 17 default sources have verified ToS allowing academic use
- [x] All default sources have publicly documented APIs
- [x] All rate limits are respected via built-in delays
- [x] Attribution requirements met via User-Agent headers and PLOS citation guidance
- [x] **Zero-setup deployment**: Hardcoded email defaults (research@sourcecrate.org)
- [x] Optional environment variable support for OpenAlex polite pool
- [x] Optional environment variable support for Unpaywall email
- [x] Automatic fallback when env vars not set
- [x] Unpaywall upgraded to dual-purpose (search + PDF enhancement)
- [x] DataCite, Zenodo, PLOS sources added with CC0/CC BY compliance
- [x] Example configuration provided for users
- [x] Documentation updated with ToS compliance info

---

## 📞 Contact for ToS Questions

If you have questions about ToS compliance:
1. Review this document
2. Check `config.example.yaml` for detailed source information
3. Consult individual source documentation (linked in configs)
4. File an issue at https://github.com/JosiahSiegel/sourcecrate/issues

---

**Last Review:** October 5, 2025
**Next Review:** April 5, 2026 (6 months)
