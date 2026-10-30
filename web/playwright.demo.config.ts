import { defineConfig, devices } from "@playwright/test";

// Run against the isolated demo only; never resets the shared database.
export default defineConfig({
  testDir: "e2e-demo",
  workers: 1,
  expect: { timeout: 15_000 },
  timeout: 90_000,
  reporter: "list",
  use: {
    baseURL: process.env.CASHFLOW_DEMO_URL ?? "http://localhost:5180",
    locale: "sv-SE",
    timezoneId: "Europe/Stockholm",
    launchOptions: process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
    screenshot: "only-on-failure",
  },
  projects: [{ name: "demo-chromium", use: { ...devices["Desktop Chrome"] } }],
});
