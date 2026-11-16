#!/usr/bin/env node
// Lint the demo fragments: one `demo-root`, a `data-source` naming a real file, no
// <script> or remote URL, and every class backed by the compiled CSS (catches invented
// classes). Hook classes the app styles from JS or a library can be allowed.
//   node validate-demos.mjs --repo <app root> [--docs docs/ui-inventory] [--allow a,b,c]
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

const argv = process.argv.slice(2);
const opt = (k, d) => (argv.includes(`--${k}`) ? argv[argv.indexOf(`--${k}`) + 1] : d);
const repo = resolve(opt("repo", "."));
const demos = join(repo, opt("docs", "docs/ui-inventory"), "demos");
const built = join(repo, ".demo-build/out/assets");
const css = readFileSync(join(built, readdirSync(built).find((f) => f.endsWith(".css"))), "utf8");
const allow = new Set(["demo-root", "lucide", "group", "peer", ...(opt("allow", "").split(",").filter(Boolean))]);
const decode = (s) => s.replace(/&amp;/g, "&").replace(/&quot;/g, "\"").replace(/&#39;/g, "'");
const escapeClass = (c) => c.replace(/([^a-zA-Z0-9_-])/g, "\\$1");
const known = (c) => css.includes(`.${escapeClass(c)}`) || css.includes(`.${c}`);

const problems = [];
const files = readdirSync(demos).filter((f) => f.endsWith(".html"));
for (const file of files) {
  const html = readFileSync(join(demos, file), "utf8").trim();
  const issue = (text) => problems.push(`${file}: ${text}`);
  if (!/^<div[^>]*class="[^"]*\bdemo-root\b/.test(html)) issue('root is not <div class="demo-root">');
  if (/<script/i.test(html)) issue("contains <script>");
  if (/(src|href)="https?:/i.test(html)) issue("remote URL");
  const source = html.match(/data-source="([^"]+)"/)?.[1];
  if (!source) issue("no data-source");
  else for (const ref of source.split(/[\s,;]+/).filter(Boolean)) {
    if (!existsSync(join(repo, ref.replace(/:\d+(-\d+)?$/, "")))) issue(`data-source file missing: ${ref}`);
  }
  const unknown = new Set();
  for (const m of html.matchAll(/class="([^"]*)"/g)) {
    for (const c of decode(m[1]).split(/\s+/).filter(Boolean)) {
      if (allow.has(c) || /^(group|peer)\//.test(c) || c.startsWith("lucide-")) continue;
      if (!known(c)) unknown.add(c);
    }
  }
  if (unknown.size) issue(`classes with no CSS: ${[...unknown].slice(0, 12).join(" ")}${unknown.size > 12 ? ` +${unknown.size - 12}` : ""}`);
}
console.log(`checked ${files.length} demo fragments, ${problems.length} problem(s)`);
for (const p of problems) console.log(`  ${p}`);
process.exitCode = problems.length ? 1 : 0;
