import { DOMParser } from 'linkedom';
import { searchPapers, sources } from 'sourcecrate/search';
import { getAccessLinks } from 'sourcecrate/access-links';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

globalThis.DOMParser ??= DOMParser;
export { sources };

export async function browse({ query, limit = 25, pdf_only = false, sources: selected }, signal) {
    const result = await searchPapers(query, { limit, pdfOnly: pdf_only, sources: selected, signal });
    return { ...result, query, papers: result.papers.map(paper => {
        const { pdfs, pages, firstUrl } = getAccessLinks(paper);
        return { ...paper, primary_url: firstUrl, access_links: [...pdfs, ...pages] };
    }) };
}

export function runPdf(request, signal) {
    return new Promise((resolve, reject) => {
        const child = spawn('uv', ['run', '--no-project', '--locked', '--script',
            fileURLToPath(new URL('./pdf/tools.py', import.meta.url))], {
            windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'], signal,
            env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
        });
        let stdout = '', stderr = '';
        const timer = setTimeout(() => { child.kill(); reject(new Error('PDF operation timed out after 5 minutes')); }, 300000);
        child.stdout.on('data', chunk => { stdout += chunk; });
        child.stderr.on('data', chunk => { stderr = (stderr + chunk).slice(-4000); });
        child.stdin.on('error', () => {});
        child.on('error', error => {
            clearTimeout(timer);
            reject(new Error(error.code === 'ENOENT' ? 'PDF tools require uv on PATH. Install uv: https://docs.astral.sh/uv/getting-started/installation/' : error.message));
        });
        child.on('close', code => {
            clearTimeout(timer);
            if (code !== 0) return reject(new Error(stderr || `PDF helper exited with code ${code}`));
            try { resolve(JSON.parse(stdout)); } catch { reject(new Error('Invalid PDF helper response')); }
        });
        child.stdin.end(JSON.stringify(request));
    });
}

export async function download(args, signal) {
    if (Boolean(args.query) === Boolean(args.pdf_urls?.length)) throw new Error('Supply either query or pdf_urls');
    const result = args.pdf_urls ? { papers: args.pdf_urls.map((url, i) => ({
        title: `Document ${i + 1}`, access_links: [{ type: 'pdf', url }]
    })), source_status: [], partial: false } : await browse({ ...args, pdf_only: true, limit: 25 }, signal);
    const papers = result.papers.filter(p => p.access_links.some(link => link.type === 'pdf')).slice(0, args.limit ?? 5);
    const files = await runPdf({ operation: 'download', papers, output_dir: args.output_dir,
        convert_to_markdown: args.convert_to_markdown ?? true }, signal);
    return { query: args.query ?? null, source_status: result.source_status, partial: result.partial, ...files };
}
