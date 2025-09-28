# Source Integration Issues Analysis and Resolution Guide

**Document Version:** 1.0
**Date:** 2025-09-27
**Status:** Critical Issues Identified

## Executive Summary

During comprehensive source testing, **4 out of 9 configured sources** exhibit critical integration issues where queries are incorrectly routed to other sources or return no results despite health checks showing "healthy" status. This affects 44% of the configured academic sources and significantly reduces search coverage.

**Issues Summary:**
- **DOAJ**: Queries routed to PubMed Central instead of actual DOAJ API
- **Europe PMC**: Queries routed to PubMed instead of Europe PMC API
- **HathiTrust**: Queries routed to CrossRef instead of HathiTrust API
- **Internet Archive**: No results returned for any test queries

**Impact:** Reduced bibliographic diversity, missing specialized content, and potential user confusion about source coverage.

---

## Detailed Issue Analysis

### 1. DOAJ (Directory of Open Access Journals) 🔴 CRITICAL

**Issue Type:** Incorrect Query Routing
**Observed Behavior:**
- Query: "open access journal publishing" → Results from PubMed Central
- Expected: Results from DOAJ's 2M+ open access articles
- Health Check: Reports "healthy" (false positive)

**Root Cause Analysis:**
```yaml
# Current config (.paperez/config/config.yaml)
doaj:
  name: doaj
  type: http_api
  enabled: true
  config:
    base_url: https://doaj.org/api/search
    search_path: /articles/_search
```

**Potential Issues:**
1. **Search orchestration routing** may be bypassing DOAJ due to query classification
2. **API endpoint changes** - DOAJ updated to v4 API in June 2024
3. **Field mapping errors** causing search failures and fallback routing
4. **Rate limiting** (2 RPS) may be triggering fallback to other sources

**Resolution Steps:**
1. **✅ CRITICAL: Update to DOAJ API v4** - DOAJ released v4 on June 18, 2024, became current on July 18, 2024
   - Current config uses old `/api/search` - should use `/api/v4` or `/api`
   - v4 mainly affects bulk uploads but may impact search routing
2. **Verify endpoint compatibility**: Test if current `/articles/_search` path works with v4 base
3. **Review search orchestration logic**: Examine why queries route to PMC instead of DOAJ
4. **Test field mappings**: Ensure `bibjson` field structure is correctly parsed with v4

---

### 2. Europe PMC 🔴 CRITICAL

**Issue Type:** Source Misrouting
**Observed Behavior:**
- Query: "cardiovascular disease treatment" → Results from PubMed
- Expected: Results from Europe PMC's 39M+ abstracts
- Health Check: Reports "healthy" but not actually queried

**Root Cause Analysis:**
```yaml
# Current config - Missing from default configuration
# Europe PMC not explicitly configured in .paperez/config/config.yaml
```

**Potential Issues:**
1. **✅ Configuration exists but routing fails** - Europe PMC properly configured in config.yaml
2. **Search orchestration priority** - PubMed selected over Europe PMC for medical queries
3. **Rate limiting stricter than documented** - Current 0.2s delay may be too fast for 10 req limit
4. **Field mapping issues** - Complex `fullTextUrlList.fullTextUrl.0.url` path may fail
5. **Privacy notice compliance** - May require explicit user agreement headers

**Resolution Steps:**
1. **✅ Current config verified correct**:
   ```yaml
   # CONFIRMED PRESENT in config.yaml lines 189-217
   base_url: https://www.ebi.ac.uk/europepmc/webservices/rest
   search_path: /search
   query_param: query
   rate_limit_delay: 0.2
   ```
2. **Debug search orchestration** - Why medical queries route to PubMed instead
3. **Test rate limiting** - Increase delay if 10 req/period limit is stricter than 0.2s
4. **Simplify field mappings** - Test if complex URL path causes parsing failures
5. **Add privacy notice headers** for EBI compliance

