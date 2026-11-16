#!/usr/bin/env node
// Compile the demo fragments with the app's own stylesheet so they draw with its real
// utilities, component classes and skin tokens. Works for Tailwind v4 apps through the
// repo's own `vite` + `@tailwindcss/vite`; the build lives in <repo>/.demo-build (git-excluded).
//   node compile-demos.mjs --repo <app root> --css src/styles.css [--docs docs/ui-inventory]
import { execFileSync } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";

const argv = process.argv.slice(2);
const opt = (k, d) => (argv.includes(`--${k}`) ? argv[argv.indexOf(`--${k}`) + 1] : d);
const repo = resolve(opt("repo", "."));
const appCss = opt("css");
if (!appCss || !existsSync(join(repo, appCss))) throw new Error("--css <path to the app's main stylesheet, relative to --repo> is required");
const demos = join(repo, opt("docs", "docs/ui-inventory"), "demos");
const build = join(repo, ".demo-build");
mkdirSync(build, { recursive: true });

const exclude = join(repo, ".git/info/exclude");
if (existsSync(exclude) && !readFileSync(exclude, "utf8").includes(".demo-build/")) appendFileSync(exclude, "\n.demo-build/\n");

const decode = (s) => s.replace(/&amp;/g, "&").replace(/&quot;/g, "\"").replace(/&#39;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
const classes = new Set();
for (const file of readdirSync(demos).filter((f) => f.endsWith(".html"))) {
  for (const m of readFileSync(join(demos, file), "utf8").matchAll(/class="([^"]*)"/g)) for (const c of decode(m[1]).split(/\s+/)) if (c) classes.add(c);
}
writeFileSync(join(build, "classes.txt"), [...classes].join("\n"));
const rel = (p) => relative(build, p).replace(/\\/g, "/");
writeFileSync(join(build, "demo.css"), `@import "${rel(join(repo, appCss))}";\n@source "${rel(demos)}";\n@source "./classes.txt";\n`);
writeFileSync(join(build, "index.html"), '<!doctype html><html><head><link rel="stylesheet" href="./demo.css"></head><body></body></html>\n');
writeFileSync(join(build, "vite.demo.config.mjs"), `import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
export default defineConfig({
  root: import.meta.dirname,
  logLevel: "warn",
  plugins: [tailwindcss()],
  build: { outDir: "out", emptyOutDir: true, cssCodeSplit: false, assetsInlineLimit: 100000000 },
});
`);

const vite = join(repo, "node_modules/vite/bin/vite.js");
if (!existsSync(vite) || !existsSync(join(repo, "node_modules/@tailwindcss/vite"))) {
  throw new Error("needs vite and @tailwindcss/vite installed in the app repo (pnpm install). For a non-Tailwind app, pass the built CSS to build-page.mjs with --css instead.");
}
execFileSync(process.execPath, [vite, "build", "--config", join(build, "vite.demo.config.mjs")], { cwd: repo, stdio: ["ignore", "ignore", "inherit"] });
const out = join(build, "out/assets");
const css = readdirSync(out).find((f) => f.endsWith(".css"));
console.log(`${classes.size} classes from demos → ${join(out, css)} (${readFileSync(join(out, css)).length} bytes)`);
