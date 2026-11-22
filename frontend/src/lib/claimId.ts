import type { Expense, Invoice } from '#lib/api/types.ts';

/** The id shown on a claim: "Utlägg #12" for expenses, "CF 12" for invoices. */
export const claimIdLabel = (claim: Expense | Invoice, t: (key: string) => string) =>
	'expense_date' in claim ? `${t('expense')} #${claim.id}` : `CF ${claim.id}`;
