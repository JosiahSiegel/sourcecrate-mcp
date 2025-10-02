// PaperezMCP Browser UI - JavaScript Client
// Communicates with PaperezMCP HTTP server

const API_BASE_URL = 'http://localhost:8000';

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
        const authors = Array.isArray(paper.authors)
            ? paper.authors.join(', ')
            : paper.authors || 'Unknown';

        html += `
            <div class="paper-card">
                <div class="paper-header">
                    <span class="paper-number">${index + 1}</span>
                    <h3>${paper.title || 'Untitled'}</h3>
                </div>
                <div class="paper-meta">
                    <span class="meta-item"><strong>Authors:</strong> ${authors}</span>
                    <span class="meta-item"><strong>Year:</strong> ${formatDate(paper.year)}</span>
                    ${paper.journal ? `<span class="meta-item"><strong>Journal:</strong> ${paper.journal}</span>` : ''}
                    <span class="meta-item"><strong>Source:</strong> ${paper.source || 'Unknown'}</span>
                </div>
                ${paper.abstract ? `<p class="paper-abstract">${paper.abstract}</p>` : ''}
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

// Render progressive streaming results
let currentEventSource = null;
let streamingResults = [];
let sourcesCompleted = 0;
let totalSources = 0;

// Helper function to build paper card HTML with proper URL handling
function buildPaperCard(paper, index, showBadge = true) {
    const authors = Array.isArray(paper.authors)
        ? paper.authors.join(', ')
        : paper.authors || 'Unknown';

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
    const pdfUrl = makeAbsoluteUrl(paper.pdf_url, paper.source) || makeAbsoluteUrl(paper.open_access_pdf, paper.source);
    if (pdfUrl) {
        accessLinks += `<a href="${pdfUrl}" target="_blank" class="btn btn-small btn-pdf">Download PDF</a>`;
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

    // Determine if paper has direct download (for badge)
    const hasDirectDownload = paper.pdf_url || paper.open_access_pdf;
    const downloadBadge = showBadge
        ? (hasDirectDownload
            ? '<span class="download-badge">📥 Direct Download</span>'
            : '<span class="download-badge no-download">🔗 Link Only</span>')
        : '';

    // Add relevance score badge
    let relevanceBadge = '';
    if (paper.relevance_score !== undefined && paper.relevance_score !== null) {
        const percentage = Math.round(paper.relevance_score * 100);
        let badgeClass = 'low';
        if (percentage >= 80) {
            badgeClass = 'high';
        } else if (percentage >= 50) {
            badgeClass = 'medium';
        }
        relevanceBadge = `<span class="relevance-badge ${badgeClass}">🎯 ${percentage}% Match</span>`;
    }

    return `
        <div class="paper-card ${showBadge ? 'paper-card-streaming' : ''}">
            <div class="paper-header">
                <span class="paper-number">${index + 1}</span>
                <div class="paper-title-row">
                    <h3>${paper.title || 'Untitled'}</h3>
                    ${relevanceBadge}
                    ${downloadBadge}
                </div>
            </div>
            <div class="paper-meta">
                <span class="meta-item"><strong>Authors:</strong> ${authors}</span>
                <span class="meta-item"><strong>Year:</strong> ${formatDate(paper.year)}</span>
                ${paper.journal ? `<span class="meta-item"><strong>Journal:</strong> ${paper.journal}</span>` : ''}
                <span class="meta-item"><strong>Source:</strong> ${paper.source || 'Unknown'}</span>
            </div>
            ${paper.abstract ? `<p class="paper-abstract">${paper.abstract}</p>` : ''}
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

    // Sort by relevance score (descending) before rendering
    streamingResults.sort((a, b) => {
        const scoreA = a.relevance_score !== undefined ? a.relevance_score : 0;
        const scoreB = b.relevance_score !== undefined ? b.relevance_score : 0;
        return scoreB - scoreA; // Descending order
    });

    let html = '';
    html += `<div class="results-summary">
        <p>Found <strong>${streamingResults.length}</strong> papers so far... (${sourcesCompleted}/${totalSources || '?'} sources completed)</p>
    </div>`;

    streamingResults.forEach((paper, index) => {
        html += buildPaperCard(paper, index, true);
    });

    resultsDiv.innerHTML = html;
}

