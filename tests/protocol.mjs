import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { mkdtemp, readFile, mkdir, copyFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';
import { query } from './mock-sources.mjs';

export async function checkProtocol(serverPath, mode = 'legacy') {
    const directory = await mkdtemp(join(tmpdir(), 'sourcecrate-protocol-'));
    const client = new Client({ name: 'sourcecrate-install-test', version: '1.0.0' });
    const transport = new StdioClientTransport({ command: process.execPath,
        args: ['--import', new URL('./mock-sources.mjs', import.meta.url).href, serverPath],
        cwd: directory, env: { ...process.env, SOURCECRATE_TEST_FIXTURES: '1' }, stderr: 'pipe' });
    let diagnostics = '';
    transport.stderr.on('data', data => { diagnostics += data; });
    try {
        await client.connect(transport, { mode });
        const { tools } = await client.listTools();
        assert.equal(tools.length, 8);
        async function call(name, args = {}, expectError = false) {
            const result = await client.callTool({ name, arguments: args }, undefined, { timeout: 180000 });
            assert.equal(Boolean(result.isError), expectError, `${name}: ${JSON.stringify(result)}`);
            return result.structuredContent ?? JSON.parse(result.content[0].text);
        }
        assert.equal((await call('get_status')).sources.length, 9);
        assert.match((await call('get_help')).search, /title and author/);
        const normal = await call('browse_papers', { query });
        const alias = await call('browse_papers_streaming', { query });
        assert.equal(normal.papers[0].doi, '10.1234/exact');
        assert.deepEqual(normal.papers, alias.papers);
        assert.equal(normal.filters.min_relevance, 25);
        assert.equal(normal.filtered_out, 1);
        const all = await call('browse_papers', { query, min_relevance: 0 });
        assert.equal(all.papers.length, 3);
        const capped = await call('browse_papers', { query, max_results: 1 });
        assert.equal(capped.papers.length, 1);
        assert.equal(capped.total_matching, 2);
        assert.equal(capped.truncated, true);
        assert.equal(normal.papers[0].primary_url, 'https://example.org/book');
        for (const tool of ['browse_papers', 'browse_papers_streaming']) {
            const recovered = await call(tool, { query: 'provider recovery climate', min_relevance: 0, sources: ['datacite', 'zenodo'] });
            assert.equal(recovered.papers.length, 2);
            assert.equal(recovered.source_status.find(s => s.source === 'datacite').error, null);
            assert.equal(recovered.source_status.find(s => s.source === 'zenodo').via, 'datacite');
            assert.match(recovered.source_status.find(s => s.source === 'zenodo').warning, /direct file links/);
            assert.equal(recovered.partial, true);
            assert.ok(recovered.papers.every(p => p.pdf_url === null));
        }
        const downloads = await call('download_papers', { query, output_dir: join(directory, 'downloads') });
        assert.equal(downloads.downloaded, 0);
        const blocked = await call('download_papers', { pdf_urls: ['http://127.0.0.1/private.pdf'], output_dir: join(directory, 'downloads') });
        assert.equal(blocked.downloaded, 0);
        assert.match(blocked.files[0].errors[0].error, /public addresses/);
        const pdf = join(directory, 'sample.pdf');
        await copyFile(new URL('./fixtures/sample.pdf', import.meta.url), pdf);
        const text = await call('convert_pdf_to_text', { file_path: pdf });
        assert.match(await readFile(text.output_path, 'utf8'), /SourceCrate PDF validation/);
        const markdown = await call('convert_pdf_to_markdown', { file_path: pdf });
        assert.match(await readFile(markdown.output_path, 'utf8'), /SourceCrate PDF validation/);
        const batchDir = join(directory, 'batch');
        await mkdir(batchDir);
        const batch = await call('batch_convert_pdfs', { directory, output_dir: batchDir, format: 'text' });
        assert.equal(batch.converted, 1);
        await call('convert_pdf_to_text', { file_path: pdf }, true); // no overwrites
        const invalid = await client.callTool({ name: 'browse_papers', arguments: { query: '' } });
        assert.equal(invalid.isError, true);
        return { mode, tools: tools.map(tool => tool.name), directory };
    } catch (error) {
        error.message += `\nServer diagnostics: ${diagnostics}`;
        throw error;
    } finally { await client.close(); }
}
