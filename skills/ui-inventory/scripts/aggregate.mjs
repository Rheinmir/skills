#!/usr/bin/env node
// Merge the JSON blocks of the inventory reports: catalogue status counts from the
// numbered parts, and the raw "new" component names from the file-map parts (M-*.md),
// then check that canon.json (group → canonical name → raw aliases) covers every raw name.
//   node aggregate.mjs --docs docs/ui-inventory [--json out.json]
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const argv = process.argv.slice(2);
const opt = (k, d) => (argv.includes(`--${k}`) ? argv[argv.indexOf(`--${k}`) + 1] : d);
const docs = resolve(opt("docs", "docs/ui-inventory"));
const parts = join(docs, "parts");
const lastJson = (file) => {
  const m = [...readFileSync(join(parts, file), "utf8").matchAll(/```json\s*\n([\s\S]*?)\n\s*```/g)].at(-1);
  if (!m) return [];
  try { return JSON.parse(m[1]); } catch (error) { console.log(`WARN ${file}: JSON block does not parse (${error.message})`); return []; }
};

const catalogue = [];
const map = [];
for (const file of readdirSync(parts).filter((f) => f.endsWith(".md") && !f.startsWith("_")).sort()) {
  for (const row of lastJson(file)) {
    if (typeof row?.n === "number") catalogue.push({ ...row, part: file });
    else if (row?.file) map.push({ ...row, part: file });
  }
}
const counts = catalogue.reduce((acc, r) => ({ ...acc, [r.status]: (acc[r.status] ?? 0) + 1 }), {});
const raw = new Map();
for (const r of map) if (r.new && r.new !== "non-visual") raw.set(r.new, [...(raw.get(r.new) ?? []), `${r.file}:${r.line} ${r.component}`]);

console.log(`catalogue rows ${catalogue.length}`, counts);
console.log(`file-map rows ${map.length} from ${new Set(map.map((r) => r.file)).size} files; raw new names ${raw.size}`);

const canonFile = join(docs, "canon.json");
if (existsSync(canonFile)) {
  const groups = JSON.parse(readFileSync(canonFile, "utf8"));
  const aliases = new Set(Object.values(groups).flatMap((g) => Object.values(g).flat()));
  const canonical = Object.values(groups).reduce((n, g) => n + Object.keys(g).length, 0);
  const uncovered = [...raw.keys()].filter((k) => !aliases.has(k));
  const unused = [...aliases].filter((a) => !raw.has(a));
  console.log(`canon.json: ${canonical} canonical names in ${Object.keys(groups).length} groups`);
  console.log(`uncovered raw names: ${uncovered.length ? uncovered.join("; ") : "none"}`);
  console.log(`aliases matching nothing: ${unused.length ? unused.join("; ") : "none"}`);
  process.exitCode = uncovered.length ? 1 : 0;
} else {
  console.log("no canon.json yet; raw names by frequency:");
  for (const [k, v] of [...raw.entries()].sort((a, b) => b[1].length - a[1].length)) console.log(`${String(v.length).padStart(4)}  ${k}`);
}
const jsonOut = opt("json");
if (jsonOut) writeFileSync(jsonOut, JSON.stringify({ catalogue, map, raw: Object.fromEntries(raw) }, null, 1));
