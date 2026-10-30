import { expect, type Page, test } from "@playwright/test";

async function login(page: Page, user: string) {
  await page.goto("/login");
  await page.locator(`button[value="${user}"]`).click();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await expect(page.getByRole("link", { name: "Byt testanvändare" })).toBeVisible();
}
async function choose(page: Page, label: string, text: string) {
  const field = page.getByRole("combobox", { name: label, exact: true });
  await field.click();
  await field.fill(text);
  await page
    .getByRole("option", { name: new RegExp(text) })
    .first()
    .click();
}

test("all six identities have their own server-enforced capabilities", async ({ browser, baseURL }) => {
  const expected = {
    turetek: { pay: true, attestAll: true, accountingAll: true, viewAll: true, manageFortnox: true },
    diadat: { pay: false, attestAny: true, attestAll: false, accountingAll: true },
    bilbek: { pay: false, attestAny: false, accountingAny: true, accountingAll: false },
    sauron: { pay: false, attestAny: false, accountingAny: false, viewAll: true },
    marmed: { pay: false, attestAny: false, accountingAny: false, viewAll: false },
    jobjav: { pay: false, attestAny: false, accountingAny: false, viewAll: false },
  };
  for (const [user, capabilities] of Object.entries(expected)) {
    const context = await browser.newContext({ baseURL, locale: "sv-SE" });
    const page = await context.newPage();
    await login(page, user);
    const me = await context.request.post("/api/cashflow.user.v1.UserService/GetMe", { data: {} });
    expect(me.status()).toBe(200);
    const data = await me.json();
    expect(data.user.username).toBe(user);
    for (const [key, value] of Object.entries(capabilities))
      expect(Boolean(data.capabilities[key]), `${user}: ${key}`).toBe(value);
    if (!capabilities.pay) {
      const denied = await context.request.post("/api/cashflow.payment.v1.PaymentService/CreatePayout", {
        data: { expenseNumbers: ["1"] },
      });
      expect(denied.status()).toBe(403);
      await page.goto("/pay");
      await expect(page.getByRole("button", { name: /Skapa utbetalning/ })).toHaveCount(0);
    }
    await page.getByRole("link", { name: "Byt testanvändare" }).click();
    await expect(page.locator('button[name="user"]')).toHaveCount(6);
    await context.close();
  }
});

test("a member submits a receipt and the treasurer approves it using only mocks", async ({ browser, baseURL }) => {
  test.setTimeout(150_000);
  const errors: string[] = [];
  const context = await browser.newContext({ baseURL, locale: "sv-SE" });
  const page = await context.newPage();
  page.on("pageerror", (error) => errors.push(error.message));
  await login(page, "marmed");
  await page.goto("/expenses/new");
  const description = `Demo smoke ${Date.now()}`;
  await page.getByLabel("Vad gäller det?").fill(description);
  await choose(page, "Resultatställe", "Ada");
  await choose(page, "Sekundärt resultatställe", "Kärnverksamhet");
  await choose(page, "Budgetpost", "Fika");
  await page.getByLabel("Belopp").fill("12,34");
  const uploaded = page.waitForResponse(
    (response) => response.url().endsWith("/files") && response.request().method() === "POST",
  );
  await page.locator('input[type="file"]').first().setInputFiles("e2e/assets/receipt.png");
  expect((await uploaded).status()).toBe(200);
  await expect(page.getByText("receipt.png")).toBeVisible();
  const submitted = page.waitForResponse((response) => response.url().endsWith("/CreateClaim"));
  await page.getByRole("button", { name: "Skicka in utlägget" }).click();
  const created = await submitted;
  expect(created.ok(), await created.text()).toBe(true);
  await expect(page.getByRole("heading", { level: 1, name: description })).toBeVisible();
  const claimURL = page.url();
  expect(claimURL).toMatch(/\/expenses\/\d+$/);
  const panel = page.locator('section[aria-labelledby="next-step"]');
  await expect(panel.getByRole("button", { name: "Attestera", exact: true })).toHaveCount(0);
  await page.getByRole("link", { name: "Byt testanvändare" }).click();
  await page.locator('button[value="turetek"]').click();
  await page.goto(claimURL);
  await panel.getByRole("button", { name: "Attestera", exact: true }).click();
  await expect(page.locator("[data-sonner-toast]", { hasText: "Attesterat" }).first()).toBeVisible();
  await panel.getByRole("button", { name: "Bekräfta kvitto" }).click();
  await expect(panel).toContainText("Klart för utbetalning");
  await page.goto("/fortnox");
  const connected = page.getByText("Fortnox är anslutet", { exact: true });
  const connect = page.getByRole("link", { name: "Anslut Fortnox" });
  await expect(connected.or(connect)).toBeVisible();
  if (await connect.isVisible()) await connect.click();
  await expect(connected).toBeVisible();
  const payout = await context.request.post("/api/cashflow.payment.v1.PaymentService/CreatePayout", {
    data: { expenseNumbers: [claimURL.split("/").at(-1)] },
  });
  expect(payout.ok(), await payout.text()).toBe(true);
  await page.goto(`${claimURL}/account`);
  const account = page.getByRole("combobox", { name: "Rad 1: Konto" });
  await expect(account).toBeVisible();
  if ((await account.inputValue()) === "") await choose(page, "Rad 1: Konto", "5460");
  await expect(page.getByText("Balanserar och stämmer med totalen.")).toBeVisible();
  await page.getByRole("button", { name: "Bokför i Fortnox" }).click();
  await expect(page.locator("[data-sonner-toast]", { hasText: /Bokfört som E\d+/ }).first()).toBeVisible();
  expect(errors).toEqual([]);
  await context.close();
});

test("the role chooser works on a phone", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/login");
  await expect(page.locator('button[name="user"]')).toHaveCount(6);
  expect(await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)).toBeLessThanOrEqual(0);
  await page.locator('button[value="jobjav"]').click();
  await expect(page.getByRole("link", { name: "Byt testanvändare" })).toBeVisible();
});
