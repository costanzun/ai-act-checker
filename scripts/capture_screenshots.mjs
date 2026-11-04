// Capture README screenshots against the running app (backend :8101, frontend :3101).
//   cd frontend && node ../scripts/capture_screenshots.mjs
// Writes PNGs to docs/screenshots/. Uses the frontend's Playwright installation.
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";
import { resolve } from "node:path";

const BASE = process.env.BASE_URL ?? "http://localhost:3101";
const OUT = resolve(process.cwd(), "..", "docs", "screenshots");
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, colorScheme: "light" });
const page = await ctx.newPage();
const shot = (name, opts = {}) => page.screenshot({ path: resolve(OUT, `${name}.png`), ...opts });

// 1. Landing (light, full page) and dark
await page.goto(`${BASE}/`);
await page.waitForLoadState("networkidle");
await page.waitForTimeout(500);
await shot("landing", { fullPage: true });
await page.emulateMedia({ colorScheme: "dark" });
await page.locator('[data-testid="theme-toggle"]').click().catch(() => {});
await page.waitForTimeout(400);
await shot("landing-dark");
await page.locator('[data-testid="theme-toggle"]').click().catch(() => {});
await page.emulateMedia({ colorScheme: "light" });

// 2. Clarify step: a description that lacks the role, so a question is asked
await page.goto(`${BASE}/assess`);
await page.getByRole("textbox").first().fill(
  "A tool that reads incoming CVs, scores candidates against the job description and ranks them for interviews."
);
await page.getByRole("button", { name: /check my system/i }).click();
await page.getByText(/a few questions|round 1/i).first().waitFor({ timeout: 120_000 });
await page.waitForTimeout(300);
await shot("clarify", { fullPage: true });

// 3. Result: the CV screening example (deployer, no questions expected)
await page.goto(`${BASE}/assess?example=cv-screening-deployer`);
await page.getByRole("button", { name: /check my system/i }).click();
await page.getByText(/high risk|rischio alto/i).first().waitFor({ timeout: 180_000 });
await page.waitForTimeout(800);
await shot("result");
await shot("result-full", { fullPage: true });

// 4. Citation panel
await page.getByText("Annex III, point 4(a)").first().click();
await page.getByRole("dialog").waitFor({ timeout: 10_000 });
await page.waitForTimeout(400);
await shot("citation-panel");
await page.keyboard.press("Escape");

// 5. Mobile result
await page.setViewportSize({ width: 390, height: 844 });
await page.waitForTimeout(300);
await shot("result-mobile");

await browser.close();
console.log(`screenshots written to ${OUT}`);
