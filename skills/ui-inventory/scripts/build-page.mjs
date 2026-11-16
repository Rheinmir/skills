#!/usr/bin/env node
// Build ONE self-contained HTML page from an inventory folder: tabs per report, the
// demos rendered under each catalogue entry, a Gallery tab, and an A/B (old/new skin)
// comparison for every demo. Usage:
//   node build-page.mjs --repo <app root> [--docs docs/ui-inventory] [--blob <url>]
//     [--demo-blob <url>] [--css <compiled demo css>] --old midnight,daylight --new ctd-dots
//     [--names "midnight=Midnight,ctd-dots=CTD Dots"] [--brand "UI INVENTORY"] [--mark UI]
//     [--font <@fontsource dir>] [--drop-fonts "Inter Variable,…"] [--out ui-inventory.html]
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const args = {};
for (let i = 2; i < process.argv.length; i += 1) {
  const key = process.argv[i].replace(/^--/, "");
  args[key] = process.argv[i + 1]?.startsWith("--") || process.argv[i + 1] === undefined ? "true" : process.argv[(i += 1)];
}
const repo = resolve(args.repo ?? ".");
const docsDir = join(repo, args.docs ?? "docs/ui-inventory");
const partsDir = join(docsDir, "parts");
const demoDir = join(docsDir, "demos");
const blob = (args.blob ?? "").replace(/\/$/, "");
const demoBlob = (args["demo-blob"] ?? blob).replace(/\/$/, "");
const oldSkins = (args.old ?? "").split(",").filter(Boolean);
const newSkin = args.new ?? "";
const titleCase = (id) => id.split(/[-_]/).map((w) => w[0]?.toUpperCase() + w.slice(1)).join(" ");
const skinName = Object.fromEntries((args.names ?? "").split(",").filter(Boolean).map((p) => p.split("=")));
const nameOf = (id) => skinName[id] ?? titleCase(id);
const brand = args.brand ?? "UI INVENTORY";
const mark = args.mark ?? "UI";
const out = join(repo, args.out ?? "ui-inventory.html");
const ab = oldSkins.length > 0 && newSkin !== "";

async function loadMarked() {
  try {
    return (await import(pathToFileURL(createRequire(join(repo, "package.json")).resolve("marked")).href)).marked;
  } catch {
    const store = join(repo, "node_modules/.pnpm");
    const dir = existsSync(store) && readdirSync(store).filter((d) => d.startsWith("marked@")).sort().at(-1);
    if (dir) return (await import(pathToFileURL(join(store, dir, "node_modules/marked/lib/marked.esm.js")).href)).marked;
    throw new Error("marked not found: run `npm i -D marked` (or pnpm add -D marked) in the app repo, or pass a repo that has it");
  }
}
const marked = await loadMarked();

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const slug = (text) => text.trim().toLowerCase().replace(/<[^>]+>/g, "").replace(/[^\p{L}\p{N}\s_-]/gu, "").replace(/ /g, "-");
const lastJson = (text) => {
  const m = [...text.matchAll(/```json\s*\n([\s\S]*?)\n\s*```/g)].at(-1);
  try { return m ? JSON.parse(m[1]) : []; } catch { return []; }
};

const partFiles = existsSync(partsDir) ? readdirSync(partsDir).filter((f) => f.endsWith(".md")).sort((a, b) => (a.startsWith("_") ? 1 : 0) - (b.startsWith("_") ? 1 : 0) || a.localeCompare(b)) : [];
const docs = [{ id: "readme", file: join(docsDir, "README.md"), name: "README.md" }, ...partFiles.map((f) => ({ id: f.replace(/\.md$/, "").replace(/^_/, "").toLowerCase().replace(/[^a-z0-9-]/g, "-").replace(/-{2,}/g, "-"), file: join(partsDir, f), name: f }))];
const byName = Object.fromEntries(docs.map((d) => [d.name, d.id]));

