import type { Page } from "@playwright/test";
import { expect, expectToast, test, USERS } from "./fixtures";

async function choose(page: Page, label: string, text: string) {
  const box = page.getByRole("combobox", { name: label, exact: true });
  await box.click();
  await box.fill(text);
  await page
    .getByRole("option", { name: new RegExp(text) })
    .first()
    .click();
}

const nextStep = (page: Page) => page.locator('section[aria-labelledby="next-step"]');

test("an invoice is attested, paid and recorded with a voucher number", async ({ login, errors }) => {
  test.setTimeout(120_000);
  const supplier = `Leverantör e2e ${Date.now()}`;

  // diadat attests Sektionslokalsgruppen; her own invoices she may attest.
  const attester = await login(USERS.attester);
  await attester.goto("/invoices/new");
  await attester.getByLabel("Vad gäller det?").fill(supplier);
  await attester.getByLabel("Fakturanummer").fill("F-2026-001");
  await attester.getByLabel(/Förfallodatum/).fill("2026-12-31");
  await choose(attester, "Resultatställe", "Sektionslokalsgruppen");
  await attester.getByRole("combobox", { name: "Sekundärt resultatställe", exact: true }).click();
  await attester.getByRole("option").first().click();
  await attester.getByRole("combobox", { name: "Budgetpost", exact: true }).click();
  await attester.getByRole("option").first().click();
  await attester.getByLabel("Belopp").fill("2 500");
  await attester.locator('input[type="file"]').first().setInputFiles("e2e/assets/receipt.png");
  await attester.getByRole("button", { name: "Skicka in fakturan" }).click();
  await expect(attester.getByRole("heading", { level: 1, name: supplier })).toBeVisible();
  const url = attester.url();
  expect(url).toMatch(/\/invoices\/\d+$/);
  await expect(attester.getByText("F-2026-001")).toBeVisible();

  // Her own invoice: she may attest it (unlike her own expenses).
  await nextStep(attester).getByRole("button", { name: "Attestera" }).click();
  await expectToast(attester, "Attesterat");
  await expect(nextStep(attester)).toContainText("Klar att betalas");

  // The kassör pays it from the claim page; invoices have no receipt to confirm.
  const kassor = await login(USERS.kassor);
  await kassor.goto(url);
  await expect(nextStep(kassor).getByRole("button", { name: "Bekräfta kvitto" })).toHaveCount(0);
  await nextStep(kassor).getByRole("button", { name: "Markera som betald" }).click();
  await expectToast(kassor, "Fakturan är markerad som betald");

  // Booked by hand in Fortnox: record the voucher number from the booking page.
  await kassor.goto(`${url}/account`);
  // No invoice date was given: the voucher is dated by the payment instead.
  await expect(kassor.locator("dd", { hasText: /^(\d{4}-\d{2}-\d{2}|\d+ \w+\. \d{4})$/ }).first()).toBeVisible();
  // With Fortnox connected the manual form is folded away; without, it shows.
  const manual = kassor.getByRole("button", { name: "Redan bokfört i Fortnox?" });
  const field = kassor.getByRole("textbox", { name: "Verifikationsnummer" });
  await expect(manual.or(field).first()).toBeVisible();
  if (await manual.isVisible()) await manual.click();
  await kassor.getByRole("textbox", { name: "Verifikationsnummer" }).fill("u77");
  await kassor.getByRole("button", { name: "Spara numret" }).click();
  await expectToast(kassor, "Bokfört som U77");

  // It is on the vouchers page, found by its number.
  await kassor.goto("/vouchers");
  await kassor.getByRole("searchbox").fill("U77");
  await expect(kassor.locator("tbody tr", { hasText: supplier })).toHaveCount(1);
  expect(errors).toEqual([]);
});
