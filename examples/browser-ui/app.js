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

// Handle search form submission
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const query = document.getElementById('searchQuery').value;
    const limit = parseInt(document.getElementById('limit').value);
    const streaming = document.getElementById('streaming').checked;

    const endpoint = streaming ? '/api/v1/search/streaming' : '/api/v1/search';

    showStatus(`Searching for "${query}"...`, 'loading');

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, limit }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (streaming && data.streaming_results) {
            // Handle streaming results
            renderResults({
                results: data.streaming_results || data.results,
                total_found: data.streaming_results?.length || data.total_found,
                sources_used: data.streaming_summary?.sources_completed || data.sources_used
            });
            showStatus(`Found ${data.streaming_results?.length || 0} papers (streaming)`, 'success');
        } else {
            // Handle regular results
            renderResults(data);
            showStatus(`Found ${data.total_found} papers`, 'success');
        }
    } catch (error) {
        console.error('Search error:', error);
        showStatus(`Error: ${error.message}. Make sure the HTTP server is running.`, 'error');
    }
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
