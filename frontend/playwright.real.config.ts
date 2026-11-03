import { defineConfig, devices } from "@playwright/test";

// Runs against the REAL backend (http://localhost:8101 must already be up). Mock suite: playwright.config.ts
export default defineConfig({
  testDir: "./e2e-real",
  timeout: 180_000,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: { baseURL: "http://localhost:3101", colorScheme: "light", trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "NEXT_PUBLIC_API_URL=http://localhost:8101 NEXT_TELEMETRY_DISABLED=1 pnpm dev",
    url: "http://localhost:3101",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
