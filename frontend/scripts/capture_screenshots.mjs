// Capture README screenshots against the running app (backend :8101, frontend :3101).
//   cd frontend && node scripts/capture_screenshots.mjs
// Writes PNGs to docs/screenshots/. Uses the frontend's Playwright installation.
// Uses the bundled examples so repeated runs hit the LLM cache (LLM_CACHE=1).
import { chromium } from "@playwright/test";
import { mkdirSync, readFileSync, rmSync } from "node:fs";
import { resolve } from "node:path";

const BASE = process.env.BASE_URL ?? "http://localhost:3101";
const OUT = resolve(process.cwd(), "..", "docs", "screenshots");
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1280, height: 860 }, deviceScaleFactor: 2, colorScheme: "light" });
const page = await ctx.newPage();
const shot = (name, opts = {}) => page.screenshot({ path: resolve(OUT, `${name}.png`), ...opts });
const top = async () => { await page.evaluate(() => window.scrollTo(0, 0)); await page.waitForTimeout(400); };
const setTheme = async (t) => { await page.evaluate((v) => localStorage.setItem("theme", v), t); await page.reload(); await page.waitForLoadState("networkidle"); };
const done = () => page.getByTestId("reasoning-streaming").waitFor({ state: "detached", timeout: 180_000 }).catch(() => {});

// 1. Landing, light and dark
await page.goto(`${BASE}/`);
await page.waitForLoadState("networkidle");
await setTheme("light");
await page.getByTestId("example-chip").first().waitFor();
await shot("landing");
await setTheme("dark");
await page.getByTestId("example-chip").first().waitFor();
await shot("landing-dark");
await setTheme("light");

// 2. Inline questions: a CV description that does not say who decides
await page.goto(`${BASE}/`);
await page.locator("#describe").fill("A tool that reads incoming CVs, scores candidates against the job description and ranks them for interviews.");
await page.getByTestId("describe-submit").click();
await page.getByTestId("question-form").waitFor({ timeout: 120_000 });
await page.getByTestId("question-form").evaluate((el) => el.scrollIntoView({ block: "center" }));
await page.waitForTimeout(500);
await shot("clarify");

// 3. Result: the CV screening example
await page.goto(`${BASE}/?example=cv-screening-deployer`);
for (let i = 0; i < 3; i++) {
  const w = await Promise.race([
    page.getByTestId("tier-hero").waitFor({ timeout: 180_000 }).then(() => "r"),
    page.getByTestId("question-form").waitFor({ timeout: 180_000 }).then(() => "q"),
  ]);
  if (w === "r") break;
  await page.getByTestId("clarify-continue").click();
  await page.getByTestId("question-form").waitFor({ state: "detached" });
}
await done();
await top();
await shot("result");
await shot("result-full", { fullPage: true });

// 4. Citation panel from the "why" sentence
await page.getByTestId("verdict-why").locator("[data-cite]").first().click();
await page.getByRole("dialog").waitFor({ timeout: 10_000 });
await page.waitForTimeout(600);
await shot("citation-panel");
await page.keyboard.press("Escape");

// 5. Mobile result, light and dark
await page.setViewportSize({ width: 390, height: 844 });
await top();
await shot("result-mobile");
await setTheme("dark");
await page.getByTestId("tier-hero").waitFor();
await top();
await shot("result-mobile-dark");

// 6. One dog per verdict: the colour block of each tier. Same saved result with the tier swapped,
//    so only the block (headline + dog) is captured, never the mismatched text below it.
await page.setViewportSize({ width: 1280, height: 860 });
await setTheme("light");
const tiers = ["prohibited", "high_risk", "limited_risk", "minimal_risk", "out_of_scope"];
const tiles = [];
for (const tier of tiers) {
  await page.evaluate((tier) => {
    const k = Object.keys(localStorage).find((x) => x.startsWith("aiact.assessment.") && !x.includes("tier-preview"));
    const a = JSON.parse(localStorage.getItem(k));
    a.id = `tier-preview-${tier}`;
    a.classification.tier = tier;
    localStorage.setItem(`aiact.assessment.${a.id}`, JSON.stringify(a));
  }, tier);
  await page.goto(`${BASE}/?id=tier-preview-${tier}`);
  const block = page.getByTestId("tier-hero").locator(".px-block").first();
  await block.waitFor();
  await page.waitForTimeout(300);
  const path = resolve(OUT, `_tile-${tier}.png`);
  await block.screenshot({ path, animations: "disabled" });
  tiles.push(path);
  await page.evaluate((id) => localStorage.removeItem(`aiact.assessment.${id}`), `tier-preview-${tier}`);
}
const sheet = await ctx.newPage();
await sheet.setViewportSize({ width: 1400, height: 400 });
await sheet.setContent(`<body style="margin:0;padding:24px;background:#ffffff;display:grid;grid-template-columns:repeat(2,1fr);gap:16px">${tiles
  .map((p) => `<img style="width:100%;border-radius:22px" src="data:image/png;base64,${readFileSync(p).toString("base64")}">`).join("")}</body>`);
await sheet.screenshot({ path: resolve(OUT, "verdicts.png"), fullPage: true });
tiles.forEach((p) => rmSync(p));

await browser.close();
console.log(`screenshots written to ${OUT}`);
