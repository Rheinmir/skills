#!/usr/bin/env node
// make-agent-uiux-map: build ONE self-contained HTML file from an inventory folder. A Name That UI style gallery of every
// component (live previews in the site's own CSS), a detail page each with real code samples, and an ontology an
// agent reads to map any design onto these components (embedded as JSON: script#ui-ontology).
//
//   node build-gallery.mjs <inventory-dir> [--out dir | file.html]   → <product>-uiux-map.html (never index.html)
//
// <inventory-dir>
//   meta.json          { product, wordmark, title, lede, css, fontsDir, fontKeep, skins, defaultSkin, houseFont, frames, ownLabel }
//   site.css           the site's compiled CSS (meta.css overrides the name); woff2 url()s are inlined from fontsDir
//   catalogue.md       optional; defaults to ../references/catalogue.md (the 91 Name That UI components)
//   parts/*.md         one "### " section per component (see ../references/report-template.md)
//   demos/N-slug.html  a catalogue component's demo (N = its catalogue number)
//   demos/x-slug.html  one of the site's own components
//   README.md          optional: a "| **Name** | count | `Comp` [`file:line`] | report | raw names |" table under "### Group"
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const inv = resolve(args.find((a) => !a.startsWith("--")) ?? ".");
const outArg = args.includes("--out") ? args[args.indexOf("--out") + 1] : null;
let out = null; // named once meta.product is known: <product>-uiux-map.html, never index.html (this is a file, not a site)
const at = (...p) => join(inv, ...p);
const readIf = (p) => (existsSync(p) ? readFileSync(p, "utf8") : "");
if (!existsSync(at("demos"))) { console.error(`no demos/ in ${inv}: see SKILL.md, step 3`); process.exit(1); }

const meta = {
  product: "Site", wordmark: null, title: "Thành phần này tên là gì", lede: null, css: "site.css", fontsDir: null,
  fontKeep: "(latin|latin-ext|vietnamese)", skins: [], skinAttr: "data-skin", defaultSkin: null, stageBg: "var(--color-app)", houseFont: null, frames: null, ownLabel: "Riêng app",
  ...JSON.parse(readIf(at("meta.json")) || "{}"),
};
meta.wordmark ??= `${meta.product.split(/\s+/)[0]}.`;
{
  const fileName = `${meta.product.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/g, "d").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "site"}-uiux-map.html`;
  const target = outArg ? resolve(outArg) : inv;
  const isDir = !/\.html?$/i.test(target);
  out = isDir ? join(target, fileName) : target;
  if (/(^|\/)index\.html?$/i.test(out)) { console.warn(`index.html is a site's name; this is one file: writing ${fileName} instead`); out = join(dirname(out), fileName); }
}
meta.lede ??= `Thư viện trực quan của giao diện ${meta.product}. Mô tả thứ bạn thấy bằng lời thường, nhận lại tên chuẩn, nơi định nghĩa, code mẫu và một prompt dán sẵn cho agent.`;

