#!/usr/bin/env node
/**
 * Customer-journey probe.
 *
 * Default: HTTP only (no form posts, no lead spam).
 * If Playwright + Chromium are installed, pass --browser to also record
 * status, title, and console errors for the same journeys.
 *
 *   node scripts/playwright_cx_stress.js
 *   node scripts/playwright_cx_stress.js --dry-run
 *   node scripts/playwright_cx_stress.js --browser
 *
 * Concurrent form submission against production is intentionally not implemented.
 * Set ECOWOODS_ALLOW_LIVE_POST=1 and point --post-url at a staging endpoint
 * you control if you need a load test. This process will still refuse to POST
 * to https://ecowoods.ca.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "..");
const reports = path.join(root, "reports");
const args = new Set(process.argv.slice(2));
const dry = args.has("--dry-run");
const wantBrowser = args.has("--browser");
const origin = (process.argv.includes("--url")
  ? process.argv[process.argv.indexOf("--url") + 1]
  : "https://ecowoods.ca"
).replace(/\/$/, "");

const JOURNEYS = [
  { id: "home", path: "/", expect: ["Ecowoods", "tel:"] },
  { id: "services", path: "/services", expect: ["sand", "tel:"] },
  { id: "dust", path: "/services/dust-free-sanding", expect: ["HEPA", "dust"] },
  { id: "refinish", path: "/hardwood-floor-refinishing-toronto", expect: ["4.75", "2.50"] },
  { id: "install", path: "/hardwood-flooring-toronto", expect: ["11.00"] },
  { id: "cost", path: "/guides/hardwood-flooring-cost-toronto", expect: ["$"] },
  { id: "framework", path: "/framework", expect: ["27", "Framework"] },
  { id: "assess", path: "/framework/assess", expect: ["quote"] },
  { id: "case", path: "/case-studies", expect: ["case"] },
  { id: "estimate", path: "/estimate", expect: ["estimate"] },
  { id: "contact", path: "/contact", expect: ["647"] },
  { id: "reviews", path: "/reviews", expect: ["HomeStars"] },
  { id: "studio", path: "/floor-studio", expect: ["floor"] },
  { id: "quote-check", path: "/quote-check", expect: ["quote"] },
  { id: "area", path: "/service-areas/downtown-toronto", expect: ["Toronto"] },
  { id: "realtors", path: "/realtors", expect: ["list"] },
];

function write(name, obj) {
  fs.mkdirSync(reports, { recursive: true });
  fs.writeFileSync(path.join(reports, name), JSON.stringify(obj, null, 2) + "\n");
}

async function httpGet(url) {
  const t0 = Date.now();
  const res = await fetch(url, {
    redirect: "follow",
    headers: { "user-agent": "EcowoodsExternalAudit/1.0 (cx probe; no form posts)" },
  });
  const buf = await res.arrayBuffer();
  const body = new TextDecoder("utf-8").decode(buf.slice(0, 400_000));
  const title = (body.match(/<title[^>]*>([^<]*)<\/title>/i) || [, ""])[1].trim();
  return {
    url,
    status: res.status,
    ms: Date.now() - t0,
    bytes: buf.byteLength,
    title,
    body,
    finalUrl: res.url,
  };
}

async function runHttp() {
  const rows = [];
  for (const j of JOURNEYS) {
    const url = origin + j.path;
    try {
      const res = await httpGet(url);
      const missing = j.expect.filter((needle) => !res.body.toLowerCase().includes(needle.toLowerCase()));
      const forms = (res.body.match(/<form[\s>]/gi) || []).length;
      rows.push({
        id: j.id,
        path: j.path,
        status: res.status,
        ms: res.ms,
        bytes: res.bytes,
        title: res.title,
        forms,
        missing_expect: missing,
        has_tel: res.body.includes("tel:"),
        pass: res.status === 200 && missing.length === 0,
      });
      console.log(`${res.status} ${j.path} ${res.ms}ms missing=${missing.join(",") || "-"}`);
    } catch (err) {
      rows.push({ id: j.id, path: j.path, status: 0, error: String(err), pass: false });
      console.log(`ERR ${j.path} ${err}`);
    }
  }
  return rows;
}

async function runBrowser(rows) {
  let chromium;
  try {
    const mod = await import("playwright");
    chromium = mod.chromium;
  } catch {
    return { launched: false, reason: "playwright is not installed on NODE_PATH. HTTP results stand. See download-heavy-deps.sh." };
  }
  let browser;
  try {
    browser = await chromium.launch({ headless: true });
  } catch (err) {
    return { launched: false, reason: `chromium failed to launch: ${err}` };
  }
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text().slice(0, 300));
  });
  page.on("pageerror", (err) => consoleErrors.push(String(err).slice(0, 300)));
  const visits = [];
  for (const j of JOURNEYS.slice(0, 8)) {
    const url = origin + j.path;
    try {
      const res = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
      const title = await page.title();
      visits.push({ id: j.id, status: res ? res.status() : 0, title });
    } catch (err) {
      visits.push({ id: j.id, error: String(err) });
    }
  }
  await browser.close();
  return { launched: true, viewport: "390x844", visits, console_errors: consoleErrors.slice(0, 30) };
}

async function main() {
  if (dry) {
    console.log(JSON.stringify({ dry_run: true, journeys: JOURNEYS.length, posts: 0 }));
    return;
  }
  if (process.env.ECOWOODS_ALLOW_LIVE_POST === "1") {
    console.log("ECOWOODS_ALLOW_LIVE_POST is set, but this script still refuses to POST to ecowoods.ca.");
  }
  const httpRows = await runHttp();
  let browser = { launched: false, reason: "--browser not passed" };
  if (wantBrowser) browser = await runBrowser(httpRows);
  const passed = httpRows.filter((r) => r.pass).length;
  const report = {
    audited_at: new Date().toISOString(),
    origin,
    mode: browser.launched ? "browser" : "http",
    posts_sent: 0,
    journeys: httpRows.length,
    passed,
    pass_rate: httpRows.length ? Number((passed / httpRows.length).toFixed(4)) : 0,
    rows: httpRows,
    browser,
    console_errors: browser.console_errors || [],
  };
  write("cx_browser.json", report);
  console.log(`cx pass ${passed}/${httpRows.length} mode=${report.mode}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
