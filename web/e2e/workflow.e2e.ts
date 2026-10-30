import type { Page } from "@playwright/test";
import { expect, settled, test, toast, USERS } from "./fixtures";

const RECEIPT = "e2e/assets/receipt.png";

/** Picks an option in a combobox by typing part of it. */
async function choose(page: Page, label: string | RegExp, text: string) {
  const box = page.getByRole("combobox", { name: label, exact: true });
  await box.click();
  await box.fill(text);
  await page.getByRole("option", { name: new RegExp(text) }).first().click();
}

/** The next-step panel on a claim page. */
const nextStep = (page: Page) => page.locator('section[aria-labelledby="next-step"]');

test("an expense goes from submitted to booked, and its owner sees every step", async ({ login, errors }) => {
  test.setTimeout(180_000);
  const description = `Fika till e2e ${Date.now()}`;

  // The member submits it, with a receipt.
  const member = await login(USERS.member);
  await member.goto("/expenses/new");
  await member.getByLabel("Vad gäller det?").fill(description);
  await choose(member, "Resultatställe", "Ada");
  await choose(member, "Sekundärt resultatställe", "Internt");
  await choose(member, "Budgetpost", "Fika");
  await member.getByLabel("Belopp").fill("123,45");
  await member.locator('input[type="file"]').first().setInputFiles(RECEIPT);
  await expect(member.getByText("receipt.png")).toBeVisible();
  await member.getByRole("button", { name: "Skicka in utlägget" }).click();
  await expect(member.getByRole("heading", { level: 1, name: description })).toBeVisible();
  const url = member.url();
  expect(url).toMatch(/\/expenses\/\d+$/);
  await expect(nextStep(member)).toContainText("Väntar på attest för Ada");

  // Editing the description alone keeps it where it is.
  await member.getByRole("link", { name: "Redigera" }).click();
  await member.getByLabel("Vad gäller det?").fill(`${description}!`);
  await member.getByRole("button", { name: "Spara ändringar" }).click();
  await expect(member.getByRole("heading", { level: 1, name: `${description}!` })).toBeVisible();

  // The kassör attests and confirms it from the claim page.
  const kassor = await login(USERS.kassor);
  await kassor.goto(url);
  await nextStep(kassor).getByRole("button", { name: "Attestera" }).click();
  expect(await toast(kassor)).toContain("Attesterat");
  await nextStep(kassor).getByRole("button", { name: "Bekräfta kvitto" }).click();
  await expect(nextStep(kassor)).toContainText("Klart för utbetalning");

  // Pays it out: the member's card on the pay page, then the bank details.
  await kassor.goto("/pay");
  await settled(kassor);
  const card = kassor.locator('[data-slot="card"]', { hasText: "Martin Median" }).first();
  await card.getByRole("button", { name: /Skapa utbetalning/ }).click();
  await kassor.getByRole("alertdialog").getByRole("button", { name: "Skapa utbetalning" }).click();
  await expect(kassor.getByText(/Utbetalning Data\d+ är skapad/)).toBeVisible();

  // Books it in (the fake) Fortnox, connecting first if needed.
  await kassor.goto("/fortnox");
  const connected = kassor.getByText("Fortnox är anslutet", { exact: true });
  const connect = kassor.getByRole("link", { name: "Anslut Fortnox" });
  await expect(connected.or(connect)).toBeVisible();
  if (await connect.isVisible()) {
    await connect.click();
    await expect(kassor.getByText("Fortnox är anslutet", { exact: true })).toBeVisible();
  }
  await kassor.goto(`${url}/account`);
  const account = kassor.getByRole("combobox", { name: "Rad 1: Konto" });
  await expect(account).toBeVisible();
  if ((await account.inputValue()) === "") await choose(kassor, "Rad 1: Konto", "5460");
  await expect(kassor.getByText("Balanserar och stämmer med totalen.")).toBeVisible();
  await kassor.getByRole("button", { name: "Bokför i Fortnox" }).click();
  expect(await toast(kassor)).toMatch(/Bokfört som E\d+/);

  // The member sees it booked, with the whole history.
  await member.goto(url);
  await expect(member.locator(".stamp")).toHaveText("Bokförd");
  const history = member.locator("ol").last();
  for (const step of ["Attesterar kvittodelen", "Jag har bekräftat kvittots giltighet.", "Betalade ut i betalning", "Bokförde med verifikationsnumret"]) {
    await expect(history, step).toContainText(step);
  }
  expect(errors).toEqual([]);
});

test("the claim form lists every problem at once and refuses files that aren't receipts", async ({ login }) => {
  const page = await login(USERS.member);
  await page.goto("/expenses/new");
  await page.getByRole("button", { name: "Skicka in utlägget" }).click();
  for (const problem of ["Skriv vad det gäller.", "Välj resultatställe.", "Fyll i ett belopp större än noll.", "Lägg till minst ett kvitto."]) {
    await expect(page.getByText(problem), problem).toBeVisible();
  }
  // An HTML file named like anything is refused by its contents.
  await page.locator('input[type="file"]').first().setInputFiles({
    name: "kvitto.png",
    mimeType: "image/png",
    buffer: Buffer.from("<html><script>alert(1)</script></html>"),
  });
  await expect(page.getByText("Bara bilder (JPEG, PNG, WebP, HEIC) och PDF fungerar.")).toBeVisible();
});

test("attesting your own expense is not offered, and the panel says why", async ({ login }) => {
  // diadat attests Sektionslokalsgruppen and has an expense there of her own.
  const page = await login(USERS.attester);
  await page.goto("/");
  await settled(page);
  await page.locator("tbody tr a", { hasText: "Kaffe och mjölk till Meta" }).first().click();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const panel = nextStep(page);
  if (await panel.getByText(/Väntar på attest/).isVisible()) {
    await expect(panel.getByRole("button", { name: "Attestera" })).toHaveCount(0);
    await expect(panel).toContainText("Du kan inte attestera dina egna utlägg");
  }
});
