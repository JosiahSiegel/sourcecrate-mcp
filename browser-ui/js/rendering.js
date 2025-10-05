// ============================================================================
// RENDERING.JS - UI rendering functions for paper cards and source links
// ============================================================================

import {
    isValidUrl,
    isValidPdfUrl,
    isKnownBrokenUrl,
    getFullDoiUrl,
    normalizeDoi,
    sanitizeFilename,
    stripHtmlTags,
    truncateText,
    formatAuthors,
    formatJournal,
    deduplicateSourceLinks,
    getPaperKey,
    applyFilters,
    sortByRelevance
} from './utils.js';
import {
    streamingResults,
    sourcesCompleted,
    totalSources,
    pdfOnlyFilter,
    renderedPaperKeys,
    DownloadReliability
} from './state.js';

/**
 * Get best access URL for a source link
 * @param {Object} paper - Paper object
 * @param {Object} link - Source link object
 * @returns {Object|null} Access object or null
 */
function getBestAccessUrl(paper, link) {
    // Check if PDF URL exists and is valid
    if (link.has_pdf && link.pdf_url && isValidUrl(link.pdf_url)) {
        // Check for known broken patterns
        if (isKnownBrokenUrl(link.pdf_url)) {
            // URL is known to be broken - use DOI fallback if available
            if (paper.doi) {
                return {
                    type: 'doi',
                    url: getFullDoiUrl(paper.doi),
                    label: `${link.source} (via DOI)`,
                    source: link.source,
                    citation_count: link.citation_count || 0,
                    is_fallback: true
                };
            }
            // No DOI available, URL is broken, skip this link
            return null;
        }

        // URL appears valid
        return {
            type: 'pdf',
            url: link.pdf_url,
            label: `Download PDF (${link.source})`,
            source: link.source,
            citation_count: link.citation_count || 0,
            is_fallback: false
        };
    }

    // No PDF, check for page URL
    if (link.url && isValidUrl(link.url)) {
        return {
            type: 'page',
            url: link.url,
            label: link.source,
            source: link.source,
            citation_count: link.citation_count || 0,
            is_fallback: false
        };
    }

    return null;
}

