// ============================================================================
// PaperezMCP Browser UI - JavaScript Client
// ============================================================================
//
// File Structure:
// 1. STATE MANAGEMENT - Global state variables
// 2. FILTERING AND SORTING UTILITIES - Reusable filter/sort functions
// 3. RENDERING UTILITIES - Paper card building and display functions
// 4. SSE STREAMING SEARCH - Server-sent events handling
// 5. EVENT HANDLERS - Form submission handlers
// 6. SYSTEM STATUS - Status check functionality
// 7. INITIALIZATION - DOMContentLoaded setup and live filter listeners
//
// ============================================================================

// API Configuration with Smart Auto-Detection
// For production deployment, set window.PAPEREZ_API_URL before loading this script:
// <script>window.PAPEREZ_API_URL = 'https://your-api.onrender.com';</script>
// Or create a config.js file with: window.PAPEREZ_API_URL = 'https://...';

/**
 * Smart API URL detection with fallback chain:
 * 1. Explicit window.PAPEREZ_API_URL (highest priority)
 * 2. Auto-detect based on current page port (dev container friendly)
 * 3. Default to localhost:8000
 */
function getApiUrl() {
    // 1. Check explicit config (highest priority)
    if (window.PAPEREZ_API_URL) {
        return window.PAPEREZ_API_URL;
    }

    // 2. Auto-detect based on current page URL (dev container friendly)
    const currentPort = window.location.port;
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;

    // Production deployment: no port or standard HTTP(S) ports → use same origin
    if (!currentPort || currentPort === '80' || currentPort === '443') {
        return `${protocol}//${hostname}`;
    }

    if (currentPort === '3000') {
        // UI on 3000, API on 9000 (standard dev setup)
        return `${protocol}//${hostname}:9000`;
    } else if (currentPort === '3001') {
        // UI forwarded to 3001, API on 9000 (devcontainer)
        return `${protocol}//${hostname}:9000`;
    }

    // 3. Default fallback
    return 'http://localhost:9000';
}

const API_BASE_URL = getApiUrl();
console.log(`[Paperez] Using API URL: ${API_BASE_URL}`);

// ============================================================================
// 1. DOWNLOAD RELIABILITY TRACKING (CLIENT-SIDE)
// ============================================================================

/**
 * Client-side download reliability tracker using localStorage.
 * Learns which domains work/fail for THIS specific browser/network.
 * Scales to infinite users - zero server load.
 */
const DownloadReliability = {
    PREFIX: 'paperez_reliability_',
    TTL: 24 * 60 * 60 * 1000, // 24 hours
    MAX_ENTRIES: 1000, // Prevent localStorage bloat

    getDomain(url) {
        try {
            return new URL(url).hostname.toLowerCase();
        } catch {
            return null;
        }
    },

    getStats(url) {
        const domain = this.getDomain(url);
        if (!domain) return null;

        const key = this.PREFIX + domain;
        const stored = localStorage.getItem(key);
        if (!stored) return { attempts: 0, successes: 0, success_rate: 0.0 };

        try {
            const data = JSON.parse(stored);
            // Check TTL
            if (Date.now() - data.timestamp > this.TTL) {
                localStorage.removeItem(key);
                return { attempts: 0, successes: 0, success_rate: 0.0 };
            }
            return data.stats;
        } catch {
            return { attempts: 0, successes: 0, success_rate: 0.0 };
        }
    },

    recordAttempt(url, success) {
        const domain = this.getDomain(url);
        if (!domain) return;

        const key = this.PREFIX + domain;
        const stats = this.getStats(url);

        stats.attempts += 1;
        if (success) stats.successes += 1;
        stats.success_rate = stats.attempts > 0 ? stats.successes / stats.attempts : 0.0;

        try {
            localStorage.setItem(key, JSON.stringify({
                stats: stats,
                timestamp: Date.now()
            }));
            this.enforceLimit();
        } catch (e) {
            console.warn('Failed to save reliability stats:', e);
        }
    },

    enforceLimit() {
        // Prevent localStorage from growing unbounded
        const keys = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.PREFIX)) {
                keys.push(key);
            }
        }

        if (keys.length > this.MAX_ENTRIES) {
            // Remove oldest entries
            const entries = keys.map(key => {
                try {
                    const data = JSON.parse(localStorage.getItem(key));
                    return { key, timestamp: data.timestamp || 0 };
                } catch {
                    return { key, timestamp: 0 };
                }
            });
            entries.sort((a, b) => a.timestamp - b.timestamp);
            const toRemove = entries.slice(0, keys.length - this.MAX_ENTRIES);
            toRemove.forEach(entry => localStorage.removeItem(entry.key));
        }
    },

    getReliability(url) {
        const stats = this.getStats(url);
        if (!stats) return 'downloadable';

        const { attempts, success_rate } = stats;

        if (success_rate < 0.2 && attempts >= 5) {
            return 'browser_required';
        } else if (success_rate < 0.5 && attempts >= 10) {
            return 'unreliable';
        } else {
            return 'downloadable';
        }
    }
};

