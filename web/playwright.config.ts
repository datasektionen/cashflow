import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end tests against the running dev setup (make dev): the web app on
 * :5173, the Go server, the mock SSO/Hive and a fake Fortnox. The database is
 * reseeded before the run (global-setup), so every run starts from the same
 * claims. Run with `make e2e`.
 */
export default defineConfig({
  testDir: "e2e",
  testMatch: "**/*.e2e.ts",
  globalSetup: "./e2e/global-setup.ts",
  // One database: tests that change claims must not race each other.
  workers: 1,
  fullyParallel: false,
  retries: 0,
  // Dev mode compiles each page on its first visit, which can take seconds.
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL: process.env.CASHFLOW_WEB_URL ?? "http://localhost:5173",
    locale: "sv-SE",
    timezoneId: "Europe/Stockholm",
    trace: "retain-on-failure",
    // A Chromium already on the machine, if Playwright's own isn't installed.
    launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } }],
});
