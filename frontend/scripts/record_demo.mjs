// Record a short demo video of the main flow against the running app, for docs/screenshots/demo.gif.
//   cd frontend && node scripts/record_demo.mjs && ffmpeg -i ../docs/screenshots/demo.webm ... (see README)
import { chromium } from "@playwright/test";
import { mkdirSync, readdirSync, renameSync } from "node:fs";
import { resolve } from "node:path";

const BASE = process.env.BASE_URL ?? "http://localhost:3101";
const OUT = resolve(process.cwd(), "..", "docs", "screenshots");
const TMP = resolve(OUT, "_video");
mkdirSync(TMP, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1280, height: 800 },
  recordVideo: { dir: TMP, size: { width: 1280, height: 800 } },
  colorScheme: "light",
});
const page = await ctx.newPage();
const pause = (ms) => page.waitForTimeout(ms);
const smoothScroll = async (y, ms = 900) => {
  await page.evaluate(({ y }) => window.scrollTo({ top: y, behavior: "smooth" }), { y });
  await pause(ms);
};

await page.goto(`${BASE}/`);
await page.evaluate(() => localStorage.setItem("theme", "light"));
await page.reload();
await page.waitForLoadState("networkidle");
await pause(1500);
await page.locator('[data-example="cv-screening-deployer"]').click();
for (let i = 0; i < 3; i++) {
  const w = await Promise.race([
    page.getByTestId("tier-hero").waitFor({ timeout: 180_000 }).then(() => "r"),
    page.getByTestId("question-form").waitFor({ timeout: 180_000 }).then(() => "q"),
  ]);
  if (w === "r") break;
  await pause(1500);
  await page.getByTestId("clarify-continue").click();
  await page.getByTestId("question-form").waitFor({ state: "detached" });
}
await pause(2500);
await page.getByTestId("verdict-why").locator("[data-cite]").first().hover();
await pause(1800);
await page.getByTestId("verdict-why").locator("[data-cite]").first().click();
await page.getByRole("dialog").waitFor({ timeout: 10_000 });
await pause(2200);
await page.keyboard.press("Escape");
await pause(500);
await smoothScroll(700, 1400);
await smoothScroll(1400, 1400);
await smoothScroll(2100, 1400);
await pause(800);
await smoothScroll(0, 800);
await pause(600);
await ctx.close();
await browser.close();

const files = readdirSync(TMP).filter((f) => f.endsWith(".webm"));
if (files.length) {
  renameSync(resolve(TMP, files[0]), resolve(OUT, "demo.webm"));
  console.log(`video written to ${resolve(OUT, "demo.webm")}`);
}
