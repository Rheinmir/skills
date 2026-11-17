// Find Playwright wherever it is installed: next to the caller, or globally (npm i -g playwright). One import for both
// scripts so the skill folder carries no node_modules of its own.
import { execSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

export async function playwright() {
  try { return await import("playwright"); } catch {}
  const roots = [];
  try { roots.push(execSync("npm root -g", { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim()); } catch {}
  roots.push(join(process.env.HOME ?? "", ".local/lib/node_modules"), "/opt/homebrew/lib/node_modules", "/usr/local/lib/node_modules");
  for (const root of roots) {
    const entry = join(root, "playwright", "index.mjs");
    if (existsSync(entry)) return import(pathToFileURL(entry).href);
  }
  console.error("Playwright not found. Install it once: npm i -g playwright && npx playwright install chromium");
  process.exit(1);
}
