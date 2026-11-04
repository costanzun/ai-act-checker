import { expect, test, type Page } from "@playwright/test";

/** Answer any clarify rounds by picking the first option, until the result is shown. */
async function untilResult(page: Page) {
  for (let i = 0; i < 3; i++) {
    const winner = await Promise.race([
      page.getByTestId("result-view").waitFor({ timeout: 150_000 }).then(() => "result" as const),
      page.getByTestId("question-form").waitFor({ timeout: 150_000 }).then(() => "questions" as const),
      page.getByTestId("error-card").waitFor({ timeout: 150_000 }).then(() => "error" as const),
    ]);
    if (winner === "result") return;
    if (winner === "error") throw new Error("error card: " + (await page.getByTestId("error-card").innerText()));
    const form = page.getByTestId("question-form");
    const sets = form.locator("fieldset");
    const n = await sets.count();
    for (let k = 0; k < n; k++) {
      const fs = sets.nth(k);
      const radios = fs.getByRole("radio");
      const rc = await radios.count();
      // boolean (Yes/No/Not sure): answer "No" so exemptions do not apply; otherwise first option
      if (rc === 3) await radios.nth(1).click();
      else if (rc) await radios.first().click();
      else await fs.getByRole("textbox").fill("n/a");
    }
    await page.getByTestId("clarify-continue").click();
  }
}

test("landing loads examples from the API", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("example-link")).toHaveCount(12, { timeout: 15_000 });
  await expect(page.getByRole("heading", { name: "CV screening for an HR department" })).toBeVisible();
});

test("CV example: stages, streaming, high risk, citations, exports", async ({ page }) => {
  await page.goto("/");
  const t0 = Date.now();
  await page.getByRole("link", { name: /CV screening for an HR department/ }).click();
  await expect(page.getByTestId("stage-timeline")).toBeVisible();
  let tFirstToken = -1;
  const tokenWatch = page.getByTestId("reasoning-panel").first().waitFor({ timeout: 150_000 }).then(() => { tFirstToken = Date.now() - t0; }).catch(() => undefined);
  await untilResult(page);
  const tResult = Date.now() - t0;
  await tokenWatch;
  console.log(`TIMING cv: first reasoning token ${tFirstToken} ms, result ${tResult} ms (from click)`);

  const hero = page.getByTestId("tier-hero");
  await expect(hero).toHaveAttribute("data-tier", "high_risk");
  console.log("ROLE badge:", await hero.innerText());

  const chip = page.locator('[data-testid="reasoning-panel"] [data-cite], [data-testid="tier-hero"] [data-cite]').first();
  await chip.click();
  await expect(page.getByTestId("citation-panel")).not.toContainText("Loading", { timeout: 10_000 });
  await page.keyboard.press("Escape");
  await page.locator('[data-cite="annex:III.4.a"]').first().click();
  await expect(page.getByTestId("citation-panel")).toContainText("recruitment or selection of natural persons");
  await page.keyboard.press("Escape");

  const [md] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Download Markdown" }).click()]);
  expect(md.suggestedFilename()).toMatch(/\.md$/);
  const [pdf] = await Promise.all([page.waitForEvent("download", { timeout: 60_000 }), page.getByRole("button", { name: "Download PDF" }).click()]);
  expect(pdf.suggestedFilename()).toMatch(/\.pdf$/);
});

test("emotion recognition at the call centre is prohibited", async ({ page }) => {
  await page.goto("/assess?example=emotion-recognition-call-centre");
  await untilResult(page);
  await expect(page.getByTestId("tier-hero").getByRole("heading", { level: 2 })).toHaveText("Prohibited practice");
});

test("customer service chatbot has transparency obligations", async ({ page }) => {
  await page.goto("/assess?example=customer-service-chatbot");
  await untilResult(page);
  await expect(page.getByTestId("tier-hero").getByRole("heading", { level: 2 })).toHaveText("Transparency obligations");
});

test("IT: payroll rules is out of scope with Italian reasoning", async ({ page }) => {
  await page.goto("/assess?example=payroll-rules&lang=it");
  await untilResult(page);
  await expect(page.getByTestId("tier-hero").getByRole("heading", { level: 2 })).toHaveText("Fuori dall'ambito di applicazione");
  await expect(page.getByTestId("reasoning-panel")).toContainText(/\b(il|della|che|non)\b/);
  await expect(page.getByTestId("result-view")).toBeVisible();
  console.log("OOS obligations section:", await page.locator("#obligations-heading").locator("xpath=..").innerText());
});
