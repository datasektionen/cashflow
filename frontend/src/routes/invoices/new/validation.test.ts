import { afterEach, assert, beforeEach, test, vi } from 'vitest';
import { freezeTime } from '$lib/test/helpers';
import type { NewInvoiceFormData } from './validation';
import validation from './validation';
import type { PartCreateUpdate } from '$lib/api/types';
import { dinero, SEK } from 'dinero.js';
import { parseDate } from '@internationalized/date';

const TODAY = parseDate('2026-05-29');
const YESTERDAY = parseDate('2026-05-28');
const TOMORROW = parseDate('2026-05-30');

beforeEach(() => {
	freezeTime(TODAY.toString());
});

afterEach(() => {
	vi.useRealTimers();
	validation.reset();
});

/** Example expense part **/
export const makePart = (overrides: Partial<PartCreateUpdate> = {}): PartCreateUpdate => ({
	// Shoutout MISTY (jag älskar kaffe)
	cost_centre: 'Sektionslokalsgruppen',
	secondary_cost_centre: 'Allmänt',
	budget_line: 'Metadryck',
	amount: dinero({ amount: 10000, currency: SEK }),
	...overrides
});

/** Example valid form */
export const makeFormData = (overrides: Partial<NewInvoiceFormData> = {}): NewInvoiceFormData => ({
	description: 'Det sista fikat någon i manusgruppen någonsin kommer äta i sina liv',
	invoiceDate: YESTERDAY,
	invoiceNumber: '12345',
	dueDate: TOMORROW,
	files: [new File(['receipt'], 'receipt.png', { type: 'image/png' })],
	parts: [makePart()],
	budgetUsage: [],
	...overrides
});

test('invoice-date: yesterday is valid', () => {
	const data = makeFormData({ invoiceDate: YESTERDAY });
	const result = validation.run(data);
	assert(!result.hasErrors('invoice-date'));
});

test('invoice-date: today is valid', () => {
	const data = makeFormData({ invoiceDate: TODAY });
	const result = validation.run(data);
	assert(!result.hasErrors('invoice-date'));
});

test('invoice-date: tomorrow is valid', () => {
	const data = makeFormData({ invoiceDate: TOMORROW });
	const result = validation.run(data);
	assert(!result.hasErrors('invoice-date'));
});

test('due-date: yesterday is valid', () => {
	const data = makeFormData({ dueDate: YESTERDAY });
	const result = validation.run(data);
	assert(!result.hasErrors('due-date'));
});

test('due-date: today is valid', () => {
	const data = makeFormData({ dueDate: TODAY });
	const result = validation.run(data);
	assert(!result.hasErrors('due-date'));
});

test('due-date: tomorrow is valid', () => {
	const data = makeFormData({ dueDate: TOMORROW });
	const result = validation.run(data);
	assert(!result.hasErrors('due-date'));
});

test('budget line: exceeding budget warns but stays valid', () => {
	const data = makeFormData({
		parts: [makePart({ amount: dinero({ amount: 10100, currency: SEK }) })],
		budgetUsage: [
			{
				budget: dinero({ amount: 100000, currency: SEK }),
				uploaded: dinero({ amount: 90000, currency: SEK })
			}
		]
	});
	const result = validation.run(data);
	assert(result.getWarnings('part-0-budgetline')[0] === 'budget_line_exceeded');
	assert(result.isValid());
});
