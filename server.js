#!/usr/bin/env node
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import { z } from 'zod';
import { browse, download, runPdf, sources, DEFAULT_MIN_RELEVANCE } from './adapter.js';
import packageInfo from './package.json' with { type: 'json' };

// Source diagnostics belong on stderr; stdout is reserved for MCP messages.
console.log = console.error;
const version = packageInfo.version;
const search = {
    query: z.string().trim().min(1).max(2000).describe('Title, author, DOI, or research topic'),
    limit: z.number().int().min(1).max(100).default(25).describe('Maximum candidates per source; results are merged and ranked together'),
    pdf_only: z.boolean().default(false),
    min_relevance: z.number().min(0).max(100).default(DEFAULT_MIN_RELEVANCE).describe('Minimum lexical relevance score, 0–100; default 25 removes weak matches. Use 0 for all candidates. Scores are not confidence probabilities.'),
    max_results: z.number().int().min(1).max(1000).optional().describe('Optional cap on final merged, filtered results; e.g. 20 for focused research. limit still controls candidates per source.'),
    sources: z.array(z.enum(sources)).min(1).optional().describe('Omit to search the same sources as sourcecrate.org')
};
const conversion = { file_path: z.string().min(1), output_path: z.string().min(1).optional() };
const help = {
    website: 'https://sourcecrate.org',
    search: 'Use browse_papers with a title and author together, or a focused academic topic. The site and MCP default to min_relevance 25; use 0 for all candidates or a higher cutoff for precision. max_results caps final results; limit is per source. Scores are lexical relevance, not confidence. Review filtered_out, total_matching and truncated. primary_url matches the site result header. Use regular web research for product documentation and practical guides.',
    availability: 'Providers may fail, rate-limit, or return different candidates over time or due to browser CORS. Inspect partial and source_status errors and warnings. Zenodo can fall back to its DataCite index (via: datacite); coverage may differ and direct file links are unavailable there. Links are metadata, not a guarantee of free access.',
    pdf: 'Search PDF links have verification: unverified. Provider metadata and URL suffixes do not prove a PDF exists. download_papers validates downloaded PDF contents before writing and returns verification evidence; bibliographic identity still requires review. PDF tools require uv on PATH; pinned dependencies are installed on first use. Existing files are never overwritten.',
    migration: 'v3 uses Node.js 22.12+ and npx. Replace the v2 uvx launch command. Category routing, YAML configuration, HTTP hosting and the independent Python search engine have been removed.',
    docs: 'https://github.com/JosiahSiegel/sourcecrate-mcp#readme'
};

export function createServer() {
    const server = new McpServer({ name: 'sourcecrate', version }, { capabilities: { tools: {} } });
    function tool(name, description, schema, handler, writes = false) {
        server.registerTool(name, { description, inputSchema: z.object(schema).strict(),
            annotations: { readOnlyHint: !writes, destructiveHint: false, openWorldHint: true } },
        async (args, ctx) => {
            try {
                const result = await handler(args, ctx.mcpReq.signal);
                return { content: [{ type: 'text', text: JSON.stringify(result) }], structuredContent: result,
                    ...(result.success === false ? { isError: true } : {}) };
            } catch (error) {
                return { isError: true, content: [{ type: 'text', text: error.message }] };
            }
        });
    }
    tool('browse_papers', 'Search SourceCrate sources concurrently. Returns ranked papers, links, scores and provider errors. Start here for research; does not download.', search, browse);
    tool('browse_papers_streaming', 'Compatibility alias for browse_papers. Searches concurrently and returns one final ranked result with source statistics.', search, browse);
    tool('download_papers', 'Download PDFs from a SourceCrate search or explicit PDF links. Supply either query or pdf_urls. Writes local files, optionally converting to Markdown. Requires uv.', {
        query: search.query.optional(), pdf_urls: z.array(z.url()).min(1).max(10).optional(),
        limit: z.number().int().min(1).max(10).default(5), sources: search.sources,
        min_relevance: search.min_relevance,
        output_dir: z.string().min(1), convert_to_markdown: z.boolean().default(true)
    }, download, true);
    for (const format of ['text', 'markdown']) {
        tool(`convert_pdf_to_${format}`, `Convert a local PDF to ${format}. Writes a new file; requires uv.`, conversion,
            (args, signal) => runPdf({ ...args, operation: 'convert', format }, signal), true);
    }
    tool('batch_convert_pdfs', 'Convert PDFs in a local directory to text or Markdown. Writes new files; requires uv.', {
        directory: z.string().min(1), output_dir: z.string().min(1).optional(),
        format: z.enum(['text', 'markdown']).default('markdown')
    }, (args, signal) => runPdf({ ...args, operation: 'batch' }, signal), true);
    tool('get_status', 'List supported sources and runtime requirements. Does not issue live searches.', {}, async () => ({
        version, sources, search_engine: 'sourcecrate/search', search_engine_revision: packageInfo.dependencies.sourcecrate, website: help.website,
        pdf_runtime: 'uv (installed separately; dependencies fetched on first PDF use)'
    }));
    tool('get_help', 'Read installation, search and PDF usage guidance.', {}, async () => help);
    return server;
}

if (process.argv.includes('--version')) process.stdout.write(`${version}\n`);
else if (process.argv.includes('--help')) process.stdout.write('SourceCrate MCP: run sourcecrate with no arguments for stdio. Node.js 22.12+; uv required only for PDF tools.\n');
else serveStdio(createServer, { onerror: error => console.error(error) });
