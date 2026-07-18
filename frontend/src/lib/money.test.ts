import { test, assert } from 'vitest';
import { toCents, sumCents, sumAmounts } from './money';

test('converts a plain decimal string to cents', () => {
	assert.equal(toCents('123.45'), 12345n);
});

test('pads a single decimal digit', () => {
	assert.equal(toCents('12.5'), 1250n);
});

test('handles a whole number with no decimal point', () => {
	assert.equal(toCents('42'), 4200n);
});

test('handles negative amounts', () => {
	assert.equal(toCents('-5.50'), -550n);
});

test('sums cents without floating-point drift', () => {
	assert.equal(sumCents(['16.90', '2433.84']), 245074n);
});

test('sums amounts back to a number that avoids float drift', () => {
	assert.equal(sumAmounts(['16.90', '2433.84']), 2450.74);
});
