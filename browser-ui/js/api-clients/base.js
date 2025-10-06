// ============================================================================
// BASE.JS - Base API client for academic databases
// ============================================================================

/**
 * Base class for browser-side academic API clients
 * Provides common functionality for direct CORS-enabled API calls
 */
export class BaseAPIClient {
    constructor(name) {
        this.name = name;
        this.timeout = 10000; // 10 second timeout
    }

    /**
     * Make HTTP request with timeout
     * @param {string} url - URL to fetch
     * @param {Object} options - Fetch options
     * @returns {Promise<Response>} Response object
     */
    async fetchWithTimeout(url, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal,
                mode: 'cors'
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error(`${this.name} request timeout after ${this.timeout}ms`);
            }
            throw error;
        }
    }

    /**
     * Normalize paper object to standard format
     * @param {Object} rawPaper - Raw paper from API
     * @returns {Object} Normalized paper
     */
    normalizePaper(rawPaper) {
        // Override in subclasses
        return rawPaper;
    }

    /**
     * Search papers
     * @param {string} query - Search query
     * @param {number} limit - Max results
     * @returns {Promise<Array>} Array of normalized papers
     */
    async search(query, limit = 10) {
        throw new Error('search() must be implemented by subclass');
    }

    /**
     * Get display name for source
     * @returns {string} Display name
     */
    getDisplayName() {
        return this.name;
    }
}

export default BaseAPIClient;
