// Record the README demo video: example chip -> follow-up question -> verdict with its dog -> citation panel
// -> what you must do -> what would change the answer -> dark mode.
//   cd frontend && BASE_URL=http://localhost:3101 node scripts/record_demo.mjs
// Writes docs/media/demo.webm (Playwright's raw recording). Convert it with ffmpeg:
//   ffmpeg -y -i ../docs/media/demo.webm -c:v libx264 -pix_fmt yuv420p -crf 23 -preset slow -movflags +faststart -an ../docs/media/demo.mp4
//   ffmpeg -y -t 34 -i ../docs/media/demo.webm -vf "fps=10,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" ../docs/media/demo.gif
// The flow uses the bundled customer-service chatbot example answered "No", so with LLM_CACHE=1 a
// repeated run replays cached model responses instead of calling the model again.
import { chromium } from "@playwright/test";
import { mkdirSync, readdirSync, renameSync, rmSync } from "node:fs";
import { resolve } from "node:path";

const BASE = process.env.BASE_URL ?? "http://localhost:3101";
const OUT = resolve(process.cwd(), "..", "docs", "media");
const TMP = resolve(OUT, "_video");
mkdirSync(TMP, { recursive: true });

const SIZE = { width: 1280, height: 800 };
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: SIZE, recordVideo: { dir: TMP, size: SIZE }, colorScheme: "light" });
// Prime the theme before the first paint so the recording does not start with a reload.
await ctx.addInitScript(() => { try { if (!sessionStorage.getItem("demo.primed")) { localStorage.setItem("theme", "light"); sessionStorage.setItem("demo.primed", "1"); } } catch {} });
const page = await ctx.newPage();
const pause = (ms) => page.waitForTimeout(ms);
const scrollTo = async (locatorOrY, ms = 1600) => {
  if (typeof locatorOrY === "number") {
    await page.evaluate((y) => window.scrollTo({ top: y, behavior: "smooth" }), locatorOrY);
  } else {
    await locatorOrY.evaluate((el) => window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 90, behavior: "smooth" }));
  }
  await pause(ms);
};
const moveTo = async (locator) => {
  const b = await locator.boundingBox();
  if (b) await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2, { steps: 14 });
};

await page.goto(`${BASE}/`);
await page.waitForLoadState("networkidle");
await page.getByTestId("example-chip").first().waitFor();
await page.mouse.move(640, 300);
await pause(2500);

// 1. Pick an example
const chip = page.locator('[data-example="customer-service-chatbot"]');
await moveTo(chip);
await pause(900);
await chip.click();

// 2. The one question that changes the answer
const form = page.getByTestId("question-form");
await form.waitFor({ timeout: 120_000 });
await form.evaluate((el) => el.scrollIntoView({ block: "center", behavior: "smooth" }));
await pause(3200);
const no = form.getByTestId("question").first().locator("button").filter({ hasText: /^No$/ });
await moveTo(no);
await pause(700);
await no.click();
await pause(1200);
const go = page.getByTestId("clarify-continue");
await moveTo(go);
await pause(500);
await go.click();

// 3. Verdict with its dog
await page.getByTestId("tier-hero").waitFor({ timeout: 120_000 });
await page.getByTestId("reasoning-streaming").waitFor({ state: "detached", timeout: 120_000 }).catch(() => {});
await scrollTo(0, 800);
await pause(3500);

// 4. Citation: hover for the text, click for the full provision
const cite = page.getByTestId("verdict-why").locator("[data-cite]").first();
await moveTo(cite);
await pause(2600);
await cite.click();
await page.getByRole("dialog").waitFor({ timeout: 10_000 });
await pause(4500);
await page.keyboard.press("Escape");
await pause(900);

// 5. What you must do, documents, what would change the answer
await scrollTo(page.getByTestId("must-do"), 3800);
await scrollTo(page.getByTestId("checklist"), 3800);
const whatIf = page.getByTestId("what-if");
if (await whatIf.count()) await scrollTo(whatIf, 4000);

// 6. The cited reasoning
const toggle = page.getByTestId("reasoning-toggle");
if (await toggle.count()) {
  await scrollTo(toggle, 1400);
  await moveTo(toggle);
  await toggle.click();
  await pause(1000);
  await scrollTo(page.getByTestId("reasoning-panel"), 4200);
}

// 7. Back to the top, dark mode
await scrollTo(0, 1600);
const theme = page.getByTestId("theme-toggle");
await moveTo(theme);
await pause(600);
await theme.click();
await pause(3500);

await ctx.close();
await browser.close();

const files = readdirSync(TMP).filter((f) => f.endsWith(".webm"));
if (files.length) {
  renameSync(resolve(TMP, files[0]), resolve(OUT, "demo.webm"));
  console.log(`video written to ${resolve(OUT, "demo.webm")}`);
}
rmSync(TMP, { recursive: true, force: true });
