#!/usr/bin/env node
// make-agent-uiux-map step 3: cut each named component out of the live site into demos/<id>.html.
//
//   node snip.mjs <inventory-dir> <picks.json> [--width 1440]
//
// picks.json: [{ "id": "2-context-menu" | "x-pricing-card", "url": "...", "selector": "...",
//                "before": ["click:button.more", "hover:.menu", "wait:300"] }]   (before is optional)
// The element's outerHTML is kept as rendered, with src/href made absolute, inside
// <div class="demo-root" data-source="url selector"><div style="width:Wpx;background:…">…</div></div>
// so the gallery can frame it. N-slug ids take the Name That UI catalogue number; x-slug ids are the site's own.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { playwright } from "./pw.mjs";

const args = process.argv.slice(2);
const [dirArg, picksArg] = args.filter((a) => !a.startsWith("--") && !/^\d+$/.test(a));
if (!dirArg || !picksArg) { console.error("usage: node snip.mjs <inventory-dir> <picks.json> [--width 1440]"); process.exit(1); }
const width = args.includes("--width") ? Number(args[args.indexOf("--width") + 1]) : 1440;
const dir = resolve(dirArg);
mkdirSync(join(dir, "demos"), { recursive: true });
const picks = JSON.parse(readFileSync(resolve(picksArg), "utf8"));

const { chromium } = await playwright();
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height: 900 } });
let done = 0, current = "";
for (const pick of picks) {
  if (!/^(\d+|x)-[a-z0-9-]+$/.test(pick.id)) { console.warn(`skip ${pick.id}: ids look like 12-segmented-control or x-pricing-card`); continue; }
  try {
    if (pick.url !== current || pick.before?.length) { await page.goto(pick.url, { waitUntil: "networkidle", timeout: 30000 }); current = pick.url; await page.waitForTimeout(500); }
    for (const step of pick.before ?? []) {
      const [verb, ...rest] = step.split(":"), target = rest.join(":");
      if (verb === "click") await page.click(target, { timeout: 5000 });
      else if (verb === "hover") await page.hover(target, { timeout: 5000 });
      else if (verb === "wait") await page.waitForTimeout(Number(target));
      await page.waitForTimeout(250);
    }
    const html = await page.$eval(pick.selector, (el) => {
      const copy = el.cloneNode(true);
      for (const [attr, prop] of [["src", "src"], ["href", "href"], ["poster", "poster"]]) {
        const live = el.querySelectorAll(`[${attr}]`), cloned = copy.querySelectorAll(`[${attr}]`);
        cloned.forEach((c, i) => { if (live[i]?.[prop]) c.setAttribute(attr, live[i][prop]); });
      }
      const r = el.getBoundingClientRect();
      let bg = "transparent";
      for (let e = el; e; e = e.parentElement) { const c = getComputedStyle(e).backgroundColor; if (c && !/rgba?\([^)]*,\s*0\)$|transparent/.test(c)) { bg = c; break; } }
      return { outer: copy.outerHTML, w: Math.ceil(r.width), h: Math.ceil(r.height), bg };
    });
    writeFileSync(join(dir, "demos", `${pick.id}.html`),
      `<div class="demo-root" data-source="${pick.url} ${pick.selector.replace(/"/g, "&quot;")}">\n<div style="width:${html.w}px;min-height:${html.h}px;background:${html.bg}">\n${html.outer}\n</div>\n</div>\n`);
    done++;
  } catch (e) { console.warn(`skip ${pick.id}: ${e.message.split("\n")[0]}`); }
}
await browser.close();
console.log(`${done}/${picks.length} demos → ${join(dir, "demos")}`);
