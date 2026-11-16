#!/usr/bin/env node
// Download the Name That UI catalogue (data.js: window.NT = {macos, web, styles, vs}) and
// write it as a numbered Markdown list the audit agents and build-page.mjs read.
//   node fetch-catalogue.mjs [--url https://uiux.giatbh.io.vn/namethatui/data.js] --out <docs>/parts/_catalogue.md
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import vm from "node:vm";

const args = Object.fromEntries(process.argv.slice(2).reduce((acc, v, i, a) => (v.startsWith("--") ? [...acc, [v.slice(2), a[i + 1]]] : acc), []));
const url = args.url ?? "https://uiux.giatbh.io.vn/namethatui/data.js";
const out = args.out ?? "docs/ui-inventory/parts/_catalogue.md";

const response = await fetch(url);
if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
const sandbox = { window: {} };
vm.runInNewContext(await response.text(), sandbox, { timeout: 2000 });
const nt = sandbox.window.NT;
if (!nt || typeof nt !== "object") throw new Error("data.js did not define window.NT");

let n = 0;
let md = `# Danh mục gốc\n\nNguồn: ${url}. Mỗi dòng: số thứ tự, \`nhóm/slug\`, **tên chuẩn**, mô tả.\n`;
const counts = {};
for (const group of Object.keys(nt)) {
  if (!Array.isArray(nt[group])) continue;
  md += `\n## ${group}\n`;
  for (const [slugName, name, description] of nt[group]) {
    n += 1;
    counts[group] = (counts[group] ?? 0) + 1;
    md += `${n}. \`${group}/${slugName}\` — **${name}** — ${description}\n`;
  }
}
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, md);
console.log(`${out}: ${n} entries`, counts);
