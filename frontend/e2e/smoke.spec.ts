import { expect, test } from "@playwright/test";

test("landing -> example -> clarify -> result -> citation -> IT -> dark", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Which EU AI Act rules apply to your AI system?");

  // First example in the gallery
  const first = page.getByTestId("example-link").first();
  await expect(first).toBeVisible();
  await first.click();

  // Stepper + streaming stages
  await expect(page.getByTestId("stepper")).toBeVisible();
  await expect(page.getByTestId("stage-timeline")).toBeVisible();

  // Clarify round 1: answer both questions
  const form = page.getByTestId("question-form");
  await expect(form).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId("round-label")).toHaveText("Round 1 of 2");
  await form.getByText("We use a system from a vendor").click();
  await form.getByText("Yes", { exact: true }).click();
  await page.getByTestId("clarify-continue").click();

  // Result
  const hero = page.getByTestId("tier-hero");
  await expect(hero).toBeVisible({ timeout: 20_000 });
  await expect(hero).toHaveAttribute("data-tier", "high_risk");
  await expect(hero.getByRole("heading", { level: 2 })).toHaveText("High risk");

  // Citation chip opens the panel with law text
  const chip = page.locator('[data-testid="reasoning-panel"] [data-cite="annex:III.4.a"]').first();
  await chip.click();
  const panel = page.getByTestId("citation-panel");
  await expect(panel).toContainText("recruitment or selection of natural persons");
  await expect(page).toHaveURL(/#cite=annex:III\.4\.a/);
  await page.keyboard.press("Escape");
  await expect(panel).toBeHidden();

  // Italian
  await page.getByRole("button", { name: "IT", exact: true }).click();
  await expect(hero.getByRole("heading", { level: 2 })).toHaveText("Rischio alto");
  await expect(page.locator("html")).toHaveAttribute("lang", "it");

  // Dark mode
  await page.getByTestId("theme-toggle").click();
  await expect(page.locator("html")).toHaveClass(/dark/);
});

test("deep link opens the citation panel", async ({ page }) => {
  await page.goto("/#cite=art:6.2");
  await expect(page.getByTestId("citation-panel")).toContainText("Annex III shall be considered to be high-risk");
});

test("about and law pages render", async ({ page }) => {
  await page.goto("/about");
  await expect(page.getByTestId("about-model")).toContainText("fixture-v1");
  await page.goto("/law/art:50.1");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Art. 50(1)");
});

test("unknown saved result shows the not-found card; describe step has no empty card", async ({ page }) => {
  await page.goto("/assess");
  await expect(page.getByTestId("empty-state")).toHaveCount(0);
  await expect(page.locator("#describe")).toBeVisible();
  await page.goto("/assess?id=does-not-exist");
  await expect(page.getByTestId("not-found")).toContainText("We could not find that result in this browser");
});

test("boolean questions have exactly three choices and no 'I don't know' link", async ({ page }) => {
  await page.goto("/assess?example=cv-screening");
  const form = page.getByTestId("question-form");
  await expect(form).toBeVisible({ timeout: 15_000 });
  const boolQ = form.locator("fieldset").nth(1);
  await expect(boolQ.getByRole("radio")).toHaveCount(3);
  await expect(boolQ.getByRole("button", { name: "I don't know" })).toHaveCount(0);
  await expect(form.locator("fieldset").first().getByRole("button", { name: "I don't know" })).toHaveCount(1);
});

