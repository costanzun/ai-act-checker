import { defineConfig, devices } from "@playwright/test";

// PW_BASE_URL: run against an already-running mock-mode server instead of starting one.
// PW_PORT: start the mocked server on its own port and build dir, next to the live `pnpm dev` on 3101.
const external = process.env.PW_BASE_URL;
const port = process.env.PW_PORT ?? "3101";
const base = `http://localhost:${port}`;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  reporter: [["list"]],
  use: { baseURL: external ?? base, colorScheme: "light", trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: external ? undefined : {
    command: `NEXT_PUBLIC_MOCK_API=1 NEXT_TELEMETRY_DISABLED=1 ${port === "3101" ? "" : "NEXT_DIST_DIR=.next-mock "}pnpm exec next dev -p ${port}`,
    url: base,
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