// ── reports ────────────────────────────────────────────────────────────────────────────────────────────────────
const sections = [];
for (const f of existsSync(at("parts")) ? readdirSync(at("parts")).filter((f) => f.endsWith(".md") && !f.startsWith("_")) : []) {
  let cur = null;
  for (const line of readFileSync(at("parts", f), "utf8").split("\n")) {
    if (line.startsWith("### ")) { cur = { file: f, heading: line.slice(4).trim(), body: [] }; sections.push(cur); continue; }
    if (line.startsWith("## ")) { cur = null; continue; }
    cur?.body.push(line);
  }
}
/** "- **Field:** value" or "- Field: value" bullets; indented sub-bullets fold into the field above. */
function fields(body) {
  const found = {};
  let key = null;
  for (const line of body) {
    const m = /^- (?:\*\*)?([^:*]{2,40}?)(?:\*\*)?:(?:\*\*)?\s*(.*)$/.exec(line);
    if (m) { key = m[1].trim(); found[key] = m[2].trim(); continue; }
    if (key && /^\s+- /.test(line)) found[key] += "\n" + line.trim().slice(2);
    else if (!line.trim() || line.startsWith("`") || line.startsWith("```")) key = null;
  }
  return found;
}
/** Code samples: a line ending in `path:range`, then a fenced block (which may be indented under its bullet). */
function samples(body) {
  const list = [];
  for (let i = 0; i < body.length; i++) {
    const ref = /`([^`\s]+:\d+(?:-\d+)?)`\s*:?\s*$/.exec(body[i].trim());
    if (!ref) continue;
    let j = i + 1;
    while (j < body.length && !body[j].trim()) j++;
    const fence = /^(\s*)```(\w*)/.exec(body[j] ?? "");
    if (!fence) continue;
    const indent = fence[1].length, code = [];
    for (j += 1; j < body.length && !/^\s*```\s*$/.test(body[j]); j++) code.push(body[j].slice(Math.min(indent, body[j].length - body[j].trimStart().length)));
    list.push({ path: ref[1], lang: fence[2] || "html", code: code.join("\n") });
    i = j;
  }
  return list;
}
const pick = (f, ...keys) => keys.map((k) => f[k]).find(Boolean) ?? "";

// ── catalogue and the optional README table of the site's own components ──────────────────────────────────────
const catalogue = new Map();
for (const line of (readIf(at("catalogue.md")) || readIf(join(here, "../references/catalogue.md"))).split("\n")) {
  const m = /^(\d+)\. `([^`]+)` — \*\*(.+?)\*\* — (.+)$/.exec(line);
  if (m) catalogue.set(Number(m[1]), { slug: m[2], name: m[3], line: m[4] });
}
const slug = (s) => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const table = new Map();
{
  let group = "";
  for (const line of readIf(at("README.md")).split("\n")) {
    if (line.startsWith("### ")) group = line.slice(4).trim();
    const m = /^\| \*\*(.+?)\*\* \| (\d+) \| (.*?) \| (.*?) \| (.*?) \|$/.exec(line);
    if (!m) continue;
    const defs = [...m[3].matchAll(/`([^`]+)` \[`([^`]+)`\]/g)].map(([, name, path]) => ({ name, path }));
    table.set(slug(m[1]), { group, name: m[1], count: Number(m[2]), defs, raw: m[5].split(/[;,]\s*/).map((s) => s.trim()).filter(Boolean) });
  }
}
// The mark decides (✅ 🟡 ❌); words only when there is no mark, so "✅ Có … (không có X)" stays full.
const statusOf = (s = "") => s.includes("✅") ? "full" : s.includes("🟡") ? "partial" : s.includes("❌") ? "none"
  : /partial|một phần/i.test(s) ? "partial" : /\bnone\b|^\s*(không có|chưa có)/i.test(s) ? "none" : "full";
const firstSentence = (s) => { const t = s.replace(/`/g, "").trim(); if (t.length <= 180) return t; const m = /^(.+?[.!?])(\s|$)/.exec(t); return (m ? m[1] : t).trim(); };

const items = [];
for (const file of readdirSync(at("demos")).filter((f) => f.endsWith(".html")).sort((a, b) => a.localeCompare(b, "en", { numeric: true }))) {
  const html = readFileSync(at("demos", file), "utf8").trim();
  const source = /data-source="([^"]+)"/.exec(html)?.[1] ?? "";
  const id = file.slice(0, -5);
  const n = Number(/^(\d+)-/.exec(id)?.[1]);
  if (!id.startsWith("x-") && catalogue.has(n)) {
    const cat = catalogue.get(n);
    const section = sections.find((s) => new RegExp(`^${n}\\. `).test(s.heading));
    const f = section ? fields(section.body) : {};
    items.push({
      id, kind: "catalogue", number: n, group: cat.slug.startsWith("macos/") ? "macOS" : "Web", name: cat.name, slug: cat.slug,
      status: statusOf(f["Trạng thái"] ?? f["Status"]), statusText: pick(f, "Trạng thái", "Status"),
      // the card and the detail page read the site's own description when the report has one; the ontology's cue stays
      // the catalogue's recognition sentence (catLine), which is what mapping matches on
      line: firstSentence(pick(f, "Mô tả", "Description")) || cat.line, description: pick(f, "Mô tả", "Description") || cat.line, catLine: cat.line,
      omb: pick(f, "Tên trong code", "Tên trong OMB", "Implemented by"), definitions: pick(f, "Định nghĩa", "Defined at"), usage: pick(f, "Nơi dùng", "Used"),
      variants: pick(f, "Biến thể", "Variants"), notes: pick(f, "Ghi chú refactor", "Notes"), aliases: (pick(f, "Tên gọi khác", "Aliases")).split(/[;,]\s*/).filter(Boolean),
      samples: section ? samples(section.body) : [], source, html,
    });
    continue;
  }
  const key = id.replace(/^x-/, "");
  const row = table.get(key);
  const names = [row?.name, ...(row?.raw ?? [])].filter(Boolean);
  const section = sections.find((s) => names.includes(s.heading)) ?? sections.find((s) => slug(s.heading) === key)
    ?? sections.find((s) => names.some((nm) => s.heading.toLowerCase() === nm.toLowerCase()));
  const f = section ? fields(section.body) : {};
  const description = pick(f, "Mô tả", "Description");
  items.push({
    id, kind: "outside", group: pick(f, "Nhóm", "Group") || row?.group || "Khác", name: row?.name ?? section?.heading ?? key,
    status: statusOf(pick(f, "Trạng thái", "Status")), statusText: "", line: firstSentence(description), description,
    variants: pick(f, "Biến thể", "Variants"),
    definitions: pick(f, "Định nghĩa", "Defined at") || (row?.defs ?? []).map((d) => `\`${d.name}\` \`${d.path}\``).join(", "),
    omb: pick(f, "Tên trong code", "Implemented by") || (row?.defs ?? []).map((d) => d.name).slice(0, 4).join(", "),
    aliases: [...(row?.raw ?? []).filter((r) => r !== row?.name), ...pick(f, "Tên gọi khác", "Aliases").split(/[;,]\s*/).filter(Boolean)],
    notes: pick(f, "Ghi chú refactor", "Notes"), usage: pick(f, "Nơi dùng", "Used") || (row ? `${row.count} component` : ""),
    samples: section ? samples(section.body) : [], source, html,
  });
}

