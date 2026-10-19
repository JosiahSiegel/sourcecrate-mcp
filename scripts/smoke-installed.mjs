import { execFileSync } from 'node:child_process';
import { mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { checkProtocol } from '../tests/protocol.mjs';
import assert from 'node:assert/strict';

const npm = process.env.npm_execpath;
if (!npm) throw new Error('Run using npm run test:install');
const packed = JSON.parse(execFileSync(process.execPath, [npm, 'pack', '--json'], { encoding: 'utf8' }))[0];
assert.ok(packed.files.every(file => !/(__pycache__|source_crate\/|tests\/)/.test(file.path)), 'Distribution must exclude legacy code, tests and bytecode');
const directory = await mkdtemp(join(tmpdir(), 'sourcecrate-installed-'));
execFileSync(process.execPath, [npm, 'install', '--prefix', directory, '--no-audit', '--no-fund', join(process.cwd(), packed.filename)], { stdio: 'inherit' });
const version = execFileSync(process.execPath, [npm, 'exec', '--offline', '--prefix', directory, '--', 'sourcecrate', '--version'], { encoding: 'utf8', cwd: directory }).trim();
assert.equal(version, packed.version);
const server = join(directory, 'node_modules', 'sourcecrate-mcp', 'server.js');
console.log(JSON.stringify(await checkProtocol(server)));