const SOURCE_REF = /^((?:src|app|lib|electron|server|shared|packages|components|pages|docs|scripts)\/[\w./@\-[\]]+\.\w+):(\d+)(?:-(\d+))?/;
const sections = [];
const toc = [];
for (const doc of docs) {
  const md = readFileSync(doc.file, "utf8");
  const seen = new Map();
  const heads = [];
  const renderer = new marked.Renderer();
  renderer.heading = function ({ tokens, depth, text }) {
    const inner = this.parser.parseInline(tokens);
    let s = slug(text.replace(/`/g, ""));
    const n = seen.get(s) ?? 0;
    seen.set(s, n + 1);
    if (n) s = `${s}-${n}`;
    if (depth <= 3) heads.push({ depth, id: `${doc.id}--${s}`, text: inner.replace(/<[^>]+>/g, "") });
    return `<h${depth} id="${doc.id}--${s}">${inner}</h${depth}>\n`;
  };
  renderer.link = function ({ href, title, tokens }) {
    const inner = this.parser.parseInline(tokens);
    let target = href;
    const local = href.match(/^(?:parts\/)?([\w-]+\.md)(#.*)?$/);
    const source = href.match(/^(?:\.\.\/)+([^#]+)(#L\d+)?$/);
    if (local && byName[local[1]] !== undefined) target = local[2] ? `#${byName[local[1]]}--${local[2].slice(1)}` : `#${byName[local[1]]}`;
    else if (source && blob) target = `${blob}/${source[1]}${source[2] ?? ""}`;
    const external = /^https?:/.test(target);
    return `<a href="${esc(target)}"${title ? ` title="${esc(title)}"` : ""}${external ? ' target="_blank" rel="noopener"' : ""}>${inner}</a>`;
  };
  renderer.html = ({ text }) => esc(text);
  renderer.codespan = ({ text }) => {
    const raw = text.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, "\"").replace(/&#39;/g, "'");
    const m = raw.match(SOURCE_REF);
    if (!m || !blob) return `<code>${esc(raw)}</code>`;
    const range = m[3] ? `#L${m[2]}-L${m[3]}` : `#L${m[2]}`;
    return `<a class="src" href="${blob}/${m[1]}${range}" target="_blank" rel="noopener"><code>${esc(raw)}</code></a>`;
  };
  const h1 = md.match(/^#\s+(.+)$/m)?.[1].replace(/[`*_]/g, "").trim() ?? doc.name;
  const label = doc.id === "readme" ? "Tổng quan" : h1.length > 30 ? `${h1.slice(0, 29)}…` : h1;
  sections.push(`<section id="${doc.id}" class="doc">${marked.parse(md, { renderer, gfm: true })}</section>`);
  toc.push({ id: doc.id, label, code: doc.id === "readme" ? "D-00" : doc.name.replace(/\.md$/, "").replace(/^_/, "").toUpperCase(), heads, items: lastJson(md) });
}

const names = {};
const catalogueFile = partFiles.find((f) => f === "_catalogue.md");
if (catalogueFile) {
  for (const line of readFileSync(join(partsDir, catalogueFile), "utf8").split("\n")) {
    const m = line.match(/^(\d+)\. `([^`]+)` — \*\*(.+?)\*\*/);
    if (m) names[m[1]] = { slug: m[2], name: m[3] };
  }
}
const status = {};
for (const t of toc) for (const r of t.items) if (typeof r?.n === "number") status[r.n] = r.status;

const demoFiles = existsSync(demoDir) ? readdirSync(demoDir).filter((f) => f.endsWith(".html")) : [];
const fragment = (file) => readFileSync(join(demoDir, file), "utf8").replace(/<script[\s\S]*?<\/script>/gi, "").trim();
const cssFile = args.css ?? (() => {
  const dir = join(repo, ".demo-build/out/assets");
  const f = existsSync(dir) && readdirSync(dir).find((n) => n.endsWith(".css"));
  return f ? join(dir, f) : null;
})();
const dropFonts = (args["drop-fonts"] ?? "").split(",").map((f) => f.trim()).filter(Boolean);
const appCss = cssFile && existsSync(cssFile)
  ? readFileSync(cssFile, "utf8").replace(/<\/style/gi, "<\\/style").replace(/@font-face\{[^}]*\}/g, (face) => (dropFonts.some((f) => face.includes(f)) ? "" : face))
  : "";

const BADGE = { yes: '<span class="st yes">Có</span>', partial: '<span class="st partial">Một phần</span>', no: '<span class="st no">Không có</span>' };
const srcHref = (s) => {
  const m = s.match(/^([^\s,:;]+):(\d+)/);
  return m ? `${demoBlob}/${m[1]}#L${m[2]}` : `${demoBlob}/${s.split(/[\s,:;]/)[0]}`;
};
const frame = (skin, html) => `<div class="demo-frame"${skin ? ` data-skin="${esc(skin)}"` : ""}>${html}</div>`;
const card = (title, badge, file, anchor) => {
  const html = fragment(file);
  const src = html.match(/data-source="([^"]+)"/)?.[1];
  const proposal = /data-proposal="true"/.test(html) ? '<span class="st prop">Đề xuất</span>' : "";
  const source = src && demoBlob ? `<a class="demo-src" href="${esc(srcHref(src))}" target="_blank" rel="noopener">${esc(src.split(/[\s,;]/)[0])}</a>` : "";
  const more = anchor ? `<a class="demo-more" href="#${anchor}">Chi tiết</a>` : "";
  const body = ab
    ? `<div class="ab"><div class="ab-side" data-side="a"><span class="ab-tag">A · Cũ · <i data-old-name>${esc(nameOf(oldSkins[0]))}</i></span>${frame(oldSkins[0], html)}</div><div class="ab-side" data-side="b"><span class="ab-tag">B · Mới · ${esc(nameOf(newSkin))}</span>${frame(newSkin, "")}</div><input class="ab-range" type="range" min="0" max="100" value="50" aria-label="Vị trí so sánh A/B"></div>`
    : frame(newSkin || oldSkins[0], html);
  return `<figure class="demo-card"><figcaption><b>${title}</b>${badge}${proposal}${source}${more}</figcaption>${body}</figure>`;
};

const numbered = (n) => demoFiles.find((f) => f.startsWith(`${n}-`));
const headingOf = {};
for (const [i, t] of toc.entries()) {
  if (!t.items.some((r) => typeof r?.n === "number")) continue;
  const pattern = new RegExp(`<h3 id="(${t.id}--(\\d+)-[^"]*)">[\\s\\S]*?<\\/h3>`, "g");
  sections[i] = sections[i].replace(pattern, (h3, hid, n) => {
    headingOf[n] = hid;
    const file = numbered(n);
    return file ? `${h3}${card(`#${n} · ${esc(names[n]?.name ?? "")}`, BADGE[status[n]] ?? "", file)}` : h3;
  });
}

const galleryHeads = [];
const block = (hid, title, cards) => {
  if (!cards.length) return "";
  galleryHeads.push({ depth: 3, id: `gallery--${hid}`, text: title });
  return `<h3 id="gallery--${hid}">${esc(title)}</h3><div class="gallery-grid">${cards.join("")}</div>`;
};
const numberedIds = Object.keys(names).map(Number).filter((n) => numbered(n)).sort((a, b) => a - b);
const families = [...new Set(numberedIds.map((n) => names[n].slug.split("/")[0]))];
const catalogueBlocks = families.map((fam) => {
  const ns = numberedIds.filter((n) => names[n].slug.startsWith(`${fam}/`));
  return block(`cat-${slug(fam)}`, `${titleCase(fam)} · ${ns[0]}–${ns.at(-1)}`, ns.map((n) => card(`#${n} · ${esc(names[n].name)}`, BADGE[status[n]] ?? "", numbered(n), headingOf[n])));
}).join("");
const kebab = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const extras = demoFiles.filter((f) => f.startsWith("x-"));
const groupsFile = join(docsDir, "canon.json");
const groups = existsSync(groupsFile) ? JSON.parse(readFileSync(groupsFile, "utf8")) : { "Thành phần riêng": Object.fromEntries(extras.map((f) => [titleCase(f.slice(2, -5)), []])) };
const placed = new Set();
const extraBlocks = Object.entries(groups).map(([group, entries], gi) => block(`x${gi}`, group, Object.keys(entries).filter((k) => extras.includes(`x-${kebab(k)}.html`)).map((k) => {
  placed.add(`x-${kebab(k)}.html`);
  return card(esc(k), "", `x-${kebab(k)}.html`);
}))).join("") + block("x-rest", "Khác", extras.filter((f) => !placed.has(f)).map((f) => card(esc(titleCase(f.slice(2, -5))), "", f)));
const demoCount = numberedIds.length + extras.length;
if (demoCount) {
  const lead = `${numberedIds.length} thành phần trong danh mục và ${extras.length} thành phần riêng, dựng bằng đúng class và token của app.${ab ? ` Mỗi thẻ hiện A (cũ: ${oldSkins.map(nameOf).join(" / ")}) cạnh B (mới: ${nameOf(newSkin)}).` : ""}`;
  sections.splice(1, 0, `<section id="gallery" class="doc"><h1 id="gallery--top">Gallery</h1><p class="lead">${esc(lead)}</p>${numberedIds.length ? `<h2 id="gallery--catalogue">Thành phần trong danh mục</h2>${catalogueBlocks}` : ""}${extras.length ? `<h2 id="gallery--extras">Thành phần riêng</h2>${extraBlocks}` : ""}</section>`);
  toc.splice(1, 0, { id: "gallery", label: "Gallery", code: `UI-${demoCount}`, heads: galleryHeads, items: [] });
}

const fontFaces = (() => {
  const dir = args.font ? resolve(args.font) : join(repo, "node_modules/@fontsource-variable/lexend-deca");
  const css = join(dir, "index.css");
  if (!existsSync(css)) return { faces: "", family: "system-ui" };
  const source = readFileSync(css, "utf8");
  const family = source.match(/font-family:\s*'([^']+)'/)?.[1] ?? "system-ui";
  const faces = [...source.matchAll(/@font-face\s*\{[^}]*\}/g)].map((m) => m[0]).filter((f) => /latin|vietnamese/.test(f) && !/cyrillic|greek/.test(f))
    .map((f) => f.replace(/url\(\.\/files\/([^)]+)\)\s*format\('woff2-variations'\)|url\(\.\/files\/([^)]+)\)/g, (_, a, b) => `url(data:font/woff2;base64,${readFileSync(join(dir, "files", a ?? b)).toString("base64")})`)).join("\n");
  return { faces, family };
})();