/**
 * Track download attempt when user clicks download button.
 * Uses optimistic recording - assumes success unless proven otherwise.
 */
window.trackDownloadAttempt = function(pdfUrl, downloadId) {
    // Optimistically record as success (user initiated download)
    // Note: We can't reliably detect if download actually succeeded due to browser security
    // But we can detect if the URL is accessible
    DownloadReliability.recordAttempt(pdfUrl, true);

    // Optional: HEAD request to check if URL is accessible
    // This helps detect 403/404 errors before user clicks
    setTimeout(() => {
        fetch(pdfUrl, { method: 'HEAD', mode: 'no-cors' })
            .then(() => {
                // URL is accessible (or CORS blocked us - assume OK)
                console.log(`Download initiated: ${DownloadReliability.getDomain(pdfUrl)}`);
            })
            .catch(() => {
                // Network error or URL inaccessible
                DownloadReliability.recordAttempt(pdfUrl, false);
                console.warn(`Download may have failed: ${DownloadReliability.getDomain(pdfUrl)}`);
            });
    }, 1000);
};

// Show status message
function showStatus(message, type = 'info') {
    const statusIndicator = document.getElementById('statusIndicator');
    statusIndicator.textContent = message;
    statusIndicator.className = `status-indicator ${type}`;
    statusIndicator.style.display = 'block';

    // Auto-hide success/error messages after 5 seconds
    if (type !== 'loading') {
        setTimeout(() => {
            statusIndicator.style.display = 'none';
        }, 5000);
    }
}

// Format date
function formatDate(year) {
    return year ? year : 'N/A';
}

// Render search results
function renderResults(data) {
    const resultsDiv = document.getElementById('results');

    if (!data.results || data.results.length === 0) {
        resultsDiv.innerHTML = '<p class="no-results">No papers found. Try a different query.</p>';
        return;
    }

    let html = '';
    html += `<div class="results-summary">
        <p>Found <strong>${data.total_found}</strong> papers from sources: ${data.sources_used ? data.sources_used.join(', ') : 'N/A'}</p>
    </div>`;

    data.results.forEach((paper, index) => {
        // Use the unified buildPaperCard function for consistent styling
        html += buildPaperCard(paper, index, false);
    });

    resultsDiv.innerHTML = html;
}

// ============================================================================
// STATE MANAGEMENT
// ============================================================================
let currentEventSource = null;
let streamingResults = [];
let papersByKey = new Map(); // Deduplication map: key → merged paper
let sourcesCompleted = 0;
let totalSources = 0;
let pdfOnlyFilter = false;
let relevanceThreshold = 45; // Default 45%

// ============================================================================
// FILTERING AND SORTING UTILITIES
// ============================================================================

// Apply filters to results
function applyFilters(results) {
    let filtered = results;

    // Filter by PDF availability
    if (pdfOnlyFilter) {
        filtered = filtered.filter(paper =>
            isValidPdfUrl(paper.pdf_url) || isValidPdfUrl(paper.open_access_pdf)
        );
    }

    // Filter by relevance threshold
    filtered = filtered.filter(paper => {
        if (paper.relevance_score === undefined || paper.relevance_score === null) {
            return true; // Keep papers without relevance scores
        }
        const percentage = Math.round(paper.relevance_score * 100);
        return percentage >= relevanceThreshold;
    });

    return filtered;
}

// Sort results by relevance score (descending), then by title (ascending)
function sortByRelevance(results) {
    return results.sort((a, b) => {
        const scoreA = a.relevance_score !== undefined ? a.relevance_score : 0;
        const scoreB = b.relevance_score !== undefined ? b.relevance_score : 0;

        // Primary sort: relevance score descending
        if (scoreB !== scoreA) {
            return scoreB - scoreA;
        }

        // Secondary sort: title ascending (keeps papers with same title together)
        const titleA = (a.title || '').toLowerCase();
        const titleB = (b.title || '').toLowerCase();
        return titleA.localeCompare(titleB);
    });
}

/**
 * Validate if string is a proper URL
 * @param {string} url - URL string to validate
 * @returns {boolean} True if valid URL
 */
function isValidUrl(url) {
    if (!url || typeof url !== 'string') return false;

    // Must start with http:// or https://
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        return false;
    }

    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// Helper function to check if a PDF URL is valid (not a DOI redirect)
function isValidPdfUrl(url) {
    if (!url) return false;

    // Must be a valid URL first
    if (!isValidUrl(url)) return false;

    // Filter out DOI URLs - they redirect to publisher pages, not direct PDFs
    if (url.includes('doi.org/') || url.startsWith('https://doi.apa.org/')) {
        return false;
    }
    return true;
}

/**
 * Determine access status from paper metadata
 * @param {Object} paper - Paper object with metadata
 * @returns {Object} Access status object with status, label, icon, and tooltip
 */
