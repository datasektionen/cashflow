import { devices } from "@playwright/test";
import { accessibilityProblems, expect, overflow, settled, test, USERS } from "./fixtures";

// The main flows fit a 1366×768 laptop screen without scrolling.
const COMPACT = [
  "/",
  "/expenses/new",
  "/expenses/1",
  "/expenses/16/account",
  "/stats",
  "/budget?cc=0",
  "/users/bilbek",
];

test("main pages fit a 1366×768 screen", async ({ login }) => {
  test.setTimeout(90_000);
  const page = await login(USERS.kassor);
  await page.setViewportSize({ width: 1366, height: 768 });
  for (const path of COMPACT) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
    await settled(page);
    const { vertical, horizontal } = await overflow(page);
    expect(vertical, `${path} scrolls by ${vertical}px`).toBeLessThanOrEqual(0);
    expect(horizontal, `${path} scrolls sideways`).toBeLessThanOrEqual(0);
  }
});

test("on a phone nothing scrolls sideways", async ({ browser }) => {
  test.setTimeout(90_000);
  const context = await browser.newContext({ ...devices["iPhone 13"], locale: "sv-SE" });
  const page = await context.newPage();
  await page.goto("/");
  await page.waitForURL(/7003\/login/);
  await page.fill('input[name="kthid"]', USERS.kassor);
  await page.click('button[type="submit"]');
  await page.waitForURL((url) => url.pathname === "/");
  for (const path of [
    "/",
    "/attest",
    "/expenses/1",
    "/expenses/new",
    "/pay",
    "/expenses/16/account",
    "/stats",
    "/budget?cc=0",
  ]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
    await settled(page);
    expect((await overflow(page)).horizontal, `${path} scrolls sideways`).toBeLessThanOrEqual(0);
  }
  await context.close();
});

test("dark mode and English read well too", async ({ login, errors }) => {
  test.setTimeout(90_000);
  const page = await login(USERS.kassor);
  await page.getByRole("button", { name: /Ture Teknolog/ }).click();
  // The menu stays open while choosing, so both choices are made in one go.
  await page.getByRole("menuitemradio", { name: "Mörkt" }).click();
  await page.getByRole("menuitemradio", { name: "English" }).click();
  await page.keyboard.press("Escape");
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Your expenses");
  for (const path of ["/", "/expenses/1", "/claims", "/stats", "/expenses/new"]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 }).first()).toBeVisible();
    await settled(page);
    expect(await accessibilityProblems(page), path).toEqual([]);
  }
  expect(errors).toEqual([]);
});