// ── the site's CSS, its fonts inlined ──────────────────────────────────────────────────────────────────────────
// meta.css may carry one "*" in its file name (a build's hashed CSS, e.g. dist/assets/styles-*.css).
const cssPath = (() => {
  const p = at(meta.css);
  if (!p.includes("*")) return p;
  const d = dirname(p), re = new RegExp(`^${p.slice(d.length + 1).split("*").map((s) => s.replace(/[.+?^${}()|[\]\\]/g, "\\$&")).join(".*")}$`);
  const hit = existsSync(d) && readdirSync(d).find((f) => re.test(f));
  return hit ? join(d, hit) : p;
})();
let siteCss = readIf(cssPath);
if (!siteCss) console.warn(`warning: no ${meta.css} in ${inv}; previews will be unstyled`);
const fontsDir = meta.fontsDir ? at(meta.fontsDir) : dirname(cssPath);
const keep = new RegExp(meta.fontKeep);
// Every font file the @font-face rules point at (woff2, woff, ttf, otf; by name or path in fontsDir) is inlined. A face
// whose file name names a subset (…-cyrillic-…) outside meta.fontKeep is dropped to keep the page light.
const MIME = { woff2: "font/woff2", woff: "font/woff", ttf: "font/ttf", otf: "font/otf" };
const fontFile = (url) => {
  const name = url.split(/[?#]/)[0].split("/").filter(Boolean).pop() ?? "";
  const file = [join(fontsDir, name), join(fontsDir, url.split(/[?#]/)[0].replace(/^\/+/, ""))].find((p) => name && existsSync(p));
  const ext = /\.(woff2|woff|ttf|otf)$/i.exec(name)?.[1]?.toLowerCase();
  return file && ext ? { name, file, ext } : null;
};
siteCss = siteCss.replace(/@font-face\s*\{[^}]*\}/g, (face) => {
  const urls = [...face.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g)].map((m) => m[1]).filter((u) => !u.startsWith("data:"));
  const found = urls.map(fontFile).filter(Boolean);
  if (!found.length) return face;
  if (found.some((f) => /-(latin|latin-ext|vietnamese|cyrillic|cyrillic-ext|greek|greek-ext|symbols\w*)-/.test(f.name) && !keep.test(f.name))) return "";
  return face.replace(/url\(\s*["']?([^"')]+)["']?\s*\)/g, (m, u) => {
    const f = fontFile(u);
    return f ? `url(data:${MIME[f.ext]};base64,${readFileSync(f.file).toString("base64")})` : m;
  });
});

// The site's CSS goes into its own cascade layer, so the gallery's chrome (unlayered) always wins over it whatever the
// specificity, while previews keep every site rule. A bundle of many pages' CSS often carries page rules on bare
// elements (body { max-width: 720px }) that would otherwise squeeze the gallery. @charset/@import cannot sit in a layer.
const hoisted = [];
siteCss = siteCss.replace(/@charset[^;]*;/g, "").replace(/@import[^;]*;/g, (m) => { hoisted.push(m); return ""; });
const layeredCss = `${hoisted.join("\n")}\n@layer site {\n${siteCss}\n}`;

// ── ontology ───────────────────────────────────────────────────────────────────────────────────────────────────
const plain = (s) => String(s ?? "").replace(/\*\*|`/g, "").replace(/\[([^\]]+)\]\([^)]*\)/g, "$1").split("\n")[0].trim();
const files = (s) => [...new Set([...String(s ?? "").matchAll(/`?([\w@.-]+(?:\/[\w@.-]+)+\.\w{1,5})(?::(\d+))?/g)].map((m) => (m[2] ? `${m[1]}:${m[2]}` : m[1])))].slice(0, 6);
const groups = [...new Set(items.map((i) => i.group))];
const ontology = {
  name: `${meta.product} UI ontology`,
  version: "1",
  classes: {
    Group: `Một họ thành phần cùng mục đích: macOS, Web, hoặc một nhóm riêng của ${meta.product}.`,
    Component: "Một phần giao diện có tên chuẩn. Map một vùng của thiết kế vào đây khi dấu hiệu nhận diện hoặc một tên gọi khác khớp.",
  },
  properties: {
    cue: "Trông thế nào và làm gì: vùng nào khớp mô tả này thì map vào thành phần này.",
    aliases: "Những tên khác người ta dùng cho cùng một thứ.",
    implementedBy: `Component, class hoặc rule CSS của ${meta.product} đã vẽ ra nó: dùng lại, đừng viết mới.`,
    definedAt: "Tệp nguồn (tệp:dòng) hoặc selector cần đọc trước khi dựng.",
    status: "full: có đủ · partial: có hành vi nhưng chưa đúng dạng chuẩn · none: chưa dựng.",
    hasSample: "Có code mẫu thật trong file này (trang chi tiết, mục \"Trong code\").",
  },
  mappingRules: [
    "Cắt thiết kế thành từng vùng theo vai trò: điều hướng, nhập liệu, phản hồi, khung chứa, nội dung, lớp phủ.",
    "Với mỗi vùng, so với cue và aliases của mọi thành phần; chọn thành phần khớp cụ thể nhất.",
    "Ưu tiên thành phần có status full; partial thì đọc ghi chú refactor trước; none thì dựng mới theo cue bằng token của trang.",
    "Dùng lại implementedBy và chép code mẫu; không viết bản thứ hai cho thứ đã có.",
    `Giữ token và class của trang${meta.houseFont ? `, cùng chữ chuẩn ${meta.houseFont}` : ""}; đối chiếu với bản xem trước.`,
    "Vùng không khớp thành phần nào là thành phần mới: đặt tên chuẩn, viết cue, xếp vào một nhóm.",
  ],
  groups: groups.map((g) => ({ name: g, components: items.filter((i) => i.group === g).map((i) => i.id) })),
  components: items.map((i) => ({
    id: i.id, name: i.name, group: i.group, kind: i.kind, slug: i.slug || undefined,
    cue: plain(i.kind === "catalogue" ? i.catLine : i.description), aliases: i.aliases?.length ? i.aliases : undefined,
    implementedBy: plain(i.omb) || undefined, definedAt: files(i.definitions || i.source), status: i.status, hasSample: i.samples.length > 0,
  })),
};
for (const i of items) i.cue = ontology.components.find((c) => c.id === i.id).cue;

// ── layouts: try the map's own components in common page layouts ──────────────────────────────────────────────
// Each slot takes the best match: keyword hits in the name weigh 3, in code names or cue 1; status full first; a
// component is used once per layout. No match → a wireframe block. The inventory may carry its own layouts.json.
const layoutSpec = JSON.parse(readIf(at("layouts.json")) || readIf(join(here, "../references/layouts.json")) || '{"layouts":[]}');
const hay = new Map(items.map((i) => [i.id, { name: i.name.toLowerCase(), rest: `${plain(i.omb)} ${i.cue} ${(i.aliases ?? []).join(" ")}`.toLowerCase() }]));
const layouts = layoutSpec.layouts.map((l) => {
  const used = new Set();
  const slots = Object.fromEntries(Object.entries(l.slots).map(([area, slot]) => {
    if (slot.wire || !slot.want?.length) return [area, { wire: slot.wire ?? "block", key: !!slot.key }];
    let best = null, bestScore = 0;
    for (const i of items) {
      if (used.has(i.id)) continue;
      const h = hay.get(i.id);
      let score = 0;
      slot.want.forEach((w, rank) => { const k = w.toLowerCase(); const weight = (slot.want.length - rank) / slot.want.length; if (h.name.includes(k)) score += 3 * weight; else if (h.rest.includes(k)) score += weight; });
      if (score > 0 && i.status === "full") score += 0.25;
      if (score > bestScore) { best = i; bestScore = score; }
    }
    if (best) used.add(best.id);
    return [area, best ? { id: best.id, key: !!slot.key } : { wire: "block", key: !!slot.key }];
  }));
  return { id: l.id, name: l.name, cue: l.cue, columns: l.columns, rows: l.rows, areas: l.areas, overlay: l.overlay ?? null, slots };
});
ontology.layouts = layouts.map((l) => ({ id: l.id, name: l.name, cue: l.cue,
  slots: Object.fromEntries(Object.entries(l.slots).map(([a, s]) => [a, s.id ?? `(${s.wire})`])) }));

// ── page ───────────────────────────────────────────────────────────────────────────────────────────────────────
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
const json = (v) => JSON.stringify(v).replace(/</g, "\\u003c");
const counts = { all: items.length, catalogue: items.filter((i) => i.kind === "catalogue").length, outside: items.filter((i) => i.kind === "outside").length };
const has = (id) => items.some((i) => i.id === id);
const frame = (f, phone) => {
  const ids = (f?.ids ?? []).filter(has);
  if (!ids.length) return "";
  const screen = `<div class="g-screen" data-ids="${esc(ids.join(","))}"></div>`;
  return phone
    ? `<figure class="g-frame"><div class="g-phone">${screen}</div><figcaption data-cap="${esc(f.cap ?? "Điện thoại 390 × 844")}"></figcaption></figure>`
    : `<figure class="g-frame"><div class="g-win"><div class="g-win-bar"><i></i><i></i><i></i><span>${esc(f.url ?? meta.product)}</span></div>${screen}</div><figcaption data-cap="${esc(f.cap ?? "Desktop 1440 × 900 (thu nhỏ)")}"></figcaption></figure>`;
};
const phones = (meta.frames?.phones ?? []).map((f) => frame(f, true)).filter(Boolean).join("");
const frames = meta.frames ? `<section class="g-frames" aria-label="Khung mẫu">${frame(meta.frames.desktop, false)}${phones ? `<div class="g-phones">${phones}</div>` : ""}</section>` : "";
const ICON = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  graph: '<circle cx="12" cy="5" r="2.5"/><circle cx="5" cy="19" r="2.5"/><circle cx="19" cy="19" r="2.5"/><path d="M12 7.5v4M12 11.5 6.5 17M12 11.5l5.5 5.5"/>',
  flow: '<rect x="3" y="4" width="6" height="5" rx="1.2"/><rect x="15" y="15" width="6" height="5" rx="1.2"/><path d="M9 6.5h4a2 2 0 0 1 2 2v6.5"/>',
  find: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  skin: '<path d="M12 3a9 9 0 1 0 0 18c1.1 0 1.6-.9 1.2-1.8-.5-1-.1-2.2 1.1-2.2H17a4 4 0 0 0 4-4c0-5.5-4-10-9-10Z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7" r="1"/><circle cx="15" cy="7.5" r="1"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/>',
  layout: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M9 9v11"/>',
};
const svg = (k) => `<svg viewBox="0 0 24 24" aria-hidden="true">${ICON[k]}</svg>`;
const page = `<!doctype html>
<html lang="vi"${meta.defaultSkin ? ` ${esc(meta.skinAttr)}="${esc(meta.defaultSkin)}"` : ""} data-g-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(meta.product)} UIUX Map</title>
<meta name="description" content="${counts.all} thành phần giao diện của ${esc(meta.product)}: bản xem trước thật, tên chuẩn, code mẫu, ontology cho agent.">
<style>${layeredCss}</style>
<style>${readFileSync(join(here, "gallery.css"), "utf8")}</style>
<style>:root { --g-stage-site: ${meta.stageBg}; }</style>
</head>
<body class="g">
<header class="g-top">
  <div class="g-bar">
    <a class="g-logo" href="#/">${esc(meta.wordmark)}</a>
    <nav class="g-nav" aria-label="Mục">
      <a href="#/" data-nav="list">${svg("grid")}Thành phần</a>
      <a href="#/ontology" data-nav="ontology">${svg("graph")}Ontology</a>
      <a href="#/layouts" data-nav="layouts">${svg("layout")}Layout</a>
    </nav>
    <div class="g-tools">
      <button class="g-tool" id="find" type="button">${svg("find")}Tìm kiếm</button>
      <label class="g-tool g-pill">${svg("skin")}Skin<select id="skin" aria-label="Skin của bản xem trước"></select></label>
      <button class="g-tool g-outline" id="theme" type="button">${svg("moon")}<span id="theme-label">Nền tối</span></button>
    </div>
  </div>
</header>
<div class="g-sheet">
<section class="g-hero" id="hero">
  <h1 class="g-display">${esc(meta.title)}<em>?</em></h1>
  <p class="g-hero-lede">${esc(meta.lede)}</p>
  <label class="g-bigsearch">${svg("find")}<input id="q" type="search" placeholder="«menu bật ra khi bấm chuột phải»" aria-label="Tìm thành phần" autocomplete="off"><kbd>⌘K</kbd></label>
  <p class="g-hint">Không gọi được tên? <a href="#/ontology">Xem ontology</a> để biết khi nào map vào thành phần nào.</p>
  <p class="g-hint g-hint2">Gõ tên, tên trong code hoặc hình dạng; kết quả lọc ngay khi gõ.</p>
</section>
${frames}
<main class="g-main">
  <section id="list">
    <div id="grid-top" class="g-scopes" role="tablist" aria-label="Phạm vi">
      <a href="#/" data-scope="all">Tất cả <i>${counts.all}</i></a>
      <a href="#/catalogue" data-scope="catalogue">Danh mục <i>${counts.catalogue}</i></a>
      <a href="#/outside" data-scope="outside">${esc(meta.ownLabel)} <i>${counts.outside}</i></a>
    </div>
    <div class="g-filters" id="groups" role="group" aria-label="Nhóm"></div>
    <div class="g-filters" id="statuses" role="group" aria-label="Trạng thái"></div>
    <p class="g-count" id="count" aria-live="polite"></p>
    <div class="g-grid" id="grid"></div>
  </section>
  <section id="ontology" hidden></section>
  <section id="layouts" hidden></section>
  <section id="detail" hidden></section>
</main>
</div>
<script id="ui-ontology" type="application/ld+json">${JSON.stringify(ontology, null, 1).replace(/</g, "\\u003c")}</script>
<script id="g-data" type="application/json">${json({ items, layouts, skins: meta.skins, meta: { product: meta.product, houseFont: meta.houseFont, defaultSkin: meta.defaultSkin, skinAttr: meta.skinAttr } })}</script>
<script>${readFileSync(join(here, "gallery.js"), "utf8")}</script>
</body>
</html>
`;
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, page);
const noDesc = items.filter((i) => !i.description).map((i) => i.id);
console.log(`${items.length} components (${counts.catalogue} catalogue, ${counts.outside} own), ${(page.length / 1e6).toFixed(1)} MB`);
console.log(`with code samples: ${items.filter((i) => i.samples.length).length}; without a description: ${noDesc.length}${noDesc.length ? " " + noDesc.slice(0, 8).join(", ") : ""}`);
// No server: the file is self-contained. Hand over its path, ready to open.
console.log(`\nHTML: ${out}\nURL:  ${pathToFileURL(out).href}\nOpen: open "${out}"`);
