import { accessibilityProblems, expect, settled, test, USERS } from "./fixtures";

// Every page each kind of user reaches from the sidebar loads, has a heading,
// has no serious accessibility problems and throws nothing.
for (const [role, username] of Object.entries(USERS)) {
  test(`every sidebar page works for the ${role}`, async ({ login, errors }) => {
    test.setTimeout(120_000);
    const page = await login(username);
    const links = await page
      .locator('[data-sidebar="menu-button"][href]')
      .evaluateAll((as) => as.map((a) => a.getAttribute("href") ?? ""));
    expect(links.length).toBeGreaterThan(2);
    for (const href of links) {
      await page.goto(href);
      await expect(page.getByRole("heading", { level: 1 }), href).toBeVisible();
      // Let lists and queries settle before judging the page.
      await settled(page);
      expect(await accessibilityProblems(page), `${href} for ${username}`).toEqual([]);
    }
    expect(errors).toEqual([]);
  });
}

test("a member sees only their own claims and no admin pages in the sidebar", async ({ login }) => {
  const page = await login(USERS.member);
  const nav = page.locator('[data-sidebar="menu"]');
  for (const admin of ["Attestera", "Betala", "Bokför", "Personer", "Verifikationer"]) {
    await expect(nav.getByText(admin, { exact: true })).toHaveCount(0);
  }
  await expect(page.locator("tbody tr").first()).toBeVisible();
  const owners = await page.locator("tbody tr").count();
  expect(owners).toBeGreaterThan(0);
});

test("admin pages opened by address explain themselves to a member", async ({ login, errors }) => {
  const page = await login(USERS.member);
  for (const path of ["/attest", "/pay", "/account", "/users", "/users/turetek", "/vouchers", "/fortnox"]) {
    await page.goto(path);
    await expect(page.getByRole("heading", { level: 1 }), path).toBeVisible();
    await settled(page);
    // A plain explanation, never a page that loads forever or a blank one.
    await expect(page.getByText("Du har inte tillgång hit"), path).toBeVisible();
  }
  expect(errors).toEqual([]);
});
