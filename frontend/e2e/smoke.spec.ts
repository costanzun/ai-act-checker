import { expect, test } from "@playwright/test";

test("one screen: example chip -> inline questions -> verdict -> citation -> IT -> dark", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Is your AI system regulated by the EU AI Act?");

  // One-click example runs immediately and shows progress
  await page.getByTestId("example-chip").first().click();
  await expect(page.getByTestId("progress")).toBeVisible();

  // Inline questions, same screen, chips
  const form = page.getByTestId("question-form");
  await expect(form).toBeVisible({ timeout: 15_000 });
  await expect(page).toHaveURL("/");
  await form.getByRole("radio", { name: "We use a system from a vendor" }).click();
  await form.getByRole("radio", { name: "Yes", exact: true }).click();
  await page.getByTestId("clarify-continue").click();

  // Verdict leads: tier, role, deadline, why with a citation
  const hero = page.getByTestId("tier-hero");
  await expect(hero).toBeVisible({ timeout: 20_000 });
  await expect(hero).toHaveAttribute("data-tier", "high_risk");
  await expect(hero.getByRole("heading", { level: 2 })).toHaveText("High risk");
  await expect(page.getByTestId("verdict-role")).toContainText("Deployer");
  await expect(page.getByTestId("verdict-deadline")).toContainText("2 December 2027");
  await expect(page.getByTestId("verdict-why").locator("[data-cite]").first()).toBeVisible();
  await expect(page.getByTestId("legal-notice")).toContainText("Not legal advice");

  // Order: verdict, must-do, documents, what-if
  const y = async (id: string) => (await page.getByTestId(id).boundingBox())!.y;
  expect(await y("tier-hero")).toBeLessThan(await y("must-do"));
  expect(await y("must-do")).toBeLessThan(await y("checklist"));
  expect(await y("checklist")).toBeLessThan(await y("what-if"));

  // Citation chip opens the panel with the law text
  await page.getByTestId("verdict-why").locator('[data-cite="annex:III.4.a"]').click();
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

test("old /assess links redirect; unknown saved result shows the not-found card", async ({ page }) => {
  await page.goto("/assess");
  await expect(page).toHaveURL("/");
  await expect(page.locator("#describe")).toBeVisible();
  await page.goto("/assess?id=does-not-exist");
  await expect(page.getByTestId("not-found")).toContainText("We could not find that result in this browser");
});

test("boolean questions are Yes / No / Not sure chips; unanswered counts as not sure", async ({ page }) => {
  await page.goto("/?example=cv-screening");
  const form = page.getByTestId("question-form");
  await expect(form).toBeVisible({ timeout: 15_000 });
  const boolQ = form.getByTestId("question").nth(1);
  await expect(boolQ.getByRole("radio")).toHaveCount(3);
  await expect(boolQ.getByRole("radio", { name: "Not sure" })).toBeVisible();
  // submit without answering anything: still gets an answer
  await page.getByTestId("clarify-continue").click();
  await expect(page.getByTestId("tier-hero")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("verdict-confidence")).toContainText("Medium");
});

test("must-do lists core duties first, the rest one click away; print shows everything", async ({ page }) => {
  await page.goto("/?example=customer-chatbot");
  await expect(page.getByTestId("result-view")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("obligations-count")).toContainText("2 obligations");
  await expect(page.getByTestId("obligation").locator("visible=true")).toHaveCount(1);
  await page.getByTestId("obligations-more").click();
  await expect(page.getByTestId("obligation").locator("visible=true")).toHaveCount(2);
  await page.getByTestId("obligations-more").click();

  await page.emulateMedia({ media: "print" });
  await expect(page.locator("header")).toBeHidden();
  await expect(page.locator("footer")).toBeHidden();
  await expect(page.getByRole("button", { name: "Download PDF" })).toHaveCount(0);
  await expect(page.getByTestId("obligation").locator("visible=true")).toHaveCount(2);
  await expect(page.getByTestId("reasoning-panel")).toBeVisible();
});

test("390px: no horizontal scroll on landing and result; toggles visible", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "IT", exact: true })).toBeVisible();
  await expect(page.getByTestId("theme-toggle")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.goto("/?example=customer-chatbot");
  await expect(page.getByTestId("result-view")).toBeVisible({ timeout: 20_000 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  // tier first, export below it on mobile; citation chips open the panel by tap
  const hero = (await page.getByTestId("tier-hero").getByRole("heading", { level: 2 }).boundingBox())!.y;
  const exp = (await page.getByRole("button", { name: "Download PDF" }).boundingBox())!.y;
  expect(hero).toBeLessThan(exp);
  await page.locator("[data-cite]").first().click();
  await expect(page.getByTestId("citation-panel")).toBeVisible();
});

test("'/' focuses the text box; Cmd+Enter submits", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("example-chip").first()).toBeVisible(); // hydrated
  await page.keyboard.press("/");
  await expect(page.locator("#describe")).toBeFocused();
  await page.keyboard.type("Our IT team uses a machine-learning spam filter for company email.");
  await page.keyboard.press("ControlOrMeta+Enter");
  await expect(page.getByTestId("tier-hero")).toHaveAttribute("data-tier", "minimal_risk", { timeout: 20_000 });
});

test("overlay badge for Art. 50 in the verdict, GPAI for a model provider", async ({ page }) => {
  await page.goto("/?example=customer-chatbot");
  await expect(page.locator('[data-testid="tier-hero"] [data-overlay="transparency_art50"]')).toBeVisible({ timeout: 20_000 });
  await page.goto("/?example=gpai-model");
  await expect(page.locator('[data-testid="tier-hero"] [data-overlay="gpai"]')).toBeVisible({ timeout: 20_000 });
});

