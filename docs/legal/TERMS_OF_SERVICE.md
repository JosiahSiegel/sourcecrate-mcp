# Terms of Service

**Effective Date:** January 7, 2025
**Project:** PaperezMCP
**Repository:** <https://github.com/JosiahSiegel/paperez-mcp>

## 1. Acceptance of Terms

By using, downloading, or configuring PaperezMCP ("the Software"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, do not use the Software.

## 2. Description of Service

PaperezMCP is a Model Context Protocol (MCP) server that provides access to academic research databases and PDF processing capabilities. The Software includes default configurations that access only legally compliant academic data sources.

## 3. Default Source Compliance

### 3.1 Legally Compliant Default Sources

PaperezMCP's default configuration includes only sources that:
- Have official public APIs designed for academic research
- Allow programmatic access under their Terms of Service
- Comply with applicable rate limiting requirements
- Have been verified for legal academic use as of the effective date

### 3.2 Default Sources Included

The following sources are included in the default configuration:
- **Scientific & General:** OpenAlex, CrossRef, Semantic Scholar, arXiv, DOAJ, Fatcat/Internet Archive Scholar
- **Medical & Biomedical:** PubMed/PMC, Europe PMC, ClinicalTrials.gov, bioRxiv, medRxiv
- **Social Sciences:** OSF Preprints (includes SocArXiv, PsyArXiv, EarthArXiv)
- **Chemistry:** ChemRxiv
- **Business & Economics:** RePEc
- **Specialized Domains:** Open Library, CORE Repository (requires API key), CourtListener

All default sources have been verified for Terms of Service compliance and API availability as of January 7, 2025.

**API Testing Completed:** All enabled sources tested on January 7, 2025 to confirm JSON/XML API availability.

### 3.3 Domain Coverage Limitations

While PaperezMCP includes comprehensive free academic sources, certain research domains have inherently limited coverage in open-access databases. This is a fundamental constraint of free academic resources, not a limitation of the Software.

**Domains with Limited Free Coverage:**

- **Philosophy Research** - Core philosophy journals (Mind, Journal of Philosophy, Philosophical Review, Ethics) require subscriptions. Recommended sources: JSTOR, PhilPapers, Project MUSE, Philosopher's Index.

- **Historical Research** - Historical archives and specialized journals typically require institutional access. Recommended sources: JSTOR, Historical Abstracts, national archives.

- **Literary Studies** - Literature research requires specialized databases. Recommended sources: MLA International Bibliography, JSTOR, Project MUSE.

- **Fine Arts & Music** - Art and music scholarship databases require subscriptions. Recommended sources: Art Index, Music Index, JSTOR.

**Why These Limitations Exist:**

1. **Lower Open Access Adoption**: Humanities and social sciences have significantly lower open access publishing rates compared to STEM fields
2. **Book-Based Scholarship**: Much humanities research is published as books by university presses, not as papers in indexed journals
3. **Minimal Preprint Culture**: Humanities disciplines lack robust preprint servers like arXiv (which serves STEM)
4. **Journal Business Models**: Many core journals in these fields operate on subscription models

**Recommendation for These Domains:**

Users researching these domains should create custom configurations with institutional database access. The Software provides guidance through the `get_help()` function for adding authenticated sources. This approach ensures:
- Comprehensive coverage for specialized domains
- Compliance with institutional licensing agreements
- Access to subscription-only content where authorized

**System Behavior for Limited Domains:**

When searching these domains with default (free) sources, users may experience:
- Low result counts (0-5 papers)
- Results primarily from interdisciplinary sources (e.g., philosophy of science, philosophy of education)
- Recommendations to create custom configurations

This is expected and correct behavior given the constraints of free academic databases. The Software will proactively suggest custom configuration options when limited coverage is detected.

### 3.4 Free API Key Sources

The Software may recommend sources that require free API keys when default sources provide inadequate coverage. These recommendations are made to improve user experience and research outcomes across all disciplines.

**Policy on Free API Key Recommendations:**

The Software may recommend sources requiring free API keys when:
1. Default sources provide poor coverage (0-5 results or wrong discipline)
2. The API key is free to obtain with NO payment required
3. Signup process is simple (< 5 minutes, basic information only)
4. The source significantly improves coverage (5-10x more relevant papers)
5. Clear instructions and signup links are provided

**Examples of Free API Key Sources:**
- **CORE Repository** (https://core.ac.uk/services/api) - 9.5M+ papers, all disciplines, 2-3 min signup
- **Semantic Scholar** (https://www.semanticscholar.org/product/api) - 200M+ papers, cross-disciplinary
- **NASA ADS** (https://ui.adsabs.harvard.edu/user/settings/token) - Astronomy/astrophysics
- **Europe PMC** (optional key for higher rate limits) - Life sciences

**User Responsibilities for Free API Key Sources:**

Users who choose to enable sources requiring free API keys are responsible for:
- Obtaining and managing their own API keys
- Complying with the Terms of Service of the API provider
- Understanding and respecting rate limits and usage restrictions
- Keeping API keys secure and not sharing them
- Regularly reviewing the API provider's Terms of Service for changes

**Software Behavior:**

The Software will:
- Present free API key sources as DISABLED by default in custom configurations
- Provide clear documentation of benefits, limitations, and signup process
- Explain the trade-off (e.g., "2-3 min signup → 10x better coverage")
- Allow users to decide whether to enable these sources
- NOT automatically enable any source requiring an API key

**The Software will NOT recommend sources that:**
- Require payment or subscription fees
- Require institutional affiliation or complex verification
- Have Terms of Service that prohibit academic research use
- Have signup processes that are complex or require approval

**Disclaimer:**

The maintainers of PaperezMCP:
- Do not guarantee the availability or terms of third-party API services
- Are not responsible for changes to API terms, rate limits, or pricing
- Recommend users review each API provider's Terms of Service before signup
- Cannot provide support for third-party API services or account issues

Users should independently verify that any recommended source complies with their institutional policies and legal requirements before obtaining an API key.

## 4. Restricted Sources

### 4.1 Sources Excluded from Default Configuration

The following sources are explicitly excluded from default configurations due to Terms of Service restrictions or technical limitations:

- **Google Scholar** - No official API; web scraping prohibited
- **SSRN** - ToS restrictions on data mining
- **ResearchGate** - ToS prohibits automated data extraction
- **Academia.edu** - No public API; ToS prohibits scraping
- **Sci-Hub** - Copyright infringement concerns

### 4.2 User Responsibility for Modifications

Users who modify the default configuration or add custom sources assume full legal responsibility for:
- Compliance with all applicable Terms of Service
- Adherence to copyright laws and institutional policies
- Verification of legal authorization for data access
- Respect for rate limits and usage restrictions

## 5. Disclaimer of Liability

### 5.1 Scope of Responsibility

**PaperezMCP provides legal compliance warranties only for the default configuration as distributed.** The maintainers disclaim all liability for:
- User modifications to the configuration
- Custom sources added by users
- Third-party API changes or Terms of Service updates
- Data accessed through user-configured sources

### 5.2 No Warranty for Custom Configurations

Users who modify the Software's configuration or add custom data sources do so entirely at their own risk and legal responsibility. PaperezMCP maintainers provide no warranties, express or implied, regarding the legality of custom configurations.

## 6. User Obligations

### 6.1 Legal Compliance

Users must:
- Comply with all applicable laws, regulations, and institutional policies
- Respect the Terms of Service of all data sources accessed
- Obtain necessary permissions for accessing proprietary databases
- Use the Software only for legitimate academic and research purposes

### 6.2 Prohibited Uses

Users may not:
- Use the Software to violate any third-party Terms of Service
- Engage in bulk data harvesting that violates rate limits
- Access copyrighted content without proper authorization
- Distribute or republish restricted content

## 7. Intellectual Property

### 7.1 Software License

PaperezMCP is licensed under the MIT License. See the LICENSE file for complete terms.

### 7.2 Third-Party Content

Content accessed through PaperezMCP remains subject to the intellectual property rights and Terms of Service of the respective data sources. Users are responsible for compliance with all such terms.

## 8. Privacy and Data Handling

### 8.1 Local Processing

PaperezMCP processes data locally and does not transmit user queries or results to third parties except as necessary to access configured data sources according to their APIs.

### 8.2 Caching

The Software may cache API responses locally to improve performance and reduce load on data sources, in compliance with each source's caching policies.

## 9. Service Availability

### 9.1 No Guarantee of Availability

PaperezMCP depends on third-party APIs and services. We do not guarantee continuous availability of any data source and are not responsible for outages or changes to third-party services.

### 9.2 Updates and Changes

We may update the default configuration to maintain legal compliance, including disabling sources that change their Terms of Service or become non-compliant.

## 10. Indemnification

Users agree to indemnify and hold harmless the PaperezMCP maintainers from any claims, damages, or legal issues arising from:
- User modifications to the Software configuration
- Use of custom or unauthorized data sources
- Violation of third-party Terms of Service
- Non-compliance with applicable laws or regulations

## 11. Termination

These Terms remain in effect until terminated. Users may terminate their agreement at any time by ceasing use of the Software. We may terminate or restrict access if users violate these Terms.

## 12. Governing Law

These Terms are governed by the laws of the jurisdiction where the Software is developed and distributed, without regard to conflict of law principles.

## 13. Changes to Terms

We reserve the right to modify these Terms at any time. Continued use of the Software after changes constitutes acceptance of the modified Terms.

## 14. Contact Information

For questions about these Terms of Service, please contact the project maintainers through the GitHub repository.

## 15. Severability

If any provision of these Terms is found to be unenforceable, the remaining provisions will continue in full force and effect.

---

**Last Updated:** January 7, 2025
**Repository:** <https://github.com/JosiahSiegel/paperez-mcp>
