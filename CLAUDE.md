# SourceCrate MCP development

This repository is a thin Node.js stdio MCP adapter. Search, ranking, deduplication and link selection are imported from the pinned `sourcecrate` dependency, maintained in the neighboring website repository. PDF file operations live in `pdf/` and run through uv only when requested.

Run `npm ci`, `npm test`, `npm run test:pdf` and `npm run test:install`. The installation test uses a fresh directory outside the checkout and exercises all eight tools. Keep public-download validation, no-overwrite behavior and stderr-only diagnostics intact. Update README, package version and both MCP config files together for releases.
