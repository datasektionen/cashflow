import { SEK, type Dinero, dinero, toDecimal, add } from 'dinero.js';

export const ZERO = dinero({ amount: 0, currency: SEK });

const FORMAT = new Intl.NumberFormat('sv-SE', {
	minimumFractionDigits: 2,
	maximumFractionDigits: 2
});

const WHOLE = new Intl.NumberFormat('sv-SE', { maximumFractionDigits: 0 });

/** Formats an amount rounded to whole kronor, e.g. "1 235". */
export function formatWholeAmount(amount: string | number): string {
	return WHOLE.format(Number(amount));
}

/** Formats kronor with the unit, showing öre only when there are any: "1 235 kr", "62,50 kr". */
export function formatKronor(amount: string | number): string {
	const rounded = Math.round(Number(amount) * 100) / 100;
	return `${Number.isInteger(rounded) ? formatWholeAmount(rounded) : formatAmount(rounded)}\u00a0kr`;
}

/** Formats a decimal amount string or number as e.g. "1 234,56". */
export function formatAmount(amount: string | number): string {
	return FORMAT.format(Number(amount));
}

/** Formats a Dinero amount for display, e.g. "1 234,56". */
export function formatDineroAmount(dineroAmount: Dinero<number, 'SEK'>): string {
	return toDecimal(dineroAmount, ({ value }) => formatAmount(value));
}

/** Creates a dinero object from a float value. */
export function dineroFromFloat(value: number, currency: typeof SEK): Dinero<number, 'SEK'> {
	const factor = currency.base ** currency.exponent;
	const amount = Math.round(factor * value);
	return dinero({ amount, currency });
}

/** Creates a dinero object from a decimal string without going through floating point. */
export function dineroFromDecimal(value: string, currency: typeof SEK): Dinero<number, 'SEK'> {
	const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value.trim());
	if (!match) {
		throw new Error(`Invalid decimal amount: "${value}"`);
	}
	const [, sign, whole, fraction = ''] = match;
	if (fraction.length > currency.exponent) {
		throw new Error(`Too many fraction digits for ${currency.code}: "${value}"`);
	}

	const minorUnits = Number(whole + fraction.padEnd(currency.exponent, '0'));
	// Avoid -0 for e.g. "-0.00"
	const amount = sign && minorUnits !== 0 ? -minorUnits : minorUnits;
	return dinero({ amount, currency });
}

export function sumDinero(amounts: Dinero<number, 'SEK'>[]): Dinero<number, 'SEK'> {
	return amounts.reduce((sum, amount) => add(sum, amount), ZERO);
}

/** The sum of a claim's parts. */
export function claimTotal(claim: {
	parts: { amount: Dinero<number, 'SEK'> }[];
}): Dinero<number, 'SEK'> {
	return sumDinero(claim.parts.map((part) => part.amount));
}
