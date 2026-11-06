import { expect, test, type Page } from "@playwright/test";

/** Answer inline questions cheaply and deterministically: boolean -> "No", others -> "Not sure". */
async function untilResult(page: Page) {
  for (let i = 0; i < 3; i++) {
    const handle = await page.waitForFunction(() => {
      if (document.querySelector('[data-testid="tier-hero"]')) return "result";
      if (document.querySelector('[data-testid="question-form"]')) return "questions";
      if (document.querySelector('[data-testid="error-card"]')) return "error";
      return null;
    }, undefined, { timeout: 120_000 });
    const winner = await handle.jsonValue();
    if (winner === "result") return;
    if (winner === "error") throw new Error("error card: " + (await page.getByTestId("error-card").innerText()));
    const qs = page.getByTestId("question-form").getByTestId("question");
    const n = await qs.count();
    for (let k = 0; k < n; k++) {
      const no = qs.nth(k).getByRole("radio", { name: "No", exact: true });
      if (await no.count()) await no.click();
    }
    await page.getByTestId("clarify-continue").click();
    await page.getByTestId("question-form").waitFor({ state: "detached" });
  }
}

test("landing loads example chips from the API", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("example-chip")).toHaveCount(5, { timeout: 15_000 });
  await expect(page.getByRole("button", { name: "CV screening for an HR department" })).toBeVisible();
});

test("CV example: progress, verdict before reasoning, high risk, citations, exports", async ({ page }) => {
  await page.goto("/");
  const t0 = Date.now();
  await page.getByRole("button", { name: "CV screening for an HR department" }).click();
  await expect(page.getByTestId("progress")).toBeVisible();
  await untilResult(page);
  const tVerdict = Date.now() - t0;
  await expect(page.getByTestId("reasoning-streaming")).toHaveCount(0, { timeout: 150_000 });
  console.log(`TIMING cv: verdict ${tVerdict} ms, reasoning done ${Date.now() - t0} ms (from click)`);

  const hero = page.getByTestId("tier-hero");
  await expect(hero).toHaveAttribute("data-tier", "high_risk");
  await expect(page.getByTestId("verdict-deadline")).toContainText("2 December 2027");
  console.log("VERDICT:", (await hero.innerText()).replace(/\s+/g, " "));
  console.log("WHAT-IF:", (await page.getByTestId("what-if").innerText()).replace(/\s+/g, " ").slice(0, 400));

  await page.locator('[data-cite="annex:III.4.a"]').first().click();
  await expect(page.getByTestId("citation-panel")).toContainText("recruitment or selection of natural persons");
  await page.keyboard.press("Escape");

  const [md] = await Promise.all([page.waitForEvent("download"), page.getByRole("button", { name: "Download Markdown" }).click()]);
  expect(md.suggestedFilename()).toMatch(/\.md$/);
  const [pdf] = await Promise.all([page.waitForEvent("download", { timeout: 60_000 }), page.getByRole("button", { name: "Download PDF" }).click()]);
  expect(pdf.suggestedFilename()).toMatch(/\.pdf$/);
});

test("emotion recognition at the call centre is prohibited", async ({ page }) => {
  await page.goto("/?example=emotion-recognition-call-centre");
  await untilResult(page);
  await expect(page.getByTestId("tier-hero").getByRole("heading", { level: 2 })).toHaveText("Prohibited practice");
});

test("customer service chatbot has transparency obligations", async ({ page }) => {
  await page.goto("/?example=customer-service-chatbot");
  await untilResult(page);
  await expect(page.getByTestId("tier-hero").getByRole("heading", { level: 2 })).toHaveText("Transparency obligations");
});

test("IT: payroll rules is out of scope with Italian reasoning", async ({ page }) => {
  await page.goto("/?example=payroll-rules&lang=it");
  await untilResult(page);
  await expect(page.getByTestId("tier-hero").getByRole("heading", { level: 2 })).toHaveText("Fuori dall'ambito di applicazione");
  await expect(page.getByTestId("reasoning-streaming")).toHaveCount(0, { timeout: 150_000 });
  await page.getByTestId("reasoning-toggle").click();
  await expect(page.getByTestId("reasoning-panel")).toContainText(/\b(il|della|che|non)\b/);
});
