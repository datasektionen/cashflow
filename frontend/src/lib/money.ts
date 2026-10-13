import { SEK, type Dinero, dinero, toDecimal, add } from 'dinero.js';

export const ZERO = dinero({ amount: 0, currency: SEK });

const FORMAT = new Intl.NumberFormat('sv-SE', {
	minimumFractionDigits: 2,
	maximumFractionDigits: 2
});

/** Formats a decimal amount string or number as e.g. "1 234,56". */
export function formatAmount(amount: string | number): string {
	return `${FORMAT.format(Number(amount))}`;
}

/**
 * Formats a Dinero amount for display, e.g. "1 234,56".
 *
 * @example
 * formatDineroAmount(dinero({ amount: 123456, currency: SEK })); // "1 234,56"
 */
export function formatDineroAmount(dineroAmount: Dinero<number, 'SEK'>): string {
	return toDecimal(dineroAmount, ({ value }) => formatAmount(value));
}

/*
 * Creates a dinero object from a float value
 */
export function dineroFromFloat(value: number, currency: typeof SEK): Dinero<number, 'SEK'> {
	const factor = currency.base ** currency.exponent;
	const amount = Math.round(factor * value);
	return dinero({ amount, currency });
}

/**
 * Creates a dinero object from a decimal string (e.g. from a Django DecimalField)
 * without going through floating point.
 *
 * @example
 * dineroFromDecimal('1234.56', SEK); // dinero({ amount: 123456, currency: SEK })
 */
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

/**
 * Sums the amount of several dinero objects. Uses the `add` function from `dinero.js` to avoid floating point errors.
 *
 * @example
 * sumDinero([dinero({ amount: 100, currency: SEK }), dinero({ amount: 200, currency: SEK })]); // dinero({ amount: 300, currency: SEK })
 */
export function sumDinero(amounts: Dinero<number, 'SEK'>[]): Dinero<number, 'SEK'> {
	return amounts.reduce((sum, amount) => {
		return add(sum, amount);
	}, ZERO);
}

/**
 * The total amount of a claim, i.e. the sum of its parts.
 *
 * @example
 * claimTotal(expense); // dinero({ amount: 30000, currency: SEK })
 */
export function claimTotal(claim: {
	parts: { amount: Dinero<number, 'SEK'> }[];
}): Dinero<number, 'SEK'> {
	return sumDinero(claim.parts.map((part) => part.amount));
}
