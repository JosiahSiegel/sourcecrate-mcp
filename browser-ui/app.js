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

// API Configuration
// For production deployment, set window.PAPEREZ_API_URL before loading this script:
// <script>window.PAPEREZ_API_URL = 'https://your-api.onrender.com';</script>
// Or create a config.js file with: window.PAPEREZ_API_URL = 'https://...';
const API_BASE_URL = window.PAPEREZ_API_URL || 'http://localhost:8000';

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
        // Format author names
        const authors = formatAuthors(paper.authors);

        // Strip HTML tags from abstract for consistent plain text display
        const cleanAbstract = stripHtmlTags(paper.abstract);

        // Format journal name
        const journal = formatJournal(paper.journal);

        html += `
            <div class="paper-card">
                <div class="paper-header">
                    <h3>${paper.title || 'Untitled'}</h3>
                </div>
                <div class="paper-meta">
                    <span class="meta-item"><strong>Authors:</strong> ${authors}</span>
                    <span class="meta-item"><strong>Year:</strong> ${formatDate(paper.year)}</span>
                    ${journal ? `<span class="meta-item"><strong>Journal:</strong> ${journal}</span>` : ''}
                    <span class="meta-item"><strong>Source:</strong> ${paper.source || 'Unknown'}</span>
                </div>
                ${cleanAbstract ? `<p class="paper-abstract">${cleanAbstract}</p>` : ''}
                <div class="paper-links">
                    ${paper.url ? `<a href="${paper.url}" target="_blank" class="btn btn-small">View Paper</a>` : ''}
                    ${paper.pdf_url ? `<a href="${paper.pdf_url}" target="_blank" class="btn btn-small btn-pdf">PDF</a>` : ''}
                    ${paper.doi ? `<a href="https://doi.org/${paper.doi}" target="_blank" class="btn btn-small">DOI</a>` : ''}
                </div>
            </div>
        `;
    });

    resultsDiv.innerHTML = html;
}

// ============================================================================
// STATE MANAGEMENT
// ============================================================================
let currentEventSource = null;
let streamingResults = [];
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

// Sort results by relevance score (descending)
function sortByRelevance(results) {
    return results.sort((a, b) => {
        const scoreA = a.relevance_score !== undefined ? a.relevance_score : 0;
        const scoreB = b.relevance_score !== undefined ? b.relevance_score : 0;
        return scoreB - scoreA; // Descending order
    });
}