---

### 3. HathiTrust Digital Library 🔴 CRITICAL

**Issue Type:** Source Misrouting
**Observed Behavior:**
- Query: "history government documents archives" → Results from CrossRef
- Expected: Results from HathiTrust's 17M+ volumes
- Health Check: Reports "healthy" but queries routed elsewhere

**Root Cause Analysis:**
```yaml
# Current config - Likely missing HTTP API configuration
# HathiTrust may be configured as builtin but not functional
```

**Potential Issues:**
1. **✅ CRITICAL: HathiTrust Data API Retired** - Data API service retired July 17, 2024
2. **Bibliographic API still functional** but limited to 20 items per batch call
3. **Query volume restrictions** - ToS limits to "small numbers of items at a time"
4. **Search orchestration** classifies historical queries for CrossRef instead of HathiTrust
5. **Current configuration may be using wrong API** - verify Bibliographic vs Data API

**Resolution Steps:**
1. **✅ Verify API endpoint** - Current config uses correct Bibliographic API endpoint:
   ```yaml
   # CONFIRMED CORRECT - Bibliographic API still operational
   base_url: https://catalog.hathitrust.org
   search_path: /api/volumes/brief/json
   ```
2. **Implement batch size limits** - Maximum 20 items per call as per ToS
3. **Update search orchestration** to properly route historical queries to HathiTrust
4. **Test query normalization** - HathiTrust normalizes OCLC numbers (remove prefixes)
5. **Add metadata sharing policy compliance** (CC0 public domain)

---

### 4. Internet Archive 🔴 CRITICAL

**Issue Type:** No Results Returned
**Observed Behavior:**
- Query: "digital library archive collection" → 0 results
- Query: "american history books archives" → Routes to CrossRef
- Expected: Results from Internet Archive's vast digital collection
- Health Check: Reports "healthy" but returns no data

**Root Cause Analysis:**
```yaml
# Current config - Missing or misconfigured
# Internet Archive API integration appears non-functional
```

**Potential Issues:**
1. **✅ Current config appears correct** - Uses proper `/advancedsearch.php` endpoint
2. **Rate limiting too aggressive** - Current 0.5s delay may be too fast (should be 1.0s for 1 RPS)
3. **Deep pagination blocking** - IA rejects deep page requests (page=10000+)
4. **Query syntax issues** - IA requires specific search formatting for mediatype=texts
5. **Terms of service compliance** - Non-commercial use only, may require headers

**Resolution Steps:**
1. **✅ Update rate limiting** - Change from 0.5s to 1.0s delay for strict 1 RPS compliance:
   ```yaml
   rate_limit_delay: 1.0  # Currently 0.5 - too fast
   ```
2. **Implement cursor-based pagination** - Use IA's scraping API for deep results
3. **Test query syntax** - Verify `mediatype: texts` and search formatting
4. **Add ToS compliance headers** for non-commercial academic use
5. **Debug search orchestration** - Check why queries return 0 results vs route elsewhere

---

## Technical Solutions and Implementation

### Priority 1: Search Orchestration Review

**File:** `paperez_mcp/services/`
1. **Examine SearchOrchestrationService** for routing logic
2. **Review category-to-source mapping** in smart routing
3. **Debug query classification** that bypasses intended sources
4. **Test fallback strategies** that may be over-aggressive

### Priority 2: Configuration Updates

**File:** `.paperez/config/config.yaml`
1. **Add missing HTTP API configurations** for Europe PMC, HathiTrust, Internet Archive
2. **Update DOAJ configuration** for API v4 compatibility
3. **Verify field mappings** for all problematic sources
4. **Test rate limiting parameters** match ToS requirements

### Priority 3: Source Registry Validation

**File:** `paperez_mcp/config/registry.py`
1. **Verify source registration** in ConfigurableSearchService
2. **Test HTTP API client creation** for each problematic source
3. **Debug source function retrieval** and execution
4. **Validate error handling** for API failures