/**
 * Build hybrid source-attributed links
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

    // Get best access URLs for all links
    const accessUrls = uniqueSourceLinks
        .map(link => getBestAccessUrl(paper, link))
        .filter(access => access !== null);

    // Separate PDFs, DOI fallbacks, and pages
    const pdfs = accessUrls.filter(access => access.type === 'pdf');
    const doiFallbacks = accessUrls.filter(access => access.type === 'doi' && access.is_fallback);
    const pages = accessUrls.filter(access => access.type === 'page');

    // Combine pages and DOI fallbacks for "All sources" section
    const allPages = [...pages, ...doiFallbacks];

    // Ensure DOI link is always included if paper has DOI
    if (paper.doi) {
        const fullDoiUrl = getFullDoiUrl(paper.doi);
        const normalizedDoi = normalizeDoi(paper.doi);

        // Only proceed if we have a valid DOI URL
        if (fullDoiUrl && isValidUrl(fullDoiUrl)) {
            // Check if any existing link is a DOI URL
            let doiLinkIndex = -1;
            for (let i = 0; i < allPages.length; i++) {
                const access = allPages[i];
                if (access.url && access.url.includes('doi.org/')) {
                    const existingNormalizedDoi = normalizeDoi(access.url);
                    if (existingNormalizedDoi === normalizedDoi) {
                        doiLinkIndex = i;
                        break;
                    }
                }
            }

            if (doiLinkIndex >= 0) {
                // Found existing DOI link - update it
                allPages[doiLinkIndex].url = fullDoiUrl;
                allPages[doiLinkIndex].label = 'DOI';
            } else {
                // No DOI link exists - add it
                allPages.push({
                    type: 'page',
                    url: fullDoiUrl,
                    label: 'DOI',
                    source: 'DOI',
                    citation_count: 0,
                    is_fallback: false
                });
            }
        }
    }

    // Deduplicate by URL
    const uniquePages = [];
    const seenUrls = new Set();
    const seenDois = new Set();

    allPages.forEach(access => {
        if (access.url && access.url.includes('doi.org/')) {
            const normalizedDoi = normalizeDoi(access.url);
            if (!seenDois.has(normalizedDoi)) {
                seenDois.add(normalizedDoi);
                seenUrls.add(access.url);
                uniquePages.push(access);
            }
        } else {
            if (!seenUrls.has(access.url)) {
                seenUrls.add(access.url);
                uniquePages.push(access);
            }
        }
    });

    let html = '<div class="source-access-container">';

    // Primary action: Download PDF button
    if (pdfs.length > 0) {
        const primaryPdf = pdfs[0];
        const downloadId = `download_${Math.random().toString(36).substr(2, 9)}`;

        html += `<div class="primary-pdf-action">
            <a href="${primaryPdf.url}"
               download="${filename}"
               target="_blank"
               rel="noopener noreferrer"
               class="btn btn-primary btn-pdf-download"
               data-pdf-url="${primaryPdf.url}"
               id="${downloadId}"
               onclick="window.trackDownloadAttempt(this.dataset.pdfUrl, this.id); return true;">
               <span class="pdf-icon">📄</span> ${primaryPdf.label}
            </a>`;

        // Progressive disclosure: Alternate PDFs
        if (pdfs.length > 1) {
            html += `<details class="alternate-pdfs-dropdown">
                <summary>+${pdfs.length - 1} more PDF${pdfs.length > 2 ? 's' : ''}</summary>
                <ul class="alternate-pdf-list">`;

            pdfs.slice(1).forEach(access => {
                const altDownloadId = `download_${Math.random().toString(36).substr(2, 9)}`;
                html += `<li>
                    <a href="${access.url}"
                       download="${filename}"
                       target="_blank"
                       rel="noopener noreferrer"
                       data-pdf-url="${access.url}"
                       id="${altDownloadId}"
                       onclick="window.trackDownloadAttempt(this.dataset.pdfUrl, this.id); return true;">
                       ${access.label}
                    </a>
                </li>`;
            });

            html += `</ul></details>`;
        }

        html += `</div>`;
    }

    // Source chips
    if (uniquePages.length > 0) {
        // Sort: DOI first, then by citation count
        const sortedPages = [...uniquePages].sort((a, b) => {
            const aIsDoi = a.url && a.url.includes('doi.org/');
            const bIsDoi = b.url && b.url.includes('doi.org/');

            if (aIsDoi && !bIsDoi) return -1;
            if (!aIsDoi && bIsDoi) return 1;

            const countA = parseInt(a.citation_count) || 0;
            const countB = parseInt(b.citation_count) || 0;
            return countB - countA;
        });

        html += `<div class="all-sources-chips">
            <span class="sources-label">Sources:</span>`;

        sortedPages.forEach(access => {
            if (!access.url || !isValidUrl(access.url)) return;

            const citationCount = parseInt(access.citation_count) || 0;

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

            const isDoiUrl = access.url.includes('doi.org/');
            const chipClass = isDoiUrl ? 'source-chip-doi' : 'source-chip-page';

            let displayLabel = access.label;
            if (isDoiUrl) {
                displayLabel = 'DOI';
            } else {
                const dbSources = ['crossref', 'semantic scholar', 'pubmed', 'arxiv', 'google scholar', 'europe pmc', 'doaj', 'core'];
                const labelLower = access.label.toLowerCase();
                if (dbSources.some(db => labelLower.includes(db))) {
                    displayLabel = 'Publisher';
                }
            }

            html += `<a href="${access.url}"
                       target="_blank"
                       class="source-chip ${chipClass}"
                       title="${isDoiUrl ? 'DOI Resolver' : 'Publisher page'}">
                       ${displayLabel}${citationText}
                     </a>`;
        });

        html += `</div>`;
    }

    // Google Scholar fallback
    if (pdfs.length === 0 && uniquePages.length === 0) {
        const searchQuery = encodeURIComponent(paper.title);
        html += `<div class="all-sources-chips">
            <a href="https://scholar.google.com/scholar?q=${searchQuery}"
               target="_blank"
               rel="noopener noreferrer"
               class="source-chip source-chip-page">
               Search on Google Scholar
            </a>
        </div>`;
    }

    html += '</div>';
    return html;
}

/**
 * Build legacy links (fallback for papers without _source_links)
 * @param {Object} paper - Paper object
 * @returns {string} HTML for legacy links
 */
