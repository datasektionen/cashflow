/**
 * Formats bank details as `CLEARING-ACCOUNT`. Accounts migrated from
 * Cashflow 3 sometimes repeat the clearing number; that prefix is dropped.
 */
export function formatBankAccount(clearingNumber: string, bankAccount: string): string {
  const clearing = clearingNumber.replace(/[\s.-]/g, "");
  const account = bankAccount.replace(/[\s.-]/g, "");
  if (!clearing) return account;
  if (!account) return clearing;

  // Swedish account numbers are at least 6 digits after the clearing number,
  // so a shorter remainder means the matching prefix belongs to the account itself.
  const rest =
    account.startsWith(clearing) && account.length - clearing.length >= 6 ? account.slice(clearing.length) : account;
  return `${clearing}-${rest}`;
}
