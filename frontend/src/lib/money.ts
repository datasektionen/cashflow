/**
 * Converts a decimal amount string (e.g. from a Django DecimalField) to
 * integer cents via BigInt, so summing many amounts can't drift the way
 * repeated `parseFloat` + binary floating-point addition does.
 */
export function toCents(amount: string): bigint {
	const trimmed = amount.trim();
	const negative = trimmed.startsWith('-');
	const unsigned = negative ? trimmed.slice(1) : trimmed;
	const [whole, frac = ''] = unsigned.split('.');
	const cents = BigInt(whole || '0') * 100n + BigInt((frac + '00').slice(0, 2) || '0');
	return negative ? -cents : cents;
}

/** Sums decimal amount strings, returning the total in integer cents. */
export function sumCents(amounts: string[]): bigint {
	return amounts.reduce((sum, amount) => sum + toCents(amount), 0n);
}

/** Sums decimal amount strings, returning the total as a plain number. */
export function sumAmounts(amounts: string[]): number {
	return Number(sumCents(amounts)) / 100;
}