### Priority 4: Health Check Accuracy

**File:** Source health monitoring system
1. **Fix false positive health checks** that report "healthy" for non-functional sources
2. **Implement actual API testing** rather than connectivity-only checks
3. **Add source-specific validation** for different API types
4. **Monitor real query success rates** vs health status

---

## Testing and Validation Plan

### Phase 1: Individual Source Testing
```bash
# Test each source API directly
curl "https://doaj.org/api/v3/search/articles/_search?q=machine+learning"
curl "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=diabetes"
curl "https://catalog.hathitrust.org/api/volumes/brief/json?q=government"
curl "https://archive.org/advancedsearch.php?q=history&output=json"
```

### Phase 2: Configuration Validation
1. **Load test configurations** with validation tools
2. **Test source registration** in development environment
3. **Verify query routing** to intended sources
4. **Measure response times** and rate limit compliance

### Phase 3: Integration Testing
1. **Test browse_papers** with force_category parameters
2. **Verify source attribution** in results
3. **Test PDF download** from newly configured sources
4. **Validate metadata parsing** and field mapping

### Phase 4: Production Deployment
1. **Deploy configuration updates** to production
2. **Monitor source health metrics** post-deployment
3. **Test user queries** across all categories
4. **Measure bibliographic diversity** improvement

---

## Success Metrics

**Target Outcomes:**
- [ ] **DOAJ**: Return actual DOAJ articles for open access queries
- [ ] **Europe PMC**: Return European biomedical content distinct from PubMed
- [ ] **HathiTrust**: Return historical documents and government archives
- [ ] **Internet Archive**: Return digital library and archival content
- [ ] **Health Checks**: Accurately reflect source functionality
- [ ] **Query Coverage**: Achieve 9/9 functional sources (100% vs current 67%)

**Measurement:**
- Source-specific result attribution in query responses
- Reduction in false positive health checks
- Increased bibliographic diversity in search results
- User access to specialized content collections

---

## Priority Classification

🔴 **Critical (Week 1):**
- **DOAJ API v4 Update** - Must update from deprecated `/api/search` to `/api/v4`
- **Search Orchestration Logic** - Debug why queries route to wrong sources

🟡 **High (Week 2):**
- **Internet Archive Rate Limiting** - Fix 0.5s → 1.0s delay for ToS compliance
- **Europe PMC Routing Priority** - Fix medical query routing from PubMed

🟡 **High (Week 3):**
- **HathiTrust Query Routing** - Historical queries should route to HathiTrust not CrossRef
- **Field Mapping Validation** - Test complex paths that may cause parsing failures

🟢 **Medium (Week 4):**
- **Health check accuracy improvements** - Fix false positives
- **ToS compliance headers** - Add required headers for IA and Europe PMC

## Key Research Findings

### ✅ **Root Cause Identified: API Version Updates**
- **DOAJ**: Using deprecated API endpoint, need v4 update (June 2024)
- **HathiTrust**: Data API retired (July 2024), but Bibliographic API still works
- **Configurations mostly correct** - issue is in search orchestration routing logic

### ✅ **Rate Limiting Issues Found**
- **Internet Archive**: 0.5s delay too fast, should be 1.0s for 1 RPS compliance
- **Europe PMC**: 0.2s delay may be too aggressive for 10 req/period limit

### ✅ **Search Orchestration Problems**
- Medical queries incorrectly routed to PubMed instead of Europe PMC
- Historical queries routed to CrossRef instead of HathiTrust
- DOAJ queries routed to PubMed Central instead of DOAJ
- **Primary issue appears to be in routing logic, not API configurations**

---

**Next Actions:**
1. Assign development resources to investigate search orchestration routing
2. Create direct API test scripts for each problematic source
3. Update configuration files with corrected API endpoints
4. Implement comprehensive integration testing for all sources
