# SourceCrate MCP

Search [SourceCrate](https://sourcecrate.org) from any MCP-capable AI agent. This is a small stdio adapter around the **same search engine used by the website**, with PDF downloading and text/Markdown conversion.

## Install

Install **Node.js 22.12 or newer** (includes `npx`). Add the following to your agent's MCP configuration, then restart or reconnect the agent:

```json
{
  "mcpServers": {
    "sourcecrate": {
      "command": "npx",
      "args": [
        "--yes",
        "--package=https://github.com/JosiahSiegel/sourcecrate-mcp/releases/download/v3.0.0/sourcecrate-mcp-3.0.0.tgz",
        "sourcecrate"
      ]
    }
  }
}
```

The same configuration is available as [mcp-config.json](mcp-config.json). No Git checkout, API key, hosted service, account, or Python installation is needed for search. First launch downloads the versioned package; later launches use npm's cache. Agents must support local stdio MCP servers; cloud agents without local process execution cannot use this transport.

For **PDF downloading and conversion**, also install [uv](https://docs.astral.sh/uv/getting-started/installation/) and ensure it is on the agent's PATH. The helper automatically installs Python and its locked PDF dependencies on first use. Allow up to three minutes for a cold first call. Search never starts Python.

For clients on Windows that cannot launch `npx` directly, use `"command": "cmd"` and prepend `"/c", "npx"` to `args`. Restart the client after installing Node or uv so it receives the updated PATH.

Check the launcher with:

```sh
npx --yes --package=https://github.com/JosiahSiegel/sourcecrate-mcp/releases/download/v3.0.0/sourcecrate-mcp-3.0.0.tgz sourcecrate --version
```

Then ask your agent to call `get_status` and search for `game programming patterns Robert Nystrom`.

## Tools

| Tool | Purpose |
| --- | --- |
| `browse_papers` | Ranked search results, scores, access links, and per-source errors |
| `browse_papers_streaming` | Compatibility alias; concurrent search returning one final ranked response |
| `download_papers` | Search and download up to 10 ranked PDFs, optionally converting to Markdown |
| `convert_pdf_to_text` | Extract text from a local PDF |
| `convert_pdf_to_markdown` | Convert a local PDF into Markdown |
| `batch_convert_pdfs` | Convert up to 100 PDFs in a directory |
| `get_status` | List sources and runtime requirements |
| `get_help` | Usage and migration guidance |

Example search arguments:

```json
{"query":"game programming patterns Robert Nystrom","limit":25}
```

`limit` is the maximum number of candidates **per source**. All candidates are deduplicated and ranked together. Optional `sources` selects from the names returned by `get_status`; omit it for the website's defaults. `pdf_only` filters to available PDF links. `relevance_score` is 0–100. `primary_url` is the same destination as the website's clickable result header; `access_links` follows the same PDF/page ordering.

Exact title phrases and matching authors rank ahead of partial title or abstract mentions. The engine cannot return a book or paper that its providers do not index. Browser CORS, rate limits, changing provider data, and response timing can affect which candidates arrive. Inspect `partial` and `source_status`; identical candidates use identical scoring and ordering in both clients.

Example download arguments (use a path on the machine running the MCP):

```json
{"query":"deep residual learning for image recognition","limit":1,"output_dir":"./papers","convert_to_markdown":true}
```

When you already have a PDF link from a result, supply `pdf_urls` instead of `query`
to avoid repeating the search: `{"pdf_urls":["https://example.org/paper.pdf"],"output_dir":"./papers"}`.

Downloads try up to three supplied PDF links per paper, validate public destinations at every redirect, cap each file at 25 MiB, and verify PDF contents before saving. Publisher login pages and access failures are reported; there is no paywall bypass. Conversion errors are reported separately from successful PDF downloads. Existing files are never overwritten. PDF calls have a five-minute server deadline; configure the client timeout accordingly for large batches. OCR is not installed; image-only scans may produce little or no text.

## Migrating from v2

Replace the old `uvx ... sourcecrate` launch entry with the `npx` entry above. Version 3 retains all eight tool names but removes the separate Python search engine, category routing, YAML/custom-source configuration, caches, and HTTP server. Old `force_category`, `debug`, status reload/health-check parameters, and conversion title/author parameters are no longer accepted. Responses are structured objects containing `papers`, statistics and source errors. Download calls require an explicit `output_dir`. The v2.1.3 release remains available for older configurations.

SourceCrate is a static GitHub Pages website; there is no hosted SourceCrate search API. The adapter imports the website's engine at a pinned repository revision and makes the same provider requests locally. Update that dependency when releasing search changes; ranking code belongs in the website repository.

## Development and validation

```sh
npm ci
npm test
npm run test:pdf
npm run test:install
```

Tests compare MCP results directly with the shared engine, exercise all eight tools over real MCP stdio (legacy and negotiated protocols), and verify real PDF conversion and download boundaries. The install test packs the distribution, installs it in a fresh temporary directory outside the checkout, and calls all eight tools. Provider fixtures make CI repeatable; live provider checks remain separate.

CI runs on Linux, Windows, and macOS with Node 22 and uv. Tags must match `package.json`; the release workflow publishes the tested tarball and portable configuration only after all platforms pass. There is no npm registry credential or deployment service to configure.
Run `node scripts/live-smoke.mjs` separately to check the real Nystrom book search,
a public CVF PDF download, and text extraction; it requires live providers to be available.

The implementation is `server.js` (MCP schemas), `adapter.js` (shared search + helper invocation), and `pdf/` (file operations). Do not add a second ranker or provider implementation here. Keep protocol diagnostics on stderr.

MIT licensed; see [LICENSE](LICENSE).