function getAccessStatus(paper) {
    const hasPdf = isValidPdfUrl(paper.pdf_url) || isValidPdfUrl(paper.open_access_pdf);
    const hasLink = paper.url || paper.doi;

    // Check for explicit open access flags (from various sources)
    const isOpenAccess = paper.is_open_access || paper.isOpenAccess || paper.open_access;

    // Semantic Scholar URLs often point to open access papers (via their aggregation)
    const isSemanticScholar = paper.url && paper.url.includes('semanticscholar.org');

    // arXiv papers are always open access
    const isArxiv = (paper.url && paper.url.includes('arxiv.org')) ||
                    (paper.source && paper.source.toLowerCase().includes('arxiv'));

    // Preprint servers are typically open access
    const isPreprint = paper.source && (
        paper.source.toLowerCase().includes('biorxiv') ||
        paper.source.toLowerCase().includes('medrxiv') ||
        paper.source.toLowerCase().includes('chemrxiv') ||
        paper.source.toLowerCase().includes('osf') ||
        paper.source.toLowerCase().includes('preprint')
    );

    // DOAJ (Directory of Open Access Journals) papers are open access by definition
    const isDoaj = paper.source && paper.source.toLowerCase().includes('doaj');

    if (hasPdf) {
        return {
            status: 'open-access',
            label: 'Open Access',
            icon: '🔓',
            tooltip: 'Free PDF available'
        };
    } else if (isOpenAccess || isArxiv || isPreprint || isDoaj) {
        // Explicit open access flag OR known open access sources
        return {
            status: 'open-access',
            label: 'Open Access',
            icon: '🔓',
            tooltip: 'Open access (check paper page for PDF)'
        };
    } else if (isSemanticScholar) {
        // Semantic Scholar aggregates from many sources - could be OA or paywalled
        return {
            status: 'check-access',
            label: 'Check Access',
            icon: '🔍',
            tooltip: 'May be open access - check paper page'
        };
    } else if (hasLink) {
        return {
            status: 'paywalled',
            label: 'Likely Paywalled',
            icon: '🔒',
            tooltip: 'May require subscription'
        };
    } else {
        return {
            status: 'unknown',
            label: 'Unknown',
            icon: '❓',
            tooltip: 'Access status unclear'
        };
    }
}

/**
 * Build access badge HTML
 * @param {Object} paper - Paper object with metadata
 * @returns {string} HTML string for access badge
 */
function buildAccessBadge(paper) {
    const access = getAccessStatus(paper);
    return `<span class="access-badge access-badge-${access.status}" title="${access.tooltip}">
        <span class="access-badge-icon">${access.icon}</span>
        <span>${access.label}</span>
    </span>`;
}

// ============================================================================
// DEDUPLICATION UTILITIES
// ============================================================================

/**
 * Normalize DOI for comparison
 * @param {string} doi - DOI string
 * @returns {string|null} Normalized DOI or null
 */
function normalizeDoi(doi) {
    if (!doi) return null;
    return doi.toLowerCase()
        .replace('https://doi.org/', '')
        .replace('http://doi.org/', '')
        .replace('doi:', '')
        .trim();
}

/**
 * Normalize title for fuzzy matching
 * @param {string} title - Paper title
 * @returns {string} Normalized title
 */
