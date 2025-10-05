# Terms of Service Compliance Documentation

**Last Updated:** January 7, 2025
**Last Review:** January 7, 2025

This document verifies ToS compliance for all academic data sources used in PaperezMCP.

---

## ✅ Environment Variables for ToS Compliance

All required environment variables are now automatically supported:

### Required for Enhanced Functionality:
```bash
# OpenAlex - Unlimited rate limits with polite pool
fly secrets set OPENALEX_EMAIL=your.email@example.com

# Unpaywall - 30M+ open access PDF discovery
fly secrets set UNPAYWALL_EMAIL=your.email@example.com
```

### How It Works:
1. **Environment variable substitution** in YAML configs using `${VAR_NAME}` syntax
2. **Automatic expansion** in `generic_http_client.py` via `_expand_env_vars()` method
3. **Unpaywall integration** automatically uses `UNPAYWALL_EMAIL` via `get_unpaywall_client()`

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

---

## 🔧 PDF Enhancement Services (Not Search Sources)

### Unpaywall
- **Type:** PDF discovery service (used during downloads, not searches)
- **ToS:** CC0 public domain, commercial use explicitly allowed
- **Rate Limits:** 100K calls/day
- **Coverage:** 30M+ open access papers
- **Configuration:** Automatic via `UNPAYWALL_EMAIL` environment variable
- **Integration:** `paperez_mcp/utils/unpaywall_client.py`
- **Usage:** Automatically tries to find open access PDFs when downloads fail (403/404 errors)
- **Status:** ✅ Fully compliant, **ENHANCED**

**How Unpaywall Works:**
1. When a PDF download fails (403/404), the system checks if a DOI is available
2. If DOI exists, queries Unpaywall API for open access alternatives
3. Tries each alternative PDF URL with proper headers
4. Uses `UNPAYWALL_EMAIL` from environment variable for API requests
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
| **Default Enabled Sources** | 13 | ✅ All compliant |
| **PDF Enhancement Services** | 1 (Unpaywall) | ✅ Compliant |
| **Disabled (No API)** | 4 | ⚠️ Not available |
| **Optional (Free API Key)** | 1 (CORE) | ✅ Compliant |
| **Total Available Sources** | 14 | ✅ 100% compliant |

---

## 🚀 Implementation Details

### Environment Variable Substitution
**File:** `paperez_mcp/api_clients/generic_http_client.py`

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
**File:** `paperez_mcp/default_configs/medical.yaml`

```yaml
openalex:
  name: openalex
  type: http_api
  enabled: true
  config:
    extra_params:
      mailto: ${OPENALEX_EMAIL}  # Auto-populated from environment
```

### Unpaywall Configuration
**File:** `paperez_mcp/utils/unpaywall_client.py`

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
        final_email = email or os.getenv("UNPAYWALL_EMAIL", "research@paperez-mcp.org")
        _unpaywall_client = UnpaywallClient(email=final_email)
        logger.info(f"Initialized Unpaywall client with email: {final_email}")
    return _unpaywall_client
```

---

## ✅ Verification Checklist

- [x] All default sources have verified ToS allowing academic use
- [x] All default sources have publicly documented APIs
- [x] All rate limits are respected via built-in delays
- [x] Attribution requirements met via User-Agent headers
- [x] Email registration completed where required (via env vars)
- [x] Environment variable support for OpenAlex polite pool
- [x] Environment variable support for Unpaywall email
- [x] Automatic fallback when env vars not set
- [x] Example configuration provided for users
- [x] Documentation updated with ToS compliance info

---

## 📞 Contact for ToS Questions

If you have questions about ToS compliance:
1. Review this document
2. Check `config.example.yaml` for detailed source information
3. Consult individual source documentation (linked in configs)
4. File an issue at https://github.com/JosiahSiegel/paperez-mcp/issues

---

**Last Review:** January 7, 2025
**Next Review:** July 7, 2025 (6 months)
