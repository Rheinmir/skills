#!/usr/bin/env node
// Check every `path:line` reference and every cited code sample in inventory Markdown
// against the source tree. A sample is cited by a `path:start-end` within the 3 lines above
// its fence, or by `/* path:start-end */` / `// path:start-end` lines inside the fence;
// every non-empty line must appear (trimmed) within that range ±2 lines. Blocks preceded by
// "Đề xuất" are proposals and are skipped.
//   node verify-refs.mjs --repo <app root> <file.md>...
import { existsSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";

const argv = process.argv.slice(2);
const repoAt = argv.indexOf("--repo");
const repo = resolve(repoAt >= 0 ? argv[repoAt + 1] : ".");
const targets = argv.filter((a, i) => a !== "--repo" && argv[i - 1] !== "--repo");
if (!targets.length) {
  console.error("usage: verify-refs.mjs --repo <root> <file.md>...");
  process.exit(2);
}

const cache = new Map();
const lines = (path) => {
  if (!cache.has(path)) {
    const full = join(repo, path);
    cache.set(path, existsSync(full) ? readFileSync(full, "utf8").split(/\r?\n/) : null);
  }
  return cache.get(path);
};
const norm = (l) => l.replace(/\s+$/, "").trimStart();
const ROOTS = "src|app|lib|electron|server|shared|packages|components|pages|docs|scripts|companion|public";
const REF = new RegExp(`\`((?:${ROOTS})\\/[\\w./@\\-[\\]]+\\.\\w+):(\\d+)(?:-(\\d+))?`, "g");
const INLINE = new RegExp(`^(?:\\/\\*|\\/\\/)\\s*\`?((?:${ROOTS})\\/[\\w./@\\-[\\]]+\\.\\w+):(\\d+)(?:-(\\d+))?\`?\\s*(?:\\*\\/)?$`);

let refs = 0;
let samples = 0;
const failures = [];
for (const target of targets) {
  const doc = readFileSync(target, "utf8").split(/\r?\n/);
  for (const [i, line] of doc.entries()) {
    for (const [, path, start] of line.matchAll(REF)) {
      refs += 1;
      const src = lines(path);
      if (!src) failures.push(`${target}:${i + 1} missing file ${path}`);
      else if (Number(start) > src.length) failures.push(`${target}:${i + 1} ${path}:${start} past end (${src.length} lines)`);
    }
  }
  for (let i = 0; i < doc.length; i += 1) {
    if (!/^\s*```(tsx|ts|jsx|js|mjs|css|scss|html|vue|svelte)\s*$/.test(doc[i])) continue;
    const end = doc.findIndex((l, at) => at > i && /^\s*```\s*$/.test(l));
    if (end < 0) break;
    const context = doc.slice(Math.max(0, i - 3), i).join(" ");
    if (/Đề xuất|Proposal/i.test(context)) { i = end; continue; }
    const block = doc.slice(i + 1, end).map(norm);
    const pieces = [];
    for (const [at, l] of block.entries()) {
      const m = l.match(INLINE);
      if (m) pieces.push({ cite: m, at, body: [] });
      else if (pieces.length) pieces.at(-1).body.push(l);
    }
    if (!pieces.length) {
      const cite = [...context.matchAll(REF)].at(-1);
      if (cite) pieces.push({ cite, at: 0, body: block });
    }
    for (const { cite: [, path, a, b], at, body } of pieces) {
      samples += 1;
      const src = lines(path);
      if (!src) { failures.push(`${target}:${i + 2 + at} sample cites missing ${path}`); continue; }
      const window = src.slice(Math.max(0, Number(a) - 3), Math.min(src.length, Number(b ?? a) + 2)).map(norm);
      const missing = body.filter((l) => l && !/^(\/\/|\/\*)?\s*(…|\.\.\.)\s*(\*\/)?$/.test(l) && !window.includes(l));
      if (missing.length) failures.push(`${target}:${i + 2 + at} sample ${path}:${a}-${b ?? a}: ${missing.length} line(s) not in source, first ${JSON.stringify(missing[0]).slice(0, 120)}`);
    }
    i = end;
  }
}
console.log(`checked ${refs} path:line references and ${samples} code samples in ${targets.length} file(s)`);
for (const f of failures) console.log(`FAIL ${f}`);
process.exitCode = failures.length ? 1 : 0;