function normalizeTitle(title) {
    if (!title) return '';
    return title.toLowerCase()
        .replace(/[^\w\s]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

/**
 * Generate unique key for paper (DOI preferred, else title)
 * @param {Object} paper - Paper object
 * @returns {string} Unique key for deduplication
 */
function getPaperKey(paper) {
    const doi = normalizeDoi(paper.doi);
    if (doi) return `doi:${doi}`;

    const title = normalizeTitle(paper.title);
    if (title) return `title:${title}`;

    // Fallback to source + URL if available
    if (paper.url) return `url:${paper.url}`;

    return `id:${Math.random()}`; // last resort
}

/**
 * Apply citation-based relevance boost
 * Boost = 10% of highest citation count (capped at 10% max boost)
 * Example: 163 citations = 16% boost, capped at 10%
 * @param {Object} paper - Paper with _source_links
 * @returns {number} Boosted relevance score (0-1 scale)
 */
function applyCitationBoost(paper) {
    // Find highest citation count among all sources
    let maxCitations = 0;

    if (paper._source_links && paper._source_links.length > 0) {
        maxCitations = Math.max(...paper._source_links.map(link => parseInt(link.citation_count) || 0));
    } else {
        // Fallback to paper's own citation_count
        maxCitations = parseInt(paper.citation_count) || 0;
    }

    // Calculate boost: 10% of citation count as percentage points
    // Example: 163 citations = 16.3 → floor to 16% boost
    const boostPercentage = Math.floor(maxCitations * 0.1);

    // Cap boost at 10 percentage points
    const cappedBoost = Math.min(boostPercentage, 10);

    // Convert to 0-1 scale (divide by 100)
    const boostScore = cappedBoost / 100;

    // Get base relevance score (default to 0 if not set)
    const baseScore = paper.relevance_score !== undefined ? paper.relevance_score : 0;

    // Add boost, cap final score at 1.0
    return Math.min(1.0, baseScore + boostScore);
}

/**
 * Merge two paper objects (combine resources from multiple sources)
 * @param {Object} existing - Existing paper object
 * @param {Object} newPaper - New paper to merge
 * @returns {Object} Merged paper object
 */
function mergePapers(existing, newPaper) {
    // Start with existing as base
    const merged = { ...existing };

    // Merge sources
    const existingSources = existing._merged_sources || [existing.source];
    const newSources = newPaper._merged_sources || [newPaper.source];
    merged._merged_sources = [...new Set([...existingSources, ...newSources])];
    merged._merged_count = merged._merged_sources.length;

    // NEW: Track source-attributed links for hybrid display
    const sourceLinks = existing._source_links || [];

    // Add existing paper's links if not already tracked
    if (!existing._source_links) {
        const existingPdf = existing.pdf_url || existing.open_access_pdf;
        sourceLinks.push({
            source: existing.source,
            pdf_url: existingPdf && isValidPdfUrl(existingPdf) ? existingPdf : null,
            url: existing.url || null,
            has_pdf: isValidPdfUrl(existingPdf),
            is_open_access: existing.is_open_access || false,
            citation_count: parseInt(existing.citation_count) || 0
        });
    }

    // Add new paper's links
    const newPdf = newPaper.pdf_url || newPaper.open_access_pdf;
    sourceLinks.push({
        source: newPaper.source,
        pdf_url: newPdf && isValidPdfUrl(newPdf) ? newPdf : null,
        url: newPaper.url || null,
        has_pdf: isValidPdfUrl(newPdf),
        is_open_access: newPaper.is_open_access || false,
        citation_count: parseInt(newPaper.citation_count) || 0
    });

    merged._source_links = sourceLinks;

    // Keep backward compatibility arrays
    const pdfUrls = new Set();
    const urls = new Set();

    sourceLinks.forEach(link => {
        if (link.pdf_url && isValidPdfUrl(link.pdf_url)) pdfUrls.add(link.pdf_url);
        if (link.url) urls.add(link.url);
    });

    merged._all_pdf_urls = Array.from(pdfUrls);
    merged._all_urls = Array.from(urls);

    // Use longest/best metadata
    if (newPaper.abstract && (!merged.abstract || newPaper.abstract.length > merged.abstract.length)) {
        merged.abstract = newPaper.abstract;
    }
    if (newPaper.doi && !merged.doi) {
        merged.doi = newPaper.doi;
    }
    if (newPaper.title && (!merged.title || newPaper.title.length > merged.title.length)) {
        merged.title = newPaper.title;
    }

    // Prefer higher citation count
    const existingCitations = parseInt(existing.citation_count) || 0;
    const newCitations = parseInt(newPaper.citation_count) || 0;
    merged.citation_count = Math.max(existingCitations, newCitations);

    // Merge open access flags (true if any source says it's OA)
    merged.is_open_access = existing.is_open_access || newPaper.is_open_access || false;

    // Keep the primary PDF URL for backward compatibility
    if (!merged.pdf_url && newPaper.pdf_url) {
        merged.pdf_url = newPaper.pdf_url;
    }
    if (!merged.open_access_pdf && newPaper.open_access_pdf) {
        merged.open_access_pdf = newPaper.open_access_pdf;
    }

    // Apply citation-based relevance boost
    merged.relevance_score = applyCitationBoost(merged);

    return merged;
}

// ============================================================================
// HYBRID SOURCE LINK UTILITIES
// ============================================================================

/**
 * Sanitize filename for PDF downloads
 * @param {string} title - Paper title
 * @returns {string} Safe filename
 */
function sanitizeFilename(title) {
    if (!title) return 'paper.pdf';
    return title
        .replace(/[<>:"/\\|?*\x00-\x1F]/g, '')
        .replace(/\s+/g, '_')
        .substring(0, 100) + '.pdf';
}

/**
 * Deduplicate source links (same source, same URLs)
 * Strategy: Keep unique combinations of source+type (PDF or page)
 * Allows same source to have both PDF and page link
 * @param {Array} sourceLinks - Array of source link objects
 * @returns {Array} Deduplicated source links
 */
function deduplicateSourceLinks(sourceLinks) {
    const seen = new Map();

    sourceLinks.forEach(link => {
        if (link.has_pdf && link.pdf_url) {
            // PDF link - key by source:pdf
            const key = `${link.source}:pdf`;
            if (!seen.has(key)) {
                seen.set(key, link);
            }
        } else if (link.url) {
            // Page link - key by source:page
            const key = `${link.source}:page`;
            if (!seen.has(key)) {
                seen.set(key, link);
            }
        }
    });

    return Array.from(seen.values());
}

/**
 * Build hybrid source-attributed links (desktop: horizontal, mobile: stacked)
 * @param {Object} paper - Paper object with _source_links
 * @returns {string} HTML for hybrid source links
 */
function buildHybridSourceLinks(paper) {
    const sourceLinks = paper._source_links || [];

    if (sourceLinks.length === 0) {
        // Fallback to legacy behavior
        return buildLegacyLinks(paper);
    }

    const uniqueSourceLinks = deduplicateSourceLinks(sourceLinks);
    const filename = sanitizeFilename(paper.title);

    // Separate PDFs and pages, validate URLs
    const pdfs = uniqueSourceLinks.filter(link => link.has_pdf && isValidUrl(link.pdf_url));
    const pages = uniqueSourceLinks.filter(link => !link.has_pdf && link.url && isValidUrl(link.url));

    let html = '<div class="source-access-container">';

    // Primary action: Download PDF button (if available)
    if (pdfs.length > 0) {
        const primaryPdf = pdfs[0];
        const downloadId = `download_${Math.random().toString(36).substr(2, 9)}`;

        html += `<div class="primary-pdf-action">
            <a href="${primaryPdf.pdf_url}"
               download="${filename}"
               target="_blank"
               class="btn btn-primary btn-pdf-download"
               data-pdf-url="${primaryPdf.pdf_url}"
               id="${downloadId}"
               onclick="window.trackDownloadAttempt(this.dataset.pdfUrl, this.id); return true;">
               <span class="pdf-icon">📄</span> Download PDF (${primaryPdf.source})
            </a>`;

        // Progressive disclosure: Alternate PDFs (if more than 1)
        if (pdfs.length > 1) {
            html += `<details class="alternate-pdfs-dropdown">
                <summary>+${pdfs.length - 1} more PDF${pdfs.length > 2 ? 's' : ''}</summary>
                <ul class="alternate-pdf-list">`;

            pdfs.slice(1).forEach(link => {
                const altDownloadId = `download_${Math.random().toString(36).substr(2, 9)}`;
                html += `<li>
                    <a href="${link.pdf_url}"
                       download="${filename}"
                       target="_blank"
                       data-pdf-url="${link.pdf_url}"
                       id="${altDownloadId}"
                       onclick="window.trackDownloadAttempt(this.dataset.pdfUrl, this.id); return true;">
                       ${link.source}
                    </a>
                </li>`;
            });

            html += `</ul></details>`;
        }

        html += `</div>`; // Close primary-pdf-action
    }

    // Source chips - only show page links (PDFs handled by button + dropdown above)
    if (pages.length > 0) {
        // Sort by citation count descending (left to right = highest to lowest)
        const sortedPages = [...pages].sort((a, b) => {
            const countA = parseInt(a.citation_count) || 0;
            const countB = parseInt(b.citation_count) || 0;
            return countB - countA;
        });

        html += `<div class="all-sources-chips">
            <span class="sources-label">All sources:</span>`;

        sortedPages.forEach(link => {
            if (!link.url || !isValidUrl(link.url)) return;

            const citationCount = parseInt(link.citation_count) || 0;

            // Determine citation tier for styling
            let citationClass = '';
            if (citationCount >= 100) {
                citationClass = 'citation-tier-high';
            } else if (citationCount >= 50) {
                citationClass = 'citation-tier-medium';
            } else if (citationCount >= 10) {
                citationClass = 'citation-tier-low';
            } else if (citationCount > 0) {
                citationClass = 'citation-tier-minimal';
            }

            const citationText = citationCount > 0
                ? ` <span class="source-citations ${citationClass}">(${citationCount.toLocaleString()})</span>`
                : '';

            // Check if this is a DOI URL
            const isDoiUrl = link.url.includes('doi.org/');
            const chipClass = isDoiUrl ? 'source-chip-doi' : 'source-chip-page';

            html += `<a href="${link.url}"
                       target="_blank"
                       class="source-chip ${chipClass}"
                       title="${isDoiUrl ? 'DOI Resolver' : 'Publisher page'}">
                       ${link.source}${citationText}
                     </a>`;
        });

        html += `</div>`; // Close all-sources-chips
    }

    html += `</div>`; // Close source-access-container

    // DOI fallback if no PDFs or pages
    if (pdfs.length === 0 && pages.length === 0 && paper.doi) {
        html = `<a href="https://doi.org/${paper.doi}" target="_blank" class="btn btn-small">View via DOI</a>`;
    }

    // Google Scholar fallback if still nothing
    if (pdfs.length === 0 && pages.length === 0 && !paper.doi) {
        const searchQuery = encodeURIComponent(paper.title);
        html = `<a href="https://scholar.google.com/scholar?q=${searchQuery}" target="_blank" class="btn btn-small btn-secondary">Search Google Scholar</a>`;
    }

    return html;
}

/**
 * Fallback: Build legacy links (backward compatibility)
 * Uses hybrid design for consistency
 * @param {Object} paper - Paper object
 * @returns {string} HTML for legacy links
 */
function buildLegacyLinks(paper) {
    const filename = sanitizeFilename(paper.title);
    const pdfUrl = paper.pdf_url || paper.open_access_pdf;

    let html = '<div class="source-access-container">';

    // Primary PDF if available
    if (isValidPdfUrl(pdfUrl)) {
        html += `<div class="primary-pdf-action">
            <a href="${pdfUrl}" download="${filename}"
               class="btn btn-primary btn-pdf-download">
               <span class="pdf-icon">📄</span> Download PDF (${paper.source || 'Unknown'})
            </a>
        </div>`;
    }

    // Source chips for all available links
    // Only show page links here (PDF already shown in download button)
    const hasPageLink = paper.url || paper.doi;
    if (hasPageLink) {
        const citationCount = parseInt(paper.citation_count) || 0;

        // Determine citation tier for styling
        let citationClass = '';
        if (citationCount >= 100) {
            citationClass = 'citation-tier-high';
        } else if (citationCount >= 50) {
            citationClass = 'citation-tier-medium';
        } else if (citationCount >= 10) {
            citationClass = 'citation-tier-low';
        } else if (citationCount > 0) {
            citationClass = 'citation-tier-minimal';
        }

        const citationText = citationCount > 0
            ? ` <span class="source-citations ${citationClass}">(${citationCount.toLocaleString()})</span>`
            : '';

        html += `<div class="all-sources-chips">
            <span class="sources-label">All sources:</span>`;

        if (paper.url && isValidUrl(paper.url)) {
            // Check if the URL is actually a DOI URL
            const isDoiUrl = paper.url.includes('doi.org/');
            const chipClass = isDoiUrl ? 'source-chip-doi' : 'source-chip-page';

            html += `<a href="${paper.url}"
                       target="_blank"
                       class="source-chip ${chipClass}"
                       title="${isDoiUrl ? 'DOI Resolver' : 'Publisher page'}">
                       ${paper.source || 'Unknown'}${citationText}
                     </a>`;
        } else if (paper.doi) {
            html += `<a href="https://doi.org/${paper.doi}"
                       target="_blank"
                       class="source-chip source-chip-doi"
                       title="DOI Resolver">
                       ${paper.source || 'Unknown'}${citationText}
                     </a>`;
        }

        html += `</div>`;
    }

    // Google Scholar fallback only if no links at all
    if (!pdfUrl && !hasPageLink) {
        const searchQuery = encodeURIComponent(paper.title);
        html += `<div class="all-sources-chips">
            <a href="https://scholar.google.com/scholar?q=${searchQuery}"
               class="source-chip source-chip-page">
               Search Google Scholar <span class="source-icon source-icon-page">🔍</span>
            </a>
        </div>`;
    }

    html += '</div>';
    return html;
}

// ============================================================================
// RENDERING UTILITIES
// ============================================================================


/**
 * Strip HTML tags from text to ensure plain text display
 */
function stripHtmlTags(text) {
    if (!text) return '';
    // Create a temporary div to use browser's HTML parsing
    const temp = document.createElement('div');
    temp.innerHTML = text;
    return temp.textContent || temp.innerText || '';
}

/**
 * Format journal names - handles strings, arrays, and objects
 */
function formatJournal(journal) {
    if (!journal) return '';

    if (Array.isArray(journal)) {
        // If array of objects, extract the 'name' or 'title' property
        const journalNames = journal.map(j => {
            if (typeof j === 'object' && j !== null) {
                return j.name || j.title || String(j);
            }
            return String(j);
        }).filter(name => name && name !== '[object Object]');
        return journalNames.join(', ');
    }

    return String(journal);
}

/**
 * Format author names - handles strings, arrays, and author objects
 */
function formatAuthors(authors) {
    if (!authors) return 'Unknown';

    if (Array.isArray(authors)) {
        const authorNames = authors.map(author => {
            if (typeof author === 'object' && author !== null) {
                // Handle author objects with various properties
                if (author.firstname && author.lastname) {
                    return `${author.firstname} ${author.lastname}`;
                }
                if (author.lastname) {
                    return author.lastname;
                }
                if (author.name) {
                    return author.name;
                }
                // Fallback to string representation
                return String(author);
            }
            return String(author);
        }).filter(name => name && !name.includes('[object Object]'));

        return authorNames.length > 0 ? authorNames.join(', ') : 'Unknown';
    }

    return String(authors);
}

// Helper function to build paper card HTML with proper URL handling
function buildPaperCard(paper, index, showBadge = true) {
    // Helper function to truncate long text fields
    const truncateText = (text, maxLength) => {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength).trim() + '...';
    };

    // Limit authors display to first 5, add "et al." if more
    let authors;
    if (Array.isArray(paper.authors) && paper.authors.length > 5) {
        authors = formatAuthors(paper.authors.slice(0, 5)) + ' et al.';
    } else {
        authors = formatAuthors(paper.authors);
    }

    // Format and truncate journal names
    const journal = truncateText(formatJournal(paper.journal), 100);

    // Strip HTML tags and truncate abstracts
    const cleanAbstract = stripHtmlTags(paper.abstract);
    const abstract = truncateText(cleanAbstract, 500);

    // Build hybrid source-attributed links
    const accessLinks = buildHybridSourceLinks(paper);

    return `
        <div class="paper-card ${showBadge ? 'paper-card-streaming' : ''}">
            <div class="paper-header">
                <h3>${paper.title || 'Untitled'}</h3>
            </div>
            <div class="paper-meta">
                <span class="meta-item"><strong>Authors:</strong> ${authors}</span>
                <span class="meta-item"><strong>Year:</strong> ${formatDate(paper.year)}</span>
                ${journal ? `<span class="meta-item"><strong>Journal:</strong> ${journal}</span>` : ''}
            </div>
            ${abstract ? `<p class="paper-abstract">${abstract}</p>` : ''}
            <div class="paper-links">
                ${accessLinks}
            </div>
        </div>
    `;
}

function renderStreamingResults() {
    const resultsDiv = document.getElementById('results');

    if (streamingResults.length === 0) {
        resultsDiv.innerHTML = '<p class="no-results">Searching...</p>';
        return;
    }

    // Apply filters and sort
    let filteredResults = applyFilters(streamingResults);
    filteredResults = sortByRelevance([...filteredResults]); // Clone to avoid mutating

    // Build summary message
    const pdfInfo = pdfOnlyFilter ? ` with direct download` : '';
    const relevanceInfo = relevanceThreshold > 0 ? `, min ${relevanceThreshold}% relevance` : '';
    let html = `<div class="results-summary">
        <p>Found <strong>${filteredResults.length}</strong> papers${pdfInfo}${relevanceInfo} (${sourcesCompleted}/${totalSources || '?'} sources completed)</p>
    </div>`;

    filteredResults.forEach((paper, index) => {
        html += buildPaperCard(paper, index, true);
    });

    resultsDiv.innerHTML = html;
}

// ============================================================================
// SSE STREAMING SEARCH
// ============================================================================

// Handle SSE streaming search
function searchWithSSE(query, limit, pdfOnly = false, minRelevance = 45) {
    // Close existing connection if any
    if (currentEventSource) {
        currentEventSource.close();
    }

    // Reset streaming state
    streamingResults = [];
    papersByKey.clear(); // Clear deduplication map for new search
    sourcesCompleted = 0;
    totalSources = 0;
    pdfOnlyFilter = pdfOnly;
    relevanceThreshold = minRelevance;

    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<p class="loading-message">🔍 Initiating search...</p>';

    // Show results section
    document.querySelector('.results-section').classList.add('active');

    const filterText = pdfOnly ? ' (Direct Download only)' : '';
    showStatus(`Searching for "${query}"${filterText}...`, 'loading');

    // Build URL with optional server-side filters
    const url = `${API_BASE_URL}/api/v1/search/stream?query=${encodeURIComponent(query)}&limit=${limit}&pdf_only=${pdfOnly}&min_relevance=${minRelevance}`;
    const eventSource = new EventSource(url);
    currentEventSource = eventSource;

    // Search start
    eventSource.addEventListener('search_start', (e) => {
        const data = JSON.parse(e.data);
        console.log('Search started:', data);
        resultsDiv.innerHTML = '<p class="loading-message">🔍 Searching across academic databases...</p>';
    });

    // Source started
    eventSource.addEventListener('source_start', (e) => {
        const data = JSON.parse(e.data);
        console.log('Source started:', data.source);
        showStatus(`Searching ${data.source}...`, 'loading');
    });

    // Results received
    eventSource.addEventListener('results', (e) => {
        const data = JSON.parse(e.data);
        console.log(`Received ${data.papers.length} papers from ${data.source}`);

        // Deduplicate and merge as we receive results
        let newCount = 0;
        let mergedCount = 0;

        data.papers.forEach(paper => {
            const key = getPaperKey(paper);

            if (papersByKey.has(key)) {
                // Merge with existing paper
                const existing = papersByKey.get(key);
                const merged = mergePapers(existing, paper);
                papersByKey.set(key, merged);
                mergedCount++;
                console.log(`Merged duplicate: "${paper.title}" from ${paper.source} (now ${merged._merged_count} sources)`);
            } else {
                // New unique paper - apply citation boost
                paper.relevance_score = applyCitationBoost(paper);
                papersByKey.set(key, paper);
                newCount++;
            }
        });

        console.log(`Deduplication: ${newCount} new, ${mergedCount} merged`);

        // Update streamingResults from deduplicated map
        streamingResults = Array.from(papersByKey.values());

        // Re-render with deduplicated results (filters applied during render)
        renderStreamingResults();
    });

    // Source completed
    eventSource.addEventListener('source_complete', (e) => {
        const data = JSON.parse(e.data);
        console.log(`Source completed: ${data.source} (${data.count} papers)`);
        sourcesCompleted = data.completed;

        // Capture total sources if available
        if (data.total && totalSources === 0) {
            totalSources = data.total;
        }

        renderStreamingResults();
    });

    // Progress update
    eventSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data);
        console.log(`Progress: ${data.percentage.toFixed(1)}% (${data.completed}/${data.total})`);

        // Capture total sources from progress event
        if (data.total && totalSources === 0) {
            totalSources = data.total;
        }

        showStatus(`Progress: ${data.percentage.toFixed(0)}% - ${data.results_count} papers found`, 'loading');
    });

    // Search complete
    eventSource.addEventListener('complete', (e) => {
        const data = JSON.parse(e.data);
        console.log('Search complete:', data);

        eventSource.close();
        currentEventSource = null;

        // Apply filters and sort for final render
        let finalResults = applyFilters(streamingResults);
        finalResults = sortByRelevance([...finalResults]);

        // Final render
        const resultsDiv = document.getElementById('results');
        const pdfInfo = pdfOnlyFilter ? ` with direct download` : '';
        const relevanceInfo = relevanceThreshold > 0 ? `, min ${relevanceThreshold}% relevance` : '';

        let html = `<div class="results-summary results-summary-complete">
            <p>✅ Search complete! Found <strong>${finalResults.length}</strong> papers${pdfInfo}${relevanceInfo} from ${data.sources_searched} sources</p>
        </div>`;

        finalResults.forEach((paper, index) => {
            html += buildPaperCard(paper, index, false);
        });

        resultsDiv.innerHTML = html;
        showStatus(`✅ Found ${finalResults.length} papers from ${data.sources_searched} sources`, 'success');
    });

    // Error handling
    eventSource.addEventListener('error', (e) => {
        // Note: e.data only exists for server-sent 'error' events, not connection errors
        if (e.data) {
            try {
                const data = JSON.parse(e.data);
                const errorMsg = data.error || 'Unknown error';

                if (data.fatal) {
                    eventSource.close();
                    currentEventSource = null;
                    showStatus(`Error: ${errorMsg}`, 'error');
                } else {
                    // Non-fatal error, continue
                    console.warn(`Source error: ${data.source} - ${errorMsg}`);
                }
            } catch (err) {
                console.error('Failed to parse error event:', err);
            }
        }
    });

    eventSource.onerror = (err) => {
        console.error('EventSource error:', err);
        eventSource.close();
        currentEventSource = null;
        if (streamingResults.length === 0) {
            showStatus('Connection error. Make sure the HTTP server is running.', 'error');
        }
    };
}

