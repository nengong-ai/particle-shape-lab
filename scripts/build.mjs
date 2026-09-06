#!/usr/bin/env node
// Copy beside the exported project's package.json, then run: node build.mjs
import { mkdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

function main() {
  const [major, minor] = process.versions.node.split('.').map(Number);
  if (major < 22 || (major === 22 && minor < 13)) {
    throw new Error(`Node >=22.13.0 is required; found ${process.versions.node}`);
  }
  const args = process.argv.slice(2);
  if (args.length > 1 || (args.length === 1 && args[0] !== '--check')) {
    throw new Error('Usage: node build.mjs [--check]');
  }
  const location = dirname(fileURLToPath(import.meta.url));
  const root = existsSync(join(location, 'package.json')) ? location : dirname(location);
  if (!existsSync(join(root, 'package.json'))) {
    throw new Error('Copy build.mjs to the exported project root beside package.json.');
  }
  const tasks = [['typescript/bin/tsc', ['--noEmit']]];
  if (args[0] !== '--check') tasks.push(['vite/bin/vite.js', ['build']]);
  for (const [entry] of tasks) {
    if (!existsSync(join(root, 'node_modules', entry))) {
      throw new Error(`Missing local dependency: ${entry}. Provide dependencies matching the original lockfile first; this tool never installs them.`);
    }
  }
  const temp = join(root, '.tmp');
  const cache = join(temp, 'node-compile-cache');
  mkdirSync(cache, { recursive: true });
  const env = { ...process.env, TMPDIR: temp, TMP: temp, TEMP: temp, NODE_COMPILE_CACHE: cache };
  for (const [entry, flags] of tasks) {
    const result = spawnSync(process.execPath, [join(root, 'node_modules', entry), ...flags], {
      cwd: root, env, stdio: 'inherit', shell: false,
    });
    if (result.error) throw result.error;
    if (result.status !== 0) {
      throw new Error(`${entry} failed (${result.signal ?? result.status}).`);
    }
  }
}

try {
  main();
} catch (error) {
  console.error(`build: ${error.message}`);
  process.exitCode = 1;
}
