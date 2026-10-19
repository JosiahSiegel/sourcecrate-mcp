// Test-only provider responses. This file is excluded from the distribution.
export const query = 'game programming patterns Robert Nystrom';
export const response = { message: { items: [
    { title: ['Numerical methods'], DOI: '10.1234/unrelated', author: [{ given: 'Robert', family: 'Nystrom' }] },
    { title: ['Game Programming Patterns'], DOI: '10.1234/wrong-author', author: [{ given: 'Another', family: 'Writer' }] },
    { title: ['Game Programming Patterns'], DOI: '10.1234/exact', URL: 'https://example.org/book', author: [{ given: 'Robert', family: 'Nystrom' }] }
] } };
export function mockSources() {
    const recovery = providerRecoveryFetch();
    globalThis.fetch = async url => {
        if (String(url).includes('provider+recovery+climate')) return recovery(url);
        if (String(url).includes('api.crossref.org')) return Response.json(response);
        if (String(url).includes('export.arxiv.org')) return new Response('<feed/>', { headers: { 'content-type': 'application/xml' } });
        if (String(url).includes('eutils.ncbi.nlm.nih.gov')) return Response.json({ esearchresult: { idlist: [] } });
        return Response.json({});
    };
}

// Exercises real shared provider clients through the packaged stdio server.
export function providerRecoveryFetch() {
    let attempts = 0;
    return async input => {
        const url = new URL(input);
        if (url.hostname === 'zenodo.org') return new Response('', { status: 403 });
        const fallback = url.searchParams.get('client-id') === 'cern.zenodo';
        if (!fallback && ++attempts === 1) return new Response('', { status: 503 });
        return Response.json({ data: [{ attributes: {
            doi: fallback ? '10.5281/zenodo.123' : '10.1234/climate',
            titles: [{ title: fallback ? 'Zenodo climate observations' : 'DataCite climate research' }],
            creators: [{ name: 'Researcher, A' }],
            url: fallback ? 'https://zenodo.org/records/123' : 'https://example.org/climate'
        } }] });
    };
}
if (process.env.SOURCECRATE_TEST_FIXTURES === '1' && process.argv[1]?.endsWith('server.js')) mockSources();