function buildLegacyLinks(paper) {
    const filename = sanitizeFilename(paper.title);
    const pdfUrl = paper.pdf_url || paper.open_access_pdf;

    let html = '<div class="source-access-container">';

    // Primary PDF if available
    if (isValidPdfUrl(pdfUrl)) {
        if (isKnownBrokenUrl(pdfUrl) && paper.doi) {
            html += `<div class="primary-pdf-action">
                <a href="${getFullDoiUrl(paper.doi)}"
                   target="_blank"
                   rel="noopener noreferrer"
                   class="btn btn-secondary">
                   <span class="pdf-icon">🔗</span> View via DOI (${paper.source || 'Unknown'})
                </a>
            </div>`;
        } else if (!isKnownBrokenUrl(pdfUrl)) {
            html += `<div class="primary-pdf-action">
                <a href="${pdfUrl}" download="${filename}"
                   target="_blank"
                   rel="noopener noreferrer"
                   class="btn btn-primary btn-pdf-download">
                   <span class="pdf-icon">📄</span> Download PDF (${paper.source || 'Unknown'})
                </a>
            </div>`;
        }
    }

    // Source chips
    const hasPageLink = paper.url || paper.doi;
    if (hasPageLink) {
        const citationCount = parseInt(paper.citation_count) || 0;

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
            <span class="sources-label">Sources:</span>`;

        // Always add DOI first if available (normalized)
        if (paper.doi) {
            const fullDoiUrl = getFullDoiUrl(paper.doi);
            if (fullDoiUrl && isValidUrl(fullDoiUrl)) {
                html += `<a href="${fullDoiUrl}"
                           target="_blank"
                           class="source-chip source-chip-doi"
                           title="DOI Resolver">
                           DOI${citationText}
                         </a>`;
            }
        }

        // Then add paper.url if it exists and is NOT a DOI
        if (paper.url && isValidUrl(paper.url) && !paper.url.includes('doi.org/')) {
            let displayLabel = paper.source || 'Unknown';
            const dbSources = ['crossref', 'semantic scholar', 'pubmed', 'arxiv', 'google scholar', 'europe pmc', 'doaj', 'core'];
            const labelLower = displayLabel.toLowerCase();
            if (dbSources.some(db => labelLower.includes(db))) {
                displayLabel = 'Publisher';
            }

            html += `<a href="${paper.url}"
                       target="_blank"
                       class="source-chip source-chip-page"
                       title="Publisher page">
                       ${displayLabel}${citationText}
                     </a>`;
        }

        html += `</div>`;
    }

    // Google Scholar fallback
    if (!pdfUrl && !hasPageLink) {
        const searchQuery = encodeURIComponent(paper.title);
        html += `<div class="all-sources-chips">
            <a href="https://scholar.google.com/scholar?q=${searchQuery}"
               target="_blank"
               rel="noopener noreferrer"
               class="source-chip source-chip-page">
               Search on Google Scholar
            </a>
        </div>`;
    }

    html += '</div>';
    return html;
}

/**
 * Build a paper card HTML
 * @param {Object} paper - Paper object
 * @param {number} index - Card index
 * @param {boolean} showBadge - Show streaming badge
 * @returns {string} HTML for paper card
 */
export function buildPaperCard(paper, index, showBadge = true) {
    // Limit authors display to first 5
    let authors;
    if (Array.isArray(paper.authors) && paper.authors.length > 5) {
        authors = formatAuthors(paper.authors.slice(0, 5)) + ' et al.';
    } else {
        authors = formatAuthors(paper.authors);
    }

    const journal = truncateText(formatJournal(paper.journal), 100);
    const cleanAbstract = stripHtmlTags(paper.abstract);
    const abstract = truncateText(cleanAbstract, 500);
    const accessLinks = buildHybridSourceLinks(paper);
    const escapedTitle = (paper.title || 'Untitled').replace(/'/g, "\\'").replace(/"/g, '&quot;');

    // Build research metadata badges
    let metadataBadges = '';

    // DOI Badge with copy icon
    if (paper.doi) {
        const fullDoiUrl = getFullDoiUrl(paper.doi);
        metadataBadges += `<span class="metadata-badge badge-doi" title="DOI: ${fullDoiUrl} (click to copy)"
                                 onclick="navigator.clipboard.writeText('${fullDoiUrl}')"
                                 style="cursor: pointer;">
                             <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.25rem;">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                             </svg>
                             ${fullDoiUrl}
                           </span>`;
    }

    // Open Access Badge
    const isOpenAccess = paper.is_open_access || paper.isOpenAccess || paper.open_access;
    if (isOpenAccess) {
        metadataBadges += `<span class="metadata-badge badge-open-access" title="Open Access - Free to read and reuse">
                             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.25rem;">
                                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                                <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
                             </svg>
                             Open Access
                           </span>`;
    }

    // Preprint Badge
    const preprintSources = ['arxiv', 'biorxiv', 'medrxiv', 'socarxiv', 'osf preprints', 'preprint'];
    const isPreprint = paper.source && preprintSources.some(ps => paper.source.toLowerCase().includes(ps));
    if (isPreprint) {
        metadataBadges += `<span class="metadata-badge badge-preprint" title="Preprint - Not peer-reviewed">
                             <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 0.25rem;">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                <line x1="12" y1="9" x2="12" y2="13"></line>
                                <line x1="12" y1="17" x2="12.01" y2="17"></line>
                             </svg>
                             Preprint
                           </span>`;
    }

    // Citation Count Badge (simplified)
    const citationCount = parseInt(paper.citation_count) || 0;
    if (citationCount > 0) {
        const citationLabel = citationCount >= 1000 ? `${(citationCount/1000).toFixed(1)}k` : citationCount.toLocaleString();
        metadataBadges += `<span class="metadata-badge badge-citations" title="${citationCount.toLocaleString()} citation${citationCount !== 1 ? 's' : ''}">
                             ${citationLabel}
                           </span>`;
    }

    return `
        <div class="paper-card ${showBadge ? 'paper-card-streaming' : ''}">
            <div class="paper-header">
                <h3>
                    ${paper.title || 'Untitled'}
                    <span class="title-search-icon"
                          onclick="searchByTitle('${escapedTitle}')"
                          title="Search for this paper"
                          role="button"
                          tabindex="0"
                          onkeypress="if(event.key==='Enter'||event.key===' ')searchByTitle('${escapedTitle}')"
                          aria-label="Search for this paper">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="11" cy="11" r="8"></circle>
                            <path d="m21 21-4.35-4.35"></path>
                        </svg>
                    </span>
                </h3>
            </div>
            ${metadataBadges ? `<div class="research-metadata-badges">${metadataBadges}</div>` : ''}
            <div class="paper-meta">
                <span class="paper-authors">${authors}</span>
                ${paper.year ? `<span class="paper-year">${paper.year}</span>` : ''}
                ${journal ? `<span class="paper-journal">${journal}</span>` : ''}
            </div>
            ${abstract ? `<p class="paper-abstract">${abstract}</p>` : ''}
            ${accessLinks}
        </div>
    `;
}

/**
 * Update results summary
 * @param {number} count - Number of results
 */
export function updateResultsSummary(count) {
    const pdfInfo = pdfOnlyFilter ? ` with direct download` : '';
    const summaryHtml = `<p>Found <strong>${count}</strong> papers${pdfInfo} (${sourcesCompleted}/${totalSources || '?'} sources completed)</p>`;

    let summaryDiv = document.getElementById('results-summary');

    if (!summaryDiv) {
        summaryDiv = document.createElement('div');
        summaryDiv.id = 'results-summary';
        summaryDiv.className = 'results-summary';

        const resultsDiv = document.getElementById('results');
        resultsDiv.insertBefore(summaryDiv, resultsDiv.firstChild);
    }

    summaryDiv.innerHTML = summaryHtml;
}

/**
 * Render streaming results incrementally
 */
export function renderStreamingResults() {
    const resultsDiv = document.getElementById('results');

    if (streamingResults.length === 0) {
        resultsDiv.innerHTML = '<p class="no-results">Searching...</p>';
        return;
    }

    // Apply filters and sort
    let filteredResults = applyFilters(streamingResults, pdfOnlyFilter, 35);
    filteredResults = sortByRelevance([...filteredResults]);

    // Update summary
    updateResultsSummary(filteredResults.length);

    // Get existing results container or create it
    let resultsContainer = document.getElementById('results-container');
    if (!resultsContainer) {
        resultsDiv.innerHTML = '';

        resultsContainer = document.createElement('div');
        resultsContainer.id = 'results-container';
        resultsDiv.appendChild(resultsContainer);
    }

    // Identify new papers
    const newPapers = filteredResults.filter(paper => {
        const key = getPaperKey(paper);
        return !renderedPaperKeys.has(key);
    });

    if (newPapers.length === 0) return;

    // Create DocumentFragment for batch DOM insertion
    const fragment = document.createDocumentFragment();

    newPapers.forEach((paper, index) => {
        const key = getPaperKey(paper);

        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = buildPaperCard(paper, renderedPaperKeys.size + index, true);

        const cardElement = tempDiv.firstElementChild;
        if (cardElement) {
            cardElement.dataset.paperKey = key;
            fragment.appendChild(cardElement);

            renderedPaperKeys.add(key);
        }
    });

    resultsContainer.appendChild(fragment);
}
