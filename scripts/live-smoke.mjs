// Optional live-provider check; deliberately excluded from CI and the distribution.
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { fileURLToPath } from 'node:url';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import assert from 'node:assert/strict';

const client = new Client({ name: 'sourcecrate-live-check', version: '1.0.0' });
const directory = await mkdtemp(join(tmpdir(), 'sourcecrate-live-v3-'));
const transport = new StdioClientTransport({ command: process.execPath,
    args: [process.argv[2] || fileURLToPath(new URL('../server.js', import.meta.url))],
    cwd: directory, env: { ...process.env }, stderr: 'pipe' });
transport.stderr.on('data', data => process.stderr.write(data));
try {
    await client.connect(transport);
    async function call(name, args) {
        const result = await client.callTool({ name, arguments: args }, undefined, { timeout: 300000 });
        assert.ok(!result.isError, JSON.stringify(result));
        return result.structuredContent ?? JSON.parse(result.content[0].text);
    }
    const search = await call('browse_papers', { query: 'game programming patterns Robert Nystrom' });
    assert.equal(search.papers[0].title, 'Game Programming Patterns');
    assert.ok(search.papers[0].authors.includes('Robert Nystrom'));
    console.log(JSON.stringify({ search: search.papers[0], total: search.total_results, source_status: search.source_status }));
    const downloads = await call('download_papers', { query: 'Deep Residual Learning for Image Recognition Kaiming He', limit: 1,
        output_dir: directory, convert_to_markdown: true });
    console.log(JSON.stringify({ downloads, directory }));
    assert.ok(downloads.downloaded > 0, 'No live PDF downloaded; inspect provider failures above');
    const pdf = downloads.files.find(file => file.success).pdf_path;
    const text = await call('convert_pdf_to_text', { file_path: pdf });
    assert.match(await readFile(text.output_path, 'utf8'), /residual/i);
    console.log(JSON.stringify({ text }));
} finally { await client.close(); }