// ============================================================================
// EVENT HANDLERS
// ============================================================================

// Handle search form submission
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const query = document.getElementById('searchQuery').value;
    const limit = 25; // Default: 25 results per source for comprehensive coverage
    const pdfOnly = document.getElementById('pdfOnly').checked;
    const minRelevance = parseInt(document.getElementById('relevanceThreshold').value);

    // Always use SSE streaming for better performance
    searchWithSSE(query, limit, pdfOnly, minRelevance);
});

// ============================================================================
// SYSTEM STATUS
// ============================================================================

// Check system status
async function checkStatus() {
    showStatus('Checking system status...', 'loading');

    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/status`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        const statusDiv = document.getElementById('systemStatus');

        // Show status section
        document.querySelector('.status-section').classList.add('active');

        // Count available sources
        const apiStatus = data.api_status || {};
        const availableSources = Object.values(apiStatus).filter(status => status === true).length;
        const totalSources = Object.keys(apiStatus).length;

        let html = `
            <div class="status-grid">
                <div class="status-item">
                    <strong>Available Sources:</strong> ${availableSources} / ${totalSources}
                </div>
            </div>
            <details>
                <summary>API Status Details</summary>
                <pre>${JSON.stringify(apiStatus, null, 2)}</pre>
            </details>
        `;

        statusDiv.innerHTML = html;
        showStatus('Status check complete', 'success');
    } catch (error) {
        console.error('Status check error:', error);
        showStatus(`Error: ${error.message}. Make sure the HTTP server is running.`, 'error');
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

// Initialize UI and set up live filter event listeners
document.addEventListener('DOMContentLoaded', () => {
    console.log('PaperezMCP Browser UI initialized');
    console.log('API Server:', API_BASE_URL);

    // Get filter UI elements
    const relevanceSlider = document.getElementById('relevanceThreshold');
    const relevanceValue = document.getElementById('relevanceValue');
    const pdfOnlyCheckbox = document.getElementById('pdfOnly');

    // Live update: Relevance slider changes
    relevanceSlider.addEventListener('input', (e) => {
        relevanceValue.textContent = e.target.value;
        relevanceThreshold = parseInt(e.target.value);

        // Re-render results with new threshold if we have results
        if (streamingResults.length > 0) {
            renderStreamingResults();
        }
    });

    // Live update: PDF-only checkbox changes
    pdfOnlyCheckbox.addEventListener('change', (e) => {
        pdfOnlyFilter = e.target.checked;

        // Re-render results with new filter if we have results
        if (streamingResults.length > 0) {
            renderStreamingResults();
        }
    });
});
