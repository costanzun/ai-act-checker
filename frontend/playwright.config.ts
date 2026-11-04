import { defineConfig, devices } from "@playwright/test";

// PW_BASE_URL: run against an already-running mock-mode server instead of starting one.
const external = process.env.PW_BASE_URL;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  reporter: [["list"]],
  use: { baseURL: external ?? "http://localhost:3101", colorScheme: "light", trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: external ? undefined : {
    command: "NEXT_PUBLIC_MOCK_API=1 NEXT_TELEMETRY_DISABLED=1 pnpm dev",
    url: "http://localhost:3101",
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
