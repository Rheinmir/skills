#!/usr/bin/env node
// Drive headless Chrome over the DevTools protocol: open the page, click each selector
// with a real mouse event, print a state probe after each click, collect uncaught errors,
// and optionally save a screenshot after the last step. Exit 1 on any page error.
//   node browser-check.mjs --url file:///…/ui-inventory.html#gallery [--width 1440] [--wait 8000]
//     [--probe "<js expression returning JSON-able>"] [--shot out.png] [--click "sel1" --click "sel2" …]
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const argv = process.argv.slice(2);
const opt = (k, d) => (argv.includes(`--${k}`) ? argv[argv.indexOf(`--${k}`) + 1] : d);
const clicks = argv.flatMap((a, i) => (a === "--click" ? [argv[i + 1]] : []));
const url = opt("url");
const width = Number(opt("width", "1440"));
const height = Number(opt("height", "1000"));
const wait = Number(opt("wait", "8000"));
const probe = opt("probe", '({hash: decodeURIComponent(location.hash), shown: [...document.querySelectorAll("section.doc")].filter(s=>!s.hidden).map(s=>s.id).join(","), ab: document.body.dataset.ab})');
const shot = opt("shot");

const chromes = [
  process.env.CHROME_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
].filter(Boolean);
const binary = chromes.find((p) => existsSync(p));
if (!url || !binary) throw new Error(!url ? "--url is required" : "no Chrome/Edge found; set CHROME_PATH");

const port = 9300 + Math.floor(Math.random() * 500);
const chrome = spawn(binary, ["--headless=new", "--disable-gpu", "--hide-scrollbars", `--remote-debugging-port=${port}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), "ui-inv-"))}`, `--window-size=${width},${height}`, "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 60 && !target; i += 1) {
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find((t) => t.type === "page"); } catch { await sleep(250); }
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => ws.addEventListener("open", r, { once: true }));
let id = 0;
const pending = new Map();
const errors = [];
ws.addEventListener("message", (e) => {
  const m = JSON.parse(e.data);
  if (m.method === "Runtime.exceptionThrown") errors.push(m.params.exceptionDetails.exception?.description ?? m.params.exceptionDetails.text);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
});
const send = (method, params = {}) => new Promise((r) => { id += 1; pending.set(id, r); ws.send(JSON.stringify({ id, method, params })); });
const evaluate = async (expression) => (await send("Runtime.evaluate", { expression, returnByValue: true })).result?.result?.value;
await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
await send("Page.navigate", { url });
await sleep(wait);
console.log("loaded", JSON.stringify(await evaluate(probe)));
for (const selector of clicks) {
  const box = await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); if (!el) return null; el.scrollIntoView({block:"center"}); const r = el.getBoundingClientRect(); return {x: r.x + r.width / 2, y: r.y + r.height / 2}; })()`);
  if (!box) { console.log(selector, "MISSING"); errors.push(`missing ${selector}`); continue; }
  for (const type of ["mousePressed", "mouseReleased"]) await send("Input.dispatchMouseEvent", { type, x: box.x, y: box.y, button: "left", clickCount: 1 });
  await sleep(900);
  console.log(selector, JSON.stringify(await evaluate(probe)));
}
if (shot) {
  await evaluate(`document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView({block:"start"})`);
  await sleep(800);
  writeFileSync(shot, Buffer.from((await send("Page.captureScreenshot", { format: "png" })).result.data, "base64"));
  console.log("screenshot", shot);
}
console.log("errors", errors.length ? errors : "none");
ws.close();
chrome.kill();
process.exit(errors.length ? 1 : 0);