const subheads = ({ id, heads }) => heads.filter((h) => (id === "readme" ? h.depth === 2 : h.depth === 3 || (!heads.some((x) => x.depth === 3) && h.depth === 2)));
const tabs = toc.map((t) => `<button type="button" role="tab" id="tab-${t.id}" aria-controls="${t.id}" aria-selected="false" data-tab="${t.id}"><span>${esc(t.label)}</span><small>${esc(t.code)}</small></button>`).join("");
const panels = sections.map((html, i) => {
  const links = subheads(toc[i]).map((h) => `<a href="#${h.id}">${esc(h.text)}</a>`).join("");
  return html.replace(/^<section id="([^"]+)" class="doc">/, `<section id="$1" class="doc" role="tabpanel" aria-labelledby="tab-$1" hidden>${links ? `<nav class="jump" aria-label="Trong mục này">${links}</nav>` : ""}`);
}).join("\n");
const compareBar = ab ? `<div class="seg" role="group" aria-label="Bản cũ (A)"><span>A · cũ</span>${oldSkins.map((s, i) => `<button type="button" data-old="${esc(s)}" aria-pressed="${i === 0}">${esc(nameOf(s))}</button>`).join("")}</div><div class="seg" role="group" aria-label="Cách so sánh"><span>So sánh</span><button type="button" data-ab="split" aria-pressed="true">A | B</button><button type="button" data-ab="slider" aria-pressed="false">Trượt</button><button type="button" data-ab="a" aria-pressed="false">Chỉ A</button><button type="button" data-ab="b" aria-pressed="false">Chỉ B</button></div>` : "";
const page = readFileSync(new URL("../assets/page.html", import.meta.url), "utf8")
  .replace("{{APP_CSS}}", () => appCss)
  .replace("{{FONT_FACES}}", () => fontFaces.faces)
  .replace("{{FONT_FAMILY}}", () => JSON.stringify(fontFaces.family))
  .replace("{{TITLE}}", () => esc(`${brand} · UI Inventory`))
  .replace("{{MARK}}", () => esc(mark))
  .replace("{{BRAND}}", () => esc(brand))
  .replace("{{SUBTITLE}}", () => esc(args.subtitle ?? "UI Inventory"))
  .replace("{{COMPARE}}", () => compareBar)
  .replace("{{STATUS}}", () => esc(`${Object.keys(status).length} mục danh mục · ${extras.length} thành phần riêng`))
  .replace("{{TABS}}", () => tabs)
  .replace("{{PANELS}}", () => panels)
  .replace("{{OLD_NAMES}}", () => JSON.stringify(Object.fromEntries(oldSkins.map((s) => [s, nameOf(s)]))));
writeFileSync(out, page);
console.log(`${out}: ${toc.length} tabs, ${demoCount} demos, ${ab ? `A/B ${oldSkins.join("/")} vs ${newSkin}` : "no A/B"}, ${page.length} bytes`);
