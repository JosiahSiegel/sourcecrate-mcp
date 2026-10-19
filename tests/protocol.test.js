import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { checkProtocol } from './protocol.mjs';
for (const mode of ['legacy', 'auto']) {
    test(`all eight tools work over MCP stdio (${mode})`, { timeout: 240000 }, () =>
        checkProtocol(fileURLToPath(new URL('../server.js', import.meta.url)), mode));
}
