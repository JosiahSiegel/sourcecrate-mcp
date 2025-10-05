// ============================================================================
// API.JS - API client and server-sent events (SSE) handling
// ============================================================================

import { API_BASE_URL, showStatus } from './state.js';
import {
    currentEventSource,
    streamingResults,
    papersByKey,
    sourcesCompleted,
    totalSources,
    pdfOnlyFilter,
    relevanceThreshold,
    currentQuery,
    renderedPaperKeys,
    setCurrentEventSource,
    setStreamingResults,
    setSourcesCompleted,
    setTotalSources,
    setPdfOnlyFilter,
    setRelevanceThreshold,
    setCurrentQuery
} from './state.js';
import { getPaperKey, mergePapers, calculateOptimalRelevance } from './utils.js';

/**
 * Handle SSE streaming search
 * @param {string} query - Search query
 * @param {number} limit - Max results per source
 * @param {boolean} pdfOnly - Filter for PDF availability
 * @param {number} minRelevance - Minimum relevance threshold
 * @param {Function} renderCallback - Callback to render results
 */
export function searchWithSSE(query, limit, pdfOnly = false, minRelevance = 35, renderCallback) {
    // Close existing connection if any
    if (currentEventSource) {
        currentEventSource.close();
    }

    // Reset streaming state
    setStreamingResults([]);
    papersByKey.clear(); // Clear deduplication map for new search
    renderedPaperKeys.clear(); // Clear rendered papers tracking for new search
    setSourcesCompleted(0);
    setTotalSources(0);
    setPdfOnlyFilter(pdfOnly);
    setRelevanceThreshold(minRelevance);
    setCurrentQuery(query); // Store query for title matching in relevance scoring

    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<p class="loading-message">🔍 Initiating search...</p>';

    // Show results section
    document.querySelector('.results-section').classList.add('active');

    const filterText = pdfOnly ? ' (Direct Download only)' : '';
    showStatus(`Searching for "${query}"${filterText}...`, 'loading');

    // Build URL with optional server-side filters
    const url = `${API_BASE_URL}/api/v1/search/stream?query=${encodeURIComponent(query)}&limit=${limit}&pdf_only=${pdfOnly}&min_relevance=${minRelevance}`;
    const eventSource = new EventSource(url);
    setCurrentEventSource(eventSource);

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
                // New unique paper - apply optimal relevance scoring
                paper.relevance_score = calculateOptimalRelevance(paper, currentQuery);
                papersByKey.set(key, paper);
                newCount++;
            }
        });

        console.log(`Deduplication: ${newCount} new, ${mergedCount} merged`);

        // Update streamingResults from deduplicated map
        setStreamingResults(Array.from(papersByKey.values()));

        // Re-render with deduplicated results (filters applied during render)
        renderCallback();
    });

    // Source completed
    eventSource.addEventListener('source_complete', (e) => {
        const data = JSON.parse(e.data);
        console.log(`Source completed: ${data.source} (${data.count} papers)`);
        setSourcesCompleted(data.completed);

        // Capture total sources if available
        if (data.total && totalSources === 0) {
            setTotalSources(data.total);
        }

        renderCallback();
    });

    // Progress update
    eventSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data);
        console.log(`Progress: ${data.percentage.toFixed(1)}% (${data.completed}/${data.total})`);

        // Capture total sources from progress event
        if (data.total && totalSources === 0) {
            setTotalSources(data.total);
        }

        showStatus(`Progress: ${data.percentage.toFixed(0)}% - ${data.results_count} papers found`, 'loading');
    });

    // Search complete
    eventSource.addEventListener('complete', (e) => {
        const data = JSON.parse(e.data);
        console.log('Search complete:', data);

        eventSource.close();
        setCurrentEventSource(null);

        // Update summary to show completion (no need to rebuild cards)
        const summaryDiv = document.getElementById('results-summary');
        if (summaryDiv) {
            const pdfInfo = pdfOnlyFilter ? ` with direct download` : '';
            summaryDiv.innerHTML = `<p>✅ Search complete! Found <strong>${streamingResults.length}</strong> papers${pdfInfo} from ${data.sources_searched} sources</p>`;
            summaryDiv.className = 'results-summary results-summary-complete';
        }

        showStatus(`✅ Found ${streamingResults.length} papers from ${data.sources_searched} sources`, 'success');
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
                    setCurrentEventSource(null);
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
        setCurrentEventSource(null);
        if (streamingResults.length === 0) {
            showStatus('Connection error. Make sure the HTTP server is running.', 'error');
        }
    };
}

/**
 * Check system status
 */
export async function checkStatus() {
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

/**
 * Search by paper title with one click
 * @param {string} title - Paper title to search for
 * @param {Function} renderCallback - Callback to render results
 */
export function searchByTitle(title, renderCallback) {
    if (!title) return;

    // Remove special characters, keep only letters, numbers, and spaces
    const cleanedTitle = title.replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim();

    // Update search input
    const searchInput = document.getElementById('searchQuery');
    searchInput.value = cleanedTitle;

    // Trigger search with current settings
    const limit = 25;
    const pdfOnly = document.getElementById('pdfOnly').checked;
    const minRelevance = 35;

    // Scroll to top to see results
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Execute search
    searchWithSSE(cleanedTitle, limit, pdfOnly, minRelevance, renderCallback);
}
