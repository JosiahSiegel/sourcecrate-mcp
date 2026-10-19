// Test-only provider responses. This file is excluded from the distribution.
export const query = 'game programming patterns Robert Nystrom';
export const response = { message: { items: [
    { title: ['Numerical methods'], DOI: '10.1234/unrelated', author: [{ given: 'Robert', family: 'Nystrom' }] },
    { title: ['Game Programming Patterns'], DOI: '10.1234/wrong-author', author: [{ given: 'Another', family: 'Writer' }] },
    { title: ['Game Programming Patterns'], DOI: '10.1234/exact', URL: 'https://example.org/book', author: [{ given: 'Robert', family: 'Nystrom' }] }
] } };
export function mockSources() {
    globalThis.fetch = async url => {
        if (String(url).includes('api.crossref.org')) return Response.json(response);
        if (String(url).includes('export.arxiv.org')) return new Response('<feed/>', { headers: { 'content-type': 'application/xml' } });
        if (String(url).includes('eutils.ncbi.nlm.nih.gov')) return Response.json({ esearchresult: { idlist: [] } });
        return Response.json({});
    };
}
if (process.env.SOURCECRATE_TEST_FIXTURES === '1' && process.argv[1]?.endsWith('server.js')) mockSources();