// Helper function to check if a PDF URL is valid (not a DOI redirect)
function isValidPdfUrl(url) {
    if (!url) return false;
    // Filter out DOI URLs - they redirect to publisher pages, not direct PDFs
    if (url.includes('doi.org/') || url.startsWith('https://doi.apa.org/')) {
        return false;
    }
    return true;
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

    // Helper function to ensure URLs are absolute
    const makeAbsoluteUrl = (url, source) => {
        if (!url) return null;

        // Already absolute
        if (url.startsWith('http://') || url.startsWith('https://')) {
            return url;
        }

        // Source-specific URL construction
        const sourceLower = source?.toLowerCase();

        // ERIC uses ?id= query parameter format
        if (sourceLower === 'eric') {
            const ericId = url.startsWith('/') ? url.substring(1) : url;
            return `https://eric.ed.gov/?id=${ericId}`;
        }

        // Handle relative URLs based on source
        const sourceBaseUrls = {
            'pubmed': 'https://pubmed.ncbi.nlm.nih.gov',
            'pubmed_central': 'https://www.ncbi.nlm.nih.gov/pmc',
            'europe_pmc': 'https://europepmc.org/article/MED',
            'arxiv': 'https://arxiv.org',
            'crossref': 'https://doi.org',
            'openalex': 'https://openalex.org',
            'semantic_scholar': 'https://www.semanticscholar.org/paper',
            'openlibrary': 'https://openlibrary.org',
            'doaj': 'https://doaj.org/article',
            'core': 'https://core.ac.uk/display',
            'biorxiv': 'https://www.biorxiv.org/content',
            'medrxiv': 'https://www.medrxiv.org/content',
            'chemrxiv': 'https://chemrxiv.org/engage/chemrxiv/article-details',
            'ssrn': 'https://papers.ssrn.com/sol3/papers.cfm?abstract_id=',
            'clinicaltrials': 'https://clinicaltrials.gov/study',
        };

        const baseUrl = sourceBaseUrls[sourceLower];
        if (baseUrl) {
            // For SSRN, URL is just the ID
            if (sourceLower === 'ssrn') {
                const ssrnId = url.replace(/[^0-9]/g, '');
                return `${baseUrl}${ssrnId}`;
            }
            return `${baseUrl}${url.startsWith('/') ? url : '/' + url}`;
        }

        // If we don't know the source, return null to skip this URL
        console.warn(`Relative URL without known source: ${url} from ${source}`);
        return null;
    };

    // Build access links - always show at least one link
    let accessLinks = '';
    let pdfUrl = makeAbsoluteUrl(paper.pdf_url, paper.source) || makeAbsoluteUrl(paper.open_access_pdf, paper.source);

    // Filter out DOI URLs - they redirect to publisher pages (HTML), not direct PDFs
    if (!isValidPdfUrl(pdfUrl)) {
        pdfUrl = null; // Don't show as downloadable PDF
    }

    if (pdfUrl) {
        // Generate a safe filename from the paper title
        const sanitizeFilename = (title) => {
            if (!title) return 'paper.pdf';
            // Remove invalid filename characters and limit length
            return title
                .replace(/[<>:"/\\|?*\x00-\x1F]/g, '')
                .replace(/\s+/g, '_')
                .substring(0, 100) + '.pdf';
        };
        const filename = sanitizeFilename(paper.title);

        // Direct download (no proxy - scales to infinite users)
        // Browser handles download natively - works for most publishers
        const downloadId = `download_${Math.random().toString(36).substr(2, 9)}`;
        accessLinks += `<a href="${pdfUrl}"
                          download="${filename}"
                          target="_blank"
                          class="btn btn-small btn-pdf"
                          data-pdf-url="${pdfUrl}"
                          id="${downloadId}"
                          onclick="window.trackDownloadAttempt(this.dataset.pdfUrl, this.id); return true;">
                          Download PDF
                        </a>`;
    }

    const viewUrl = makeAbsoluteUrl(paper.url, paper.source);
    if (viewUrl) {
        accessLinks += `<a href="${viewUrl}" target="_blank" class="btn btn-small">View Online</a>`;
    } else if (paper.doi) {
        accessLinks += `<a href="https://doi.org/${paper.doi}" target="_blank" class="btn btn-small">View via DOI</a>`;
    }

    // If still no links, create a search link
    if (!accessLinks) {
        const searchQuery = encodeURIComponent(paper.title);
        accessLinks = `<a href="https://scholar.google.com/scholar?q=${searchQuery}" target="_blank" class="btn btn-small btn-secondary">Search Google Scholar</a>`;
    }

    return `
        <div class="paper-card ${showBadge ? 'paper-card-streaming' : ''}">
            <div class="paper-header">
                <h3>${paper.title || 'Untitled'}</h3>
            </div>
            <div class="paper-meta">
                <span class="meta-item"><strong>Authors:</strong> ${authors}</span>
                <span class="meta-item"><strong>Year:</strong> ${formatDate(paper.year)}</span>
                ${journal ? `<span class="meta-item"><strong>Journal:</strong> ${journal}</span>` : ''}
                <span class="meta-item"><strong>Source:</strong> ${paper.source || 'Unknown'}</span>
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

    const url = `${API_BASE_URL}/api/v1/search/stream?query=${encodeURIComponent(query)}&limit=${limit}`;
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

        // Add all papers (filtering happens in renderStreamingResults)
        streamingResults.push(...data.papers);

        // Re-render with new results (filters applied during render)
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
        let errorMsg = 'Unknown error';
        try {
            const data = JSON.parse(e.data);
            errorMsg = data.error;

            if (data.fatal) {
                eventSource.close();
                currentEventSource = null;
                showStatus(`Error: ${errorMsg}`, 'error');
            } else {
                // Non-fatal error, continue
                console.warn(`Source error: ${data.source} - ${errorMsg}`);
            }
        } catch (err) {
            // Connection error
            console.error('SSE connection error:', err);
            eventSource.close();
            currentEventSource = null;
            showStatus('Connection lost. Please try again.', 'error');
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