// Global filter state
let pdfOnlyFilter = false;

// Handle SSE streaming search
function searchWithSSE(query, limit, pdfOnly = false) {
    // Close existing connection if any
    if (currentEventSource) {
        currentEventSource.close();
    }

    // Reset streaming state
    streamingResults = [];
    sourcesCompleted = 0;
    totalSources = 0;
    pdfOnlyFilter = pdfOnly;

    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<p class="loading-message">🔍 Initiating search...</p>';

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

        // Filter papers if PDF-only mode is enabled
        const papersToAdd = pdfOnlyFilter
            ? data.papers.filter(paper => paper.pdf_url || paper.open_access_pdf)
            : data.papers;

        // Add new papers
        streamingResults.push(...papersToAdd);

        // Re-render with new results
        renderStreamingResults();

        const filterInfo = pdfOnlyFilter ? ` with direct download` : '';
        showStatus(`Found ${streamingResults.length} papers${filterInfo} so far (from ${data.source})...`, 'loading');
    });

    // Source completed
    eventSource.addEventListener('source_complete', (e) => {
        const data = JSON.parse(e.data);
        console.log(`Source completed: ${data.source} (${data.count} papers)`);
        sourcesCompleted = data.completed;
        renderStreamingResults();
    });

    // Progress update
    eventSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data);
        console.log(`Progress: ${data.percentage.toFixed(1)}% (${data.completed}/${data.total})`);
        showStatus(`Progress: ${data.percentage.toFixed(0)}% - ${data.results_count} papers found`, 'loading');
    });

    // Search complete
    eventSource.addEventListener('complete', (e) => {
        const data = JSON.parse(e.data);
        console.log('Search complete:', data);

        eventSource.close();
        currentEventSource = null;

        // Sort by relevance score (descending) before final render
        streamingResults.sort((a, b) => {
            const scoreA = a.relevance_score !== undefined ? a.relevance_score : 0;
            const scoreB = b.relevance_score !== undefined ? b.relevance_score : 0;
            return scoreB - scoreA; // Descending order
        });

        // Final render
        const resultsDiv = document.getElementById('results');
        let html = `<div class="results-summary results-summary-complete">
            <p>✅ Search complete! Found <strong>${data.total_results}</strong> papers from ${data.sources_searched} sources</p>
        </div>`;

        streamingResults.forEach((paper, index) => {
            html += buildPaperCard(paper, index, false);
        });

        resultsDiv.innerHTML = html;
        showStatus(`✅ Found ${data.total_results} papers from ${data.sources_searched} sources`, 'success');
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

// Handle search form submission
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const query = document.getElementById('searchQuery').value;
    const limit = parseInt(document.getElementById('limit').value);
    const pdfOnly = document.getElementById('pdfOnly').checked;

    // Always use SSE streaming for better performance
    searchWithSSE(query, limit, pdfOnly);
});

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

        // Count available sources
        const apiStatus = data.api_status || {};
        const availableSources = Object.values(apiStatus).filter(status => status === true).length;
        const totalSources = Object.keys(apiStatus).length;

        let html = `
            <div class="status-grid">
                <div class="status-item">
                    <strong>Available Sources:</strong> ${availableSources} / ${totalSources}
                </div>
                ${data.cache_stats ? `
                    <div class="status-item">
                        <strong>Cache Size:</strong> ${data.cache_stats.size || 'N/A'}
                    </div>
                ` : ''}
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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('PaperezMCP Browser UI initialized');
    console.log('API Server:', API_BASE_URL);
});
