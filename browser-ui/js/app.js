// ============================================================================
// APP.JS - Main entry point and event handlers
// ============================================================================

import { API_BASE_URL, DownloadReliability } from './state.js';
import {
    streamingResults,
    pdfOnlyFilter,
    renderedPaperKeys,
    setPdfOnlyFilter
} from './state.js';
import { searchWithClient, searchByTitle as apiSearchByTitle } from './api.js';
import { renderStreamingResults } from './rendering.js';

// ============================================================================
// Global window functions (for onclick handlers in HTML)
// ============================================================================

/**
 * Track download attempt when user clicks download button
 * @param {string} pdfUrl - PDF URL
 * @param {string} downloadId - Download button ID
 */
window.trackDownloadAttempt = function(pdfUrl, downloadId) {
    // Optimistically record as success
    DownloadReliability.recordAttempt(pdfUrl, true);

    // Optional: HEAD request to check if URL is accessible
    setTimeout(() => {
        fetch(pdfUrl, { method: 'HEAD', mode: 'no-cors' })
            .then(() => {
                // console.log(`Download initiated: ${DownloadReliability.getDomain(pdfUrl)}`);
            })
            .catch(() => {
                DownloadReliability.recordAttempt(pdfUrl, false);
                // console.warn(`Download may have failed: ${DownloadReliability.getDomain(pdfUrl)}`);
            });
    }, 1000);
};

/**
 * Search by paper title (exposed globally for onclick)
 * @param {string} title - Paper title
 */
window.searchByTitle = function(title) {
    apiSearchByTitle(title, renderStreamingResults);
};


// ============================================================================
// Event Handlers
// ============================================================================

/**
 * Handle search form submission
 */
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const query = document.getElementById('searchQuery').value;
    const limit = 25; // Default: 25 results per source
    const pdfOnly = document.getElementById('pdfOnly').checked;
    const minRelevance = 35;

    // Execute search across multiple academic databases
    await searchWithClient(query, limit, pdfOnly, minRelevance, renderStreamingResults);
});

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // console.log('SourceCrate Browser UI initialized');

    // Get filter UI elements
    const pdfOnlyCheckbox = document.getElementById('pdfOnly');

    // Live update: PDF-only checkbox changes
    pdfOnlyCheckbox.addEventListener('change', (e) => {
        setPdfOnlyFilter(e.target.checked);

        // Re-render results with new filter if we have results
        if (streamingResults.length > 0) {
            // Reset rendering state to force full re-render with new filter
            renderedPaperKeys.clear();

            // Clear existing results container
            const resultsContainer = document.getElementById('results-container');
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
            }

            // Re-render all papers with new filter applied
            renderStreamingResults();
        }
    });
});
