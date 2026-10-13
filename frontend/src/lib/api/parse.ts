import { SEK } from 'dinero.js';
import { dineroFromDecimal } from '$lib/money';
import type {
	Claim,
	Expense,
	ExpensePart,
	Invoice,
	InvoicePart,
	LeaderboardEntry,
	Payment,
	PendingPayment
} from '$lib/api/types';
import type { MonthlyStatistics, YearlyStatistics } from '$lib/api/resources/stats';

// The API returns money as decimal strings. These types describe the raw responses,
// and the parse functions convert them to Dinero objects as early as possible.

/** Replaces the given money fields of `T` with the decimal strings the API sends. */
type WithDecimalStrings<T, K extends keyof T> = Omit<T, K> & { [P in K]: string };

export type APIExpensePart = WithDecimalStrings<ExpensePart, 'amount'>;
export type APIInvoicePart = WithDecimalStrings<InvoicePart, 'amount'>;
export type APIPayment = WithDecimalStrings<Payment, 'total'>;
export type APIPendingPayment = WithDecimalStrings<PendingPayment, 'total'>;
export type APILeaderboardEntry = WithDecimalStrings<LeaderboardEntry, 'expense_total'>;
export type APIMonthlyStatistics = WithDecimalStrings<
	MonthlyStatistics,
	'expense_total' | 'invoice_total'
>;
export type APIYearlyStatistics = Omit<YearlyStatistics, 'months'> & {
	months: APIMonthlyStatistics[];
};

export type APIExpense = Omit<Expense, 'parts' | 'payment'> & {
	parts: APIExpensePart[];
	payment: APIPayment | null;
};
export type APIInvoice = Omit<Invoice, 'parts'> & {
	parts: APIInvoicePart[];
};

type ExpenseClaim = Extract<Claim, { type: 'expense' }>;
type InvoiceClaim = Extract<Claim, { type: 'invoice' }>;
export type APIClaim =
	| (Omit<ExpenseClaim, 'parts' | 'amount'> & { parts: APIExpensePart[]; amount: string })
	| (Omit<InvoiceClaim, 'parts' | 'amount'> & { parts: APIInvoicePart[]; amount: string });

const toDinero = (value: string) => dineroFromDecimal(value, SEK);

export function parseExpensePart(part: APIExpensePart): ExpensePart {
	return { ...part, amount: toDinero(part.amount) };
}

export function parseInvoicePart(part: APIInvoicePart): InvoicePart {
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
		parts: expense.parts.map(parseExpensePart)
	};
}

export function parseInvoice(invoice: APIInvoice): Invoice {
	return {
		...invoice,
		parts: invoice.parts.map(parseInvoicePart)
	};
}

export function parseClaim(claim: APIClaim): Claim {
	const amount = toDinero(claim.amount);
	return claim.type === 'expense'
		? { ...claim, amount, parts: claim.parts.map(parseExpensePart) }
		: { ...claim, amount, parts: claim.parts.map(parseInvoicePart) };
}

export function parseLeaderboardEntry(entry: APILeaderboardEntry): LeaderboardEntry {
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
