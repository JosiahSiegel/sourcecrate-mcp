import { test } from 'node:test';
import assert from 'node:assert/strict';
import { browse } from '../adapter.js';
import { searchPapers } from 'sourcecrate/search';
import { getAccessLinks } from 'sourcecrate/access-links';
import { mockSources, query } from './mock-sources.mjs';

test('MCP uses the exact site ranking, scores and link destinations for title + author', async () => {
    mockSources();
    const website = await searchPapers(query);
    const mcp = await browse({ query });
    assert.equal(mcp.papers[0].doi, '10.1234/exact');
    assert.equal(mcp.papers.length, 3);
    for (let i = 0; i < mcp.papers.length; i++) {
        const { primary_url, access_links, ...paper } = mcp.papers[i];
        assert.deepEqual(paper, website.papers[i]);
        const links = getAccessLinks(paper);
        assert.equal(primary_url, links.firstUrl);
        assert.deepEqual(access_links, [...links.pdfs, ...links.pages]);
    }
});

test('provider errors remain visible rather than looking like complete empty results', async () => {
    globalThis.fetch = async () => new Response('', { status: 429 });
    const result = await browse({ query, sources: ['crossref'] });
    assert.equal(result.partial, true);
    assert.equal(result.source_status[0].error, 'HTTP 429');
    assert.deepEqual(result.papers, []);
});

test('Open Library book stays ahead of similarly named articles by other authors', async () => {
    globalThis.fetch = async url => String(url).includes('openlibrary.org') ? Response.json({ docs: [{
        key: '/works/OL19650342W', title: 'Game Programming Patterns', author_name: ['Robert Nystrom']
    }] }) : Response.json({ message: { items: [{ title: ['Game patterns: patterns for game programming'],
        DOI: '10.1145/2581507.2581518', author: [{ given: 'David', family: 'Ferreira' }] }] } });
    const result = await browse({ query, sources: ['openlibrary', 'crossref'] });
    assert.equal(result.papers.length, 2);
    assert.equal(result.papers[0].title, 'Game Programming Patterns');
    assert.equal(result.papers[0].primary_url, 'https://openlibrary.org/works/OL19650342W');
});

test('XML source adapters work in Node with the browser-compatible parser', async () => {
    globalThis.fetch = async url => {
        if (String(url).includes('esearch.fcgi')) return Response.json({ esearchresult: { idlist: ['123'] } });
        if (String(url).includes('efetch.fcgi')) return new Response('<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article><ArticleTitle>PubMed parser test</ArticleTitle><AuthorList><Author><LastName>Nystrom</LastName><ForeName>Robert</ForeName></Author></AuthorList></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>');
        return new Response('<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>http://arxiv.org/abs/1512.03385v1</id><title>Deep Residual Learning for Image Recognition</title><author><name>Kaiming He</name></author><published>2015-12-10</published><summary>Residual learning</summary></entry></feed>');
    };
    const result = await browse({ query: 'residual learning', sources: ['arxiv', 'pubmed'] });
    assert.equal(result.papers.length, 2);
    assert.ok(result.papers.some(p => p.authors.includes('Kaiming He')));
    assert.ok(result.papers.some(p => p.title === 'PubMed parser test'));
    assert.equal(result.partial, false);
});
