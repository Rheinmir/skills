#!/usr/bin/env node
// make-agent-uiux-map step 1: capture a live site into an inventory folder.
//
//   node capture.mjs <url> <inventory-dir> [--pages 12] [--width 1440]
//
// Writes into <inventory-dir>:
//   site.css          every stylesheet the pages load (same-origin rules, fetched cross-origin sheets, inline <style>),
//                     url()s made absolute; woff2 fonts downloaded into fonts/ and pointed at by file name
//   capture/N.png     a full-page screenshot of each visited page, capture/N.html its rendered DOM
//   candidates.json   regions worth naming, per page: role, a unique selector, tag, classes, size, a text hint
//   meta.json         a starting point (product from <title>); edit it, it is never overwritten
// Visits the start page and same-origin links breadth-first, up to --pages.
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { playwright } from "./pw.mjs";

const args = process.argv.slice(2);
const [start, dirArg] = args.filter((a) => !a.startsWith("--") && !/^\d+$/.test(a));
if (!start || !dirArg) { console.error("usage: node capture.mjs <url> <inventory-dir> [--pages 12] [--width 1440]"); process.exit(1); }
const opt = (k, d) => (args.includes(k) ? Number(args[args.indexOf(k) + 1]) : d);
const dir = resolve(dirArg), maxPages = opt("--pages", 12), width = opt("--width", 1440);
for (const d of ["capture", "fonts"]) mkdirSync(join(dir, d), { recursive: true });

const { chromium } = await playwright();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height: 900 } });
const origin = new URL(start).origin;
const queue = [start], seen = new Set(), sheets = new Map(), candidates = [];
let title = "";

