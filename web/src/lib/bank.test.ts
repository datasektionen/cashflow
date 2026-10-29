import { expect, test } from "vitest";
import { formatBankAccount } from "./bank";

// Ported from Cashflow 3's bankAccount.test.ts (IBAN cases dropped: accounts
// are at most 13 digits).
test("joins clearing and account with a dash", () => {
  expect(formatBankAccount("8327", "1234567")).toBe("8327-1234567");
});

test("deduplicates a clearing number included in the account", () => {
  expect(formatBankAccount("8327", "83271234567")).toBe("8327-1234567");
});

test("keeps an account that merely starts with the clearing digits", () => {
  expect(formatBankAccount("8327", "8327123")).toBe("8327-8327123");
});

test("strips spaces, dashes and dots before formatting", () => {
  expect(formatBankAccount("8327-9", "123 456 789-0")).toBe("83279-1234567890");
});

test("returns whichever part is present", () => {
  expect(formatBankAccount("", "1234567")).toBe("1234567");
  expect(formatBankAccount("8327", "")).toBe("8327");
});
