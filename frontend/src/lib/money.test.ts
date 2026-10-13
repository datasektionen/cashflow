import { test, assert } from 'vitest';
import {
	formatAmount,
	formatDineroAmount,
	dineroFromFloat,
	dineroFromDecimal,
	ZERO,
	sumDinero
} from './money';
import { dinero, equal as dineroEqual, SEK } from 'dinero.js';

const sek = (amount: number) => dinero({ amount, currency: SEK });

test('formatAmount: correct formatting', () => {
	assert.equal(formatAmount('0'), '0,00');
	assert.equal(formatAmount(0), '0,00');

	assert.equal(formatAmount(0.001), '0,00');

	// \u00a0 is a non-breaking space
	assert.equal(formatAmount('1234.56'), '1\u00a0234,56');
	assert.equal(formatAmount(1234.56), '1\u00a0234,56');
});

test('formatDineroAmount: correct formatting', () => {
	assert.equal(formatDineroAmount(sek(123456)), '1\u00a0234,56');
});

test('dineroFromFloat: correct rounding', () => {
	assert.isTrue(dineroEqual(dineroFromFloat(1234.567, SEK), sek(123457))); // Should round up to closest öre
	assert.isTrue(dineroEqual(dineroFromFloat(0.005, SEK), sek(1))); // Should round to one öre
});

test('dineroFromDecimal: parses decimal strings', () => {
	assert.isTrue(dineroEqual(dineroFromDecimal('1234.56', SEK), sek(123456)));
	assert.isTrue(dineroEqual(dineroFromDecimal('0.10', SEK), sek(10)));
	assert.isTrue(dineroEqual(dineroFromDecimal('12.5', SEK), sek(1250)));
	assert.isTrue(dineroEqual(dineroFromDecimal('100', SEK), sek(10000)));
	assert.isTrue(dineroEqual(dineroFromDecimal('-12.34', SEK), sek(-1234)));
	assert.isTrue(dineroEqual(dineroFromDecimal('-0.00', SEK), ZERO));
});

test('dineroFromDecimal: rejects invalid input', () => {
	assert.throws(() => dineroFromDecimal('', SEK));
	assert.throws(() => dineroFromDecimal('12,50', SEK));
	assert.throws(() => dineroFromDecimal('abc', SEK));
	assert.throws(() => dineroFromDecimal('1.234', SEK));
});

test('sumDinero: correct sum', () => {
	assert.isTrue(dineroEqual(sumDinero([]), ZERO));

	const intAmounts = [1234, 54233, 123, 1, 14421];
	let intSum = intAmounts.reduce((sum, amount) => sum + amount);
	let dineroAmounts = intAmounts.map(sek);

	assert.isTrue(dineroEqual(sumDinero(dineroAmounts), sek(intSum)));

	const intAmountsWithNegatives = [1234, -54233, 123, 1, 14421, -1234];
	intSum = intAmountsWithNegatives.reduce((sum, amount) => sum + amount);
	dineroAmounts = intAmountsWithNegatives.map(sek);
	assert.isTrue(dineroEqual(sumDinero(dineroAmounts), sek(intSum)));
});