while (queue.length && seen.size < maxPages) {
  const url = queue.shift().split("#")[0];
  if (seen.has(url)) continue;
  seen.add(url);
  const n = seen.size;
  try { await page.goto(url, { waitUntil: "networkidle", timeout: 30000 }); } catch { console.warn(`skip ${url}`); continue; }
  await page.waitForTimeout(800);
  title ||= await page.title();
  await page.screenshot({ path: join(dir, "capture", `${n}.png`), fullPage: true });
  writeFileSync(join(dir, "capture", `${n}.html`), await page.content());

  // Stylesheets: rules we can read in the page, and the href of each sheet we cannot (cross-origin), fetched below.
  const found = await page.evaluate(() => [...document.styleSheets].map((s) => {
    try { return { href: s.href, css: [...s.cssRules].map((r) => r.cssText).join("\n") }; } catch { return { href: s.href, css: null }; }
  }));
  for (const s of found) {
    const key = s.href ?? `inline:${url}:${sheets.size}`;
    if (sheets.has(key)) continue;
    let css = s.css;
    if (css == null && s.href) { try { css = await (await page.request.get(s.href)).text(); } catch { css = ""; } }
    sheets.set(key, { base: s.href ?? url, css: css ?? "" });
  }

  // Regions worth naming: landmarks, controls, overlays, collections, and boxes that look like cards.
  candidates.push(...await page.evaluate((pageNo) => {
    const path = (el) => {
      if (el.id) return `#${CSS.escape(el.id)}`;
      const parts = [];
      for (let e = el; e && e.nodeType === 1 && e !== document.body; e = e.parentElement) {
        const i = [...e.parentElement.children].filter((c) => c.tagName === e.tagName).indexOf(e) + 1;
        parts.unshift(`${e.tagName.toLowerCase()}:nth-of-type(${i})`);
        if (e.parentElement?.id) { parts.unshift(`#${CSS.escape(e.parentElement.id)}`); break; }
      }
      return parts.join(" > ");
    };
    const roleOf = (el) => {
      const t = el.tagName.toLowerCase(), r = el.getAttribute("role");
      if (r) return r;
      if (["nav", "header", "footer", "aside", "form", "table", "dialog", "select", "textarea", "details", "figure"].includes(t)) return t;
      if (t === "input") return `input:${el.type}`;
      if (t === "button" || (t === "a" && /btn|button/i.test(el.className))) return "button";
      if ((t === "ul" || t === "ol") && el.children.length >= 3) return "list";
      const cs = getComputedStyle(el);
      if (el.children.length >= 2 && parseFloat(cs.borderRadius) >= 6 && (cs.boxShadow !== "none" || parseFloat(cs.borderTopWidth) > 0)) return "card";
      return null;
    };
    const out = [], took = new Set();
    for (const el of document.querySelectorAll("body *")) {
      const role = roleOf(el);
      if (!role) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 16 || r.height < 12) continue;
      const sel = path(el);
      if (took.has(sel)) continue;
      took.add(sel);
      out.push({ page: pageNo, url: location.href, role, selector: sel, tag: el.tagName.toLowerCase(), classes: String(el.className).slice(0, 120),
        size: [Math.round(r.width), Math.round(r.height)], text: (el.innerText || el.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ").slice(0, 80) });
      if (out.length >= 300) break;
    }
    return out;
  }, n));

  for (const href of await page.evaluate(() => [...document.querySelectorAll("a[href]")].map((a) => a.href))) {
    try { const u = new URL(href); if (u.origin === origin && !seen.has(u.href.split("#")[0])) queue.push(u.href); } catch {}
  }
}

// One stylesheet: url()s absolute; woff2 fonts downloaded and referenced by file name (build-gallery inlines them).
let css = "", fonts = 0;
const absolute = (text, base) => text.replace(/url\(\s*(["']?)([^"')]+)\1\s*\)/g, (m, q, u) => { try { return u.startsWith("data:") ? m : `url("${new URL(u, base).href}")`; } catch { return m; } });
for (const { base, css: text } of sheets.values()) css += absolute(text, base) + "\n";
// @import (Google Fonts and the like) is pulled in, so the file needs no network. Fetched with the browser's own
// user-agent: font services answer an unknown client with ttf, a real Chromium with woff2.
const ua = await page.evaluate(() => navigator.userAgent);
for (let round = 0; round < 3; round++) {
  const imports = [...css.matchAll(/@import\s+url\("([^"]+)"\)[^;]*;/g)];
  if (!imports.length) break;
  for (const [stmt, href] of imports) {
    let text = "";
    try { const res = await page.request.get(href, { headers: { "user-agent": ua } }); if (res.ok()) text = await res.text(); } catch {}
    css = css.split(stmt).join(text ? absolute(text, href) : stmt);
  }
}
// Every url() inside an @font-face, extension or not (icon fonts are often served as /font?kit=…): downloaded into
// fonts/ under a stable name whose extension follows the content type.
const fontUrls = [...new Set([...css.matchAll(/@font-face\s*\{[^}]*\}/g)].flatMap((m) => [...m[0].matchAll(/url\("(https?:[^"]+)"\)/g)].map((u) => u[1])))];
const EXT = { "font/woff2": "woff2", "font/woff": "woff", "font/ttf": "ttf", "font/otf": "otf", "application/font-woff2": "woff2", "application/font-woff": "woff", "application/x-font-ttf": "ttf", "font/sfnt": "ttf" };
for (const u of fontUrls) {
  try {
    const res = await page.request.get(u, { headers: { "user-agent": ua } });
    if (!res.ok()) continue;
    const type = (res.headers()["content-type"] ?? "").split(";")[0].trim();
    const ext = EXT[type] ?? /\.(woff2|woff|ttf|otf)(?:$|[?#])/.exec(u)?.[1] ?? "woff2";
    const name = `${createHash("sha1").update(u).digest("hex").slice(0, 12)}.${ext}`;
    writeFileSync(join(dir, "fonts", name), await res.body()); css = css.split(u).join(name); fonts++;
  } catch {}
}
writeFileSync(join(dir, "site.css"), css);
writeFileSync(join(dir, "candidates.json"), JSON.stringify(candidates, null, 1));
if (!existsSync(join(dir, "meta.json"))) {
  const product = (title.split(/[|·—–-]/)[0] || new URL(start).hostname).trim();
  writeFileSync(join(dir, "meta.json"), JSON.stringify({ product, css: "site.css", fontsDir: "fonts", skins: [], frames: null, source: start }, null, 2));
}
await browser.close();
console.log(`${seen.size} pages · site.css ${(css.length / 1024).toFixed(0)} KB, ${fonts} fonts · ${candidates.length} candidate regions → ${dir}`);
