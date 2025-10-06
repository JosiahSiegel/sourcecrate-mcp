// ============================================================================
// ORCHESTRATOR.JS - Client-side search orchestrator
// ============================================================================
// Coordinates parallel searches across multiple CORS-enabled academic APIs
// This replaces server-side search for supported sources (Phase 2 optimization)

import ArxivClient from './arxiv.js';
import CrossRefClient from './crossref.js';
import PubMedClient from './pubmed.js';
import OpenAlexClient from './openalex.js';

/**
 * Client-side search orchestrator for CORS-enabled sources
 * Runs searches in parallel directly from the browser
 */
export class ClientSearchOrchestrator {
    constructor() {
        // Initialize all CORS-enabled clients
        this.clients = {
            arxiv: new ArxivClient(),
            crossref: new CrossRefClient(),
            pubmed: new PubMedClient(),
            openalex: new OpenAlexClient()
        };

        this.defaultSources = ['arxiv', 'crossref', 'pubmed', 'openalex'];
    }

    /**
     * Search across multiple sources in parallel
     * @param {string} query - Search query
     * @param {Object} options - Search options
     * @returns {Promise<Object>} Search results with metadata
     */
    async search(query, options = {}) {
        const {
            limit = 10,
            sources = this.defaultSources,
            onSourceStart = null,
            onSourceComplete = null,
            onProgress = null
        } = options;

        console.log(`[ClientSearch] Starting parallel search across ${sources.length} sources`);

        const startTime = performance.now();
        const results = {
            papers: [],
            sources_searched: 0,
            sources_successful: 0,
            total_results: 0,
            elapsed_ms: 0
        };

        // Create search promises for all sources
        const searchPromises = sources.map(async (sourceName) => {
            if (!this.clients[sourceName]) {
                console.warn(`[ClientSearch] Unknown source: ${sourceName}`);
                return { source: sourceName, papers: [], error: 'Unknown source' };
            }

            const client = this.clients[sourceName];

            try {
                // Notify source started
                if (onSourceStart) {
                    onSourceStart({ source: sourceName });
                }

                const papers = await client.search(query, limit);

                // Notify source completed
                if (onSourceComplete) {
                    onSourceComplete({
                        source: sourceName,
                        count: papers.length,
                        success: true
                    });
                }

                return { source: sourceName, papers, error: null };
            } catch (error) {
                console.error(`[ClientSearch] ${sourceName} failed:`, error);

                // Notify source completed (with error)
                if (onSourceComplete) {
                    onSourceComplete({
                        source: sourceName,
                        count: 0,
                        success: false,
                        error: error.message
                    });
                }

                return { source: sourceName, papers: [], error: error.message };
            }
        });

        // Wait for all searches to complete
        const sourceResults = await Promise.all(searchPromises);

        // Aggregate results
        sourceResults.forEach(result => {
            results.sources_searched++;
            if (result.papers.length > 0) {
                results.sources_successful++;
                results.papers.push(...result.papers);
                results.total_results += result.papers.length;
            }
        });

        results.elapsed_ms = performance.now() - startTime;

        console.log(`[ClientSearch] Completed in ${results.elapsed_ms.toFixed(0)}ms: ${results.total_results} papers from ${results.sources_successful}/${results.sources_searched} sources`);

        return results;
    }

    /**
     * Search with streaming-like callback support
     * Calls onResults callback as each source completes
     * @param {string} query - Search query
     * @param {Object} options - Search options
     * @returns {Promise<Object>} Final aggregated results
     */
    async searchWithCallbacks(query, options = {}) {
        const {
            limit = 10,
            sources = this.defaultSources,
            onSourceStart = null,
            onResults = null,
            onSourceComplete = null,
            onComplete = null
        } = options;

        console.log(`[ClientSearch] Starting streaming search across ${sources.length} sources`);

        const startTime = performance.now();
        let sourcesCompleted = 0;
        let sourcesSuccessful = 0;
        let totalResults = 0;

        // Search each source and call callbacks as they complete
        const searchPromises = sources.map(async (sourceName) => {
            if (!this.clients[sourceName]) {
                console.warn(`[ClientSearch] Unknown source: ${sourceName}`);
                return;
            }

            const client = this.clients[sourceName];

            try {
                // Notify source started
                if (onSourceStart) {
                    onSourceStart({ source: sourceName });
                }

                const papers = await client.search(query, limit);

                // Notify results received (streaming-like)
                if (onResults && papers.length > 0) {
                    onResults({
                        source: sourceName,
                        papers,
                        count: papers.length
                    });
                }

                sourcesCompleted++;
                if (papers.length > 0) {
                    sourcesSuccessful++;
                    totalResults += papers.length;
                }

                // Notify source completed
                if (onSourceComplete) {
                    onSourceComplete({
                        source: sourceName,
                        count: papers.length,
                        completed: sourcesCompleted,
                        total: sources.length
                    });
                }
            } catch (error) {
                console.error(`[ClientSearch] ${sourceName} failed:`, error);
                sourcesCompleted++;

                // Notify source completed (with error)
                if (onSourceComplete) {
                    onSourceComplete({
                        source: sourceName,
                        count: 0,
                        completed: sourcesCompleted,
                        total: sources.length,
                        error: error.message
                    });
                }
            }
        });

        // Wait for all searches to complete
        await Promise.all(searchPromises);

        const elapsedMs = performance.now() - startTime;

        // Notify search complete
        if (onComplete) {
            onComplete({
                sources_searched: sources.length,
                sources_successful: sourcesSuccessful,
                total_results: totalResults,
                elapsed_ms: elapsedMs
            });
        }

        console.log(`[ClientSearch] Completed in ${elapsedMs.toFixed(0)}ms: ${totalResults} papers from ${sourcesSuccessful}/${sources.length} sources`);

        return {
            sources_searched: sources.length,
            sources_successful: sourcesSuccessful,
            total_results: totalResults,
            elapsed_ms: elapsedMs
        };
    }
}

export default ClientSearchOrchestrator;
