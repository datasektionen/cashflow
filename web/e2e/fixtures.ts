import AxeBuilder from "@axe-core/playwright";
import { test as base, expect, type Page } from "@playwright/test";

/** The mock SSO's users (compose.next.yaml) and what they may do. */
export const USERS = {
  /** Kassör: every permission. */
  kassor: "turetek",
  /** Attests Sektionslokalsgruppen, books everything. */
  attester: "diadat",
  /** No permissions: their own claims only. */
  member: "marmed",
  /** Books Mottagningen 2026 only. */
  accountant: "bilbek",
  /** Sees everything, may do nothing. */
  viewer: "sauron",
} as const;

type Fixtures = {
  /** Logs in through the mock SSO, as a user from USERS. */
  login: (username: string) => Promise<Page>;
  /** Console errors and uncaught exceptions seen during the test. */
  errors: string[];
};

export const test = base.extend<Fixtures>({
  errors: async ({}, use) => {
    await use([]);
  },
  login: async ({ browser, errors }, use) => {
    const contexts: Awaited<ReturnType<typeof browser.newContext>>[] = [];
    await use(async (username) => {
      const context = await browser.newContext();
      contexts.push(context);
      const page = await context.newPage();
      page.on("pageerror", (e) => errors.push(`${username}: ${e.message}`));
      page.on("console", (m) => {
        // 4xx answers are the app's business (the login redirect, refused actions).
        if (m.type() === "error" && !/status of 4\d\d/.test(m.text())) errors.push(`${username}: ${m.text()}`);
      });
      await page.goto("/");
      await page.waitForURL(/7003\/login/);
      await page.fill('input[name="kthid"]', username);
      await page.click('button[type="submit"]');
      await page.waitForURL((url) => url.pathname === "/");
      await page.getByRole("heading", { level: 1 }).waitFor();
      return page;
    });
    for (const context of contexts) await context.close();
  },
});

export { expect };

/** The last toast's text. */
export async function toast(page: Page) {
  const t = page.locator("[data-sonner-toast]").last();
  await t.waitFor();
  return (await t.innerText()).replace(/\s+/g, " ").trim();
}

/** Accessibility violations axe finds, serious and critical only. */
export async function accessibilityProblems(page: Page) {
  const { violations } = await new AxeBuilder({ page }).exclude("[data-tsd-source] iframe").analyze();
  return violations
    .filter((v) => v.impact === "serious" || v.impact === "critical")
    .map(
      (v) =>
        `${v.id}: ${v.help} (${v.nodes
          .map((n) => n.target.join(" "))
          .slice(0, 3)
          .join(", ")})`,
    );
}

/** Whether the page scrolls: vertical overflow beyond the viewport, and any horizontal overflow. */
export async function overflow(page: Page) {
  return page.evaluate(() => ({
    vertical: document.documentElement.scrollHeight - innerHeight,
    horizontal: document.documentElement.scrollWidth - innerWidth,
  }));
}

/** Waits until nothing is loading: no skeletons, nothing marked busy. */
export async function settled(page: Page) {
  await expect(page.locator('[data-slot="skeleton"], [aria-busy="true"]')).toHaveCount(0, { timeout: 10_000 });
}