test("timeline shows all milestones and highlights relevant ones; print view is complete", async ({ page }) => {
  await page.goto("/assess?example=customer-chatbot");
  await expect(page.getByTestId("result-view")).toBeVisible({ timeout: 20_000 });
  const items = page.getByTestId("timeline").locator("li");
  await expect(items).toHaveCount(11);
  await expect(items.locator("visible=true")).toHaveCount(1);
  await page.getByTestId("timeline-toggle").click();
  await expect(items.locator("visible=true")).toHaveCount(11);
  await page.getByTestId("timeline-toggle").click();
  await expect(page.getByTestId("obligations-count")).toContainText("2 obligations");
  await expect(page.getByTestId("timeline").locator('li[data-relevant="true"]')).toHaveCount(1);
  // chatbot result has no uncertainties -> callout hidden
  await expect(page.getByText("Assumptions and open points")).toHaveCount(0);

  await page.emulateMedia({ media: "print" });
  await expect(page.locator("header")).toBeHidden();
  await expect(page.locator("footer")).toBeHidden();
  await expect(page.getByRole("button", { name: "Download PDF" })).toBeHidden();
  await expect(page.getByRole("tablist")).toBeHidden();
  await expect(page.getByTestId("obligation").locator("visible=true")).toHaveCount(2);
});

test("375px header: wordmark on one line, toggles visible, menu has Home/About", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto("/");
  const mark = page.getByText("EU AI Act Checker").first();
  const box = await mark.boundingBox();
  expect(box!.height).toBeLessThan(28);
  await expect(page.getByRole("button", { name: "IT", exact: true })).toBeVisible();
  await expect(page.getByTestId("theme-toggle")).toBeVisible();
  await page.getByTestId("mobile-menu").click();
  await expect(page.getByRole("menuitem", { name: "About" })).toBeVisible();
});

test("'/' focuses the landing textarea", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("example-link").first()).toBeVisible(); // hydrated
  await page.keyboard.press("/");
  await expect(page.locator("#hero-description")).toBeFocused();
});

test("overlay badges: GPAI in gallery and hero, Art. 50 in hero", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator('[data-testid="examples-gallery"] [data-overlay="gpai"]')).toHaveCount(1);
  await page.goto("/assess?example=customer-chatbot");
  await expect(page.getByTestId("tier-hero")).toBeVisible({ timeout: 20_000 });
  await expect(page.locator('[data-testid="tier-hero"] [data-overlay="transparency_art50"]')).toBeVisible();
  await page.goto("/assess?example=gpai-model");
  await expect(page.locator('[data-testid="tier-hero"] [data-overlay="gpai"]')).toBeVisible({ timeout: 20_000 });
});

test("conditional obligations are grouped separately", async ({ page }) => {
  await page.goto("/assess?example=cv-screening");
  const form = page.getByTestId("question-form");
  await expect(form).toBeVisible({ timeout: 15_000 });
  await form.getByText("We use a system from a vendor").click();
  await form.getByText("Yes", { exact: true }).click();
  await page.getByTestId("clarify-continue").click();
  const cond = page.getByTestId("conditional-group").first();
  await expect(cond).toContainText("Conditional — check whether this applies to you");
  await expect(cond).toContainText("Fundamental rights impact assessment");
});

test("'Correct this' reopens the Describe step prefilled", async ({ page }) => {
  await page.goto("/assess?example=spam-filter");
  await expect(page.getByTestId("result-view")).toBeVisible({ timeout: 20_000 });
  await page.getByRole("button", { name: "Correct this" }).click();
  await expect(page.locator("#describe")).toHaveValue(/spam folder/);
});

test("mobile: hero first, reasoning before the export row", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 800 });
  await page.goto("/assess?example=customer-chatbot");
  await expect(page.getByTestId("result-view")).toBeVisible({ timeout: 20_000 });
  const y = async (sel: string) => (await page.locator(sel).first().boundingBox())!.y;
  const hero = await y('[data-testid="tier-hero"]');
  const reasoning = await y('[data-testid="reasoning-panel"]');
  const exportRow = await y('[role="group"][aria-label="Export"]');
  expect(hero).toBeLessThan(reasoning);
  expect(reasoning).toBeLessThan(exportRow);
  // citation chips on touch-less emulation still open the panel
  await page.locator("[data-cite]").first().click();
  await expect(page.getByTestId("citation-panel")).toBeVisible();
});
