import { spawn, spawnSync } from 'node:child_process';
import { existsSync, readdirSync, statSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
process.chdir(root);
const candidates = [
  ...(process.env.RETAIL_PYTHON ? [[process.env.RETAIL_PYTHON, []]] : []),
  [path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python'), []],
  ...(process.env.USERPROFILE ? [[path.join(process.env.USERPROFILE, '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'), []]] : []),
  ['python', []], ['python3', []], ['py', ['-3']],
];
const chosen = candidates.find(([exe, args]) => spawnSync(exe, [...args, '-c', 'import sys; assert sys.version_info >= (3,10)'], { stdio: 'ignore' }).status === 0);
if (!chosen) {
  console.error('Python 3.10+ is required. Install Python, then run npm start again.');
  process.exit(1);
}
const [python, prefix] = chosen;
function run(exe, args, options = {}) {
  const result = spawnSync(exe, args, { stdio: 'inherit', ...options });
  if (result.status !== 0) process.exit(result.status || 1);
}
const imports = spawnSync(python, [...prefix, '-c', 'import pandas,numpy,openpyxl'], { stdio: 'ignore' });
if (imports.status !== 0) run(python, [...prefix, '-m', 'pip', 'install', '-r', 'requirements.txt']);
if (!existsSync('data/retail.sqlite') || !existsSync('data/metadata.json')) run(python, [...prefix, 'scripts/prepare_data.py']);
function newest(dir) {
  return Math.max(...readdirSync(dir, { withFileTypes: true }).map(d => d.isDirectory() ? newest(path.join(dir, d.name)) : statSync(path.join(dir, d.name)).mtimeMs));
}
if (!existsSync('dist/index.html') || newest('src') > statSync('dist/index.html').mtimeMs) {
  if (!existsSync('node_modules')) run(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['install'], { shell: process.platform === 'win32' });
  run(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'build'], { shell: process.platform === 'win32' });
}
const server = spawn(python, [...prefix, 'server/app.py'], { stdio: 'inherit' });
server.on('exit', code => process.exit(code || 0));
server.on('error', err => { console.error(err.message); process.exit(1); });
process.on('SIGINT', () => server.kill());
process.on('SIGTERM', () => server.kill());
