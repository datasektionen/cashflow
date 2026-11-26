import { SEK, toDecimal } from 'dinero.js';
import { dineroFromDecimal } from '#lib/money.ts';
import type {
	Claim,
	ClaimPart,
	Expense,
	Invoice,
	LeaderboardEntry,
	PartCreateUpdate,
	Payment,
	PendingPayment
} from '#lib/api/types.ts';
import type {
	MonthlyStatistics,
	UserLeaderboardStats,
	YearlyStatistics
} from '#lib/api/resources/stats.ts';

// The API returns money as decimal strings. These types describe the raw responses,
// and the parse functions convert them to Dinero objects as early as possible.

/** Replaces the given money fields of `T` with the decimal strings the API sends. */
type WithDecimalStrings<T, K extends keyof T> = Omit<T, K> & { [P in K]: string };

type APIClaimPart = WithDecimalStrings<ClaimPart, 'amount'>;
export type APIPayment = WithDecimalStrings<Payment, 'total'>;
type APIPendingPayment = WithDecimalStrings<PendingPayment, 'total'>;
export type APILeaderboardEntry = WithDecimalStrings<LeaderboardEntry, 'expense_total'>;
export type APIUserLeaderboardStats = WithDecimalStrings<UserLeaderboardStats, 'expense_total'>;
type APIMonthlyStatistics = WithDecimalStrings<
	MonthlyStatistics,
	'expense_total' | 'invoice_total'
>;
export type APIYearlyStatistics = Omit<YearlyStatistics, 'months'> & {
	months: APIMonthlyStatistics[];
};

export type APIExpense = Omit<Expense, 'parts' | 'payment'> & {
	parts: APIClaimPart[];
	payment: APIPayment | null;
};
export type APIInvoice = Omit<Invoice, 'parts'> & { parts: APIClaimPart[] };

type ExpenseClaim = Extract<Claim, { type: 'expense' }>;
type InvoiceClaim = Extract<Claim, { type: 'invoice' }>;
type APIClaim =
	| (Omit<ExpenseClaim, 'parts' | 'amount'> & { parts: APIClaimPart[]; amount: string })
	| (Omit<InvoiceClaim, 'parts' | 'amount'> & { parts: APIClaimPart[]; amount: string });

const toDinero = (value: string) => dineroFromDecimal(value, SEK);

function parseClaimPart(part: APIClaimPart): ClaimPart {
	return { ...part, amount: toDinero(part.amount) };
}

export function parsePayment(payment: APIPayment): Payment {
	return { ...payment, total: toDinero(payment.total) };
}

export function parsePendingPayment(pending: APIPendingPayment): PendingPayment {
	return { ...pending, total: toDinero(pending.total) };
}

export function parseExpense(expense: APIExpense): Expense {
	return {
		...expense,
		payment: expense.payment && parsePayment(expense.payment),
		parts: expense.parts.map(parseClaimPart)
	};
}

export function parseInvoice(invoice: APIInvoice): Invoice {
	return { ...invoice, parts: invoice.parts.map(parseClaimPart) };
}

export function parseClaim(claim: APIClaim): Claim {
	return { ...claim, amount: toDinero(claim.amount), parts: claim.parts.map(parseClaimPart) };
}

export function parseLeaderboardEntry<T extends APILeaderboardEntry>(
	entry: T
): Omit<T, 'expense_total'> & Pick<LeaderboardEntry, 'expense_total'> {
	return { ...entry, expense_total: toDinero(entry.expense_total) };
}

export function parseYearlyStatistics(stats: APIYearlyStatistics): YearlyStatistics {
	return {
		...stats,
		months: stats.months.map((month) => ({
			...month,
			expense_total: toDinero(month.expense_total),
			invoice_total: toDinero(month.invoice_total)
		}))
	};
}

/** Builds the multipart body for creating or updating an expense or invoice. */
export function claimFormData({
	parts,
	files,
	delete_files,
	...fields
}: {
	parts?: PartCreateUpdate[];
	files?: File[];
	delete_files?: number[];
}): FormData {
	const body = new FormData();
	for (const [key, value] of Object.entries(fields)) {
		if (value !== undefined) body.append(key, String(value));
	}
	if (parts) {
		const decimalParts = parts.map((part) => ({ ...part, amount: toDecimal(part.amount) }));
		body.append('parts', JSON.stringify(decimalParts));
	}
	if (delete_files) body.append('delete_files', JSON.stringify(delete_files));
	for (const file of files ?? []) body.append('files', file, file.name);
	return body;
}
