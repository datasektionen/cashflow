import { expect, settled, test, USERS } from "./fixtures";

test("the filter panel narrows the list, shows chips, and is kept in the address", async ({ login, errors }) => {
  const page = await login(USERS.kassor);
  await page.goto("/claims");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  const all = await page.locator("tbody tr").count();

  await page.getByRole("button", { name: /^Filter/ }).click();
  const panel = page.getByRole("dialog");
  await panel.getByRole("group", { name: "Betalt" }).getByRole("button", { name: "Ja" }).click();
  await panel.getByRole("group", { name: "Flaggat" }).getByRole("button", { name: "Nej" }).click();
  await panel.getByRole("button", { name: "Visa" }).click();
  await expect(page).toHaveURL(/paid=true/);
  await expect(page).toHaveURL(/flagged=false/);
  await expect(page.getByRole("button", { name: "Betalt: Ja" })).toBeVisible();
  await settled(page);
  const paid = await page.locator("tbody tr").count();
  expect(paid).toBeLessThan(all);
  for (const status of await page.locator("tbody tr td:last-child").allInnerTexts()) {
    expect(["Betalt", "Bokfört"]).toContain(status.trim());
  }

  // Reloading keeps the filters; a chip removes one.
  await page.reload();
  await expect(page.getByRole("button", { name: "Betalt: Ja" })).toBeVisible();
  await page.getByRole("button", { name: "Betalt: Ja" }).click();
  await expect(page).not.toHaveURL(/paid=true/);
  await expect(page.getByRole("button", { name: /^Filter/ })).toContainText("1");
  expect(errors).toEqual([]);
});

test("search finds a claim by number and the keyboard opens it", async ({ login }) => {
  const page = await login(USERS.kassor);
  await page.goto("/claims");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await page.keyboard.press("/");
  await page.keyboard.type("#3");
  await expect(page).toHaveURL(/q=/);
  await settled(page);
  await page.locator("body").click({ position: { x: 5, y: 5 } });
  await page.keyboard.press("j");
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/\/(expenses|invoices)\/3$/);
});

test("a queue is worked through with 'Nästa i kön'", async ({ login }) => {
  const page = await login(USERS.kassor);
  await page.goto("/confirm");
  await settled(page);
  const first = page.locator("tbody tr a").first();
  const firstTitle = await first.innerText();
  await first.click();
  await expect(page.getByRole("heading", { level: 1, name: firstTitle })).toBeVisible();
  await page.getByRole("link", { name: "Nästa i kön" }).click();
  await expect(page.getByRole("heading", { level: 1 })).not.toHaveText(firstTitle);
  await expect(page).toHaveURL(/queue=confirm/);
});

test("a cost centre chip filters the list", async ({ login }) => {
  const page = await login(USERS.kassor);
  await page.goto("/claims");
  await expect(page.locator("tbody tr").first()).toBeVisible();
  await page.locator("tbody tr").first().getByRole("button").first().click();
  await expect(page).toHaveURL(/cc=/);
  const cc = new URL(page.url()).searchParams.get("cc") ?? "";
  await expect(page.getByRole("button", { name: `Resultatställe: ${cc}` })).toBeVisible();
});