test("conditional obligations are labelled under 'Also check'", async ({ page }) => {
  await page.goto("/?example=cv-screening");
  const form = page.getByTestId("question-form");
  await expect(form).toBeVisible({ timeout: 15_000 });
  await form.getByRole("radio", { name: "We use a system from a vendor" }).click();
  await page.getByTestId("clarify-continue").click();
  await page.getByTestId("obligations-more").click({ timeout: 20_000 });
  const extra = page.getByTestId("conditional-group");
  await expect(extra).toContainText("Conditional — check whether this applies to you");
  await expect(extra).toContainText("Fundamental rights impact assessment");
});

test("what would change the answer: one click re-checks with that answer", async ({ page }) => {
  await page.goto("/?example=cv-screening");
  await expect(page.getByTestId("question-form")).toBeVisible({ timeout: 15_000 });
  await page.getByTestId("clarify-continue").click();
  const item = page.locator('[data-testid="what-if-item"][data-fact="decision_impact"]');
  await expect(item).toContainText("Minimal risk", { timeout: 20_000 });
  await item.getByTestId("what-if-apply").click();
  await expect(page.getByTestId("tier-hero")).toHaveAttribute("data-tier", "minimal_risk", { timeout: 20_000 });
  // no second round of questions
  await expect(page.getByTestId("question-form")).toHaveCount(0);
});

test("reasoning streams behind the verdict and opens on demand; copy link and new check", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/?example=customer-chatbot");
  await expect(page.getByTestId("tier-hero")).toBeVisible({ timeout: 20_000 });
  await expect(page.getByTestId("reasoning-streaming")).toHaveCount(0, { timeout: 20_000 });
  await page.getByTestId("reasoning-toggle").click();
  await expect(page.getByTestId("reasoning-panel")).toContainText("talks directly to customers");
  await page.getByRole("button", { name: "Copy link" }).first().click();
  const link = await page.evaluate(() => navigator.clipboard.readText());
  expect(link).toMatch(/\/\?id=mock-customer-chatbot-en/);
  await page.goto(link);
  await expect(page.getByTestId("tier-hero")).toHaveAttribute("data-tier", "limited_risk");
  await page.getByTestId("new-check").click();
  await expect(page.locator("#describe")).toHaveValue("");
});

test("each verdict has its own dog scene; animations stop under reduced motion", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("mascots").getByRole("img")).toHaveCount(2);
  await page.goto("/?example=emotion-workplace");
  const hero = page.getByTestId("tier-hero");
  await expect(hero).toHaveAttribute("data-tier", "prohibited", { timeout: 20_000 });
  await expect(hero.getByRole("img", { name: /doberman on guard.*stop sign/ })).toBeVisible();
  await page.goto("/?example=spam-filter");
  await expect(page.getByTestId("tier-hero").getByRole("img", { name: /schnauzer smiling/ })).toBeVisible({ timeout: 20_000 });

  await page.emulateMedia({ reducedMotion: "reduce" });
  const anim = await page.locator(".px-twinkle").first().evaluate((el) => getComputedStyle(el).animationName);
  expect(anim).toBe("none");
});

test("model picker: header pill opens 'Who does the sniffing?' with subscriptions, API keys and local", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("model-pill").click();
  const dialog = page.getByTestId("model-dialog");
  await expect(dialog).toContainText("Who does the sniffing?");
  for (const id of ["claude_cli", "codex_cli", "anthropic_api", "openai_api", "nvidia", "local_mlx"]) {
    await expect(page.getByTestId(`model-${id}`)).toBeVisible();
  }
  await expect(page.getByTestId("model-claude_cli")).toHaveAttribute("data-active", "true");
  await expect(page.getByTestId("model-claude_cli")).toContainText("Claude Code found");

  // Codex missing: copyable install + login commands, "Use this" disabled
  await page.getByTestId("model-codex_cli").getByRole("button").first().click();
  await expect(page.getByTestId("model-codex_cli")).toContainText("Codex CLI is not installed");
  await expect(page.getByRole("button", { name: "Copy command: codex login" })).toBeVisible();
  await expect(page.getByTestId("use-codex_cli")).toBeDisabled();

  // API key: password field, model suggestions, Test disabled until a key is saved
  await page.getByTestId("model-anthropic_api").getByRole("button").first().click();
  await expect(page.getByTestId("key-anthropic_api")).toHaveAttribute("type", "password");
  await expect(page.getByTestId("test-anthropic_api")).toBeDisabled();
  await page.getByRole("button", { name: "claude-opus-5-5" }).click();
  await expect(page.getByTestId("model-input-anthropic_api")).toHaveValue("claude-opus-5-5");

  // Test the active subscription
  await page.getByTestId("model-claude_cli").getByRole("button").first().click();
  await page.getByTestId("test-claude_cli").click();
  await expect(page.getByTestId("model-test")).toContainText("Connected");
  await page.getByRole("button", { name: "Close" }).click();
  await expect(page.getByTestId("model-dialog")).toBeHidden();
});

test("model picker in Italian, and the pill fits a 375px phone", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("/?lang=it");
  const pill = page.getByTestId("model-pill");
  await expect(pill).toBeVisible();
  await expect(page.getByTestId("theme-toggle")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(375);
  await pill.click();
  await expect(page.getByTestId("model-dialog")).toContainText("Chi fiuta la legge?");
  await expect(page.getByTestId("model-codex_cli")).toContainText("Abbonamento ChatGPT");
  const box = (await page.getByTestId("model-dialog").boundingBox())!;
  expect(box.x).toBeGreaterThanOrEqual(0);
  expect(box.x + box.width).toBeLessThanOrEqual(375);
});
