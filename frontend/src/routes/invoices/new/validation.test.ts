import { afterEach, assert, beforeEach, test, vi } from 'vitest';
import { freezeTime } from '$lib/test/helpers';
import type { InvoiceFormData, Part } from './validation';
import validation from './validation';

export const TODAY = '2026-05-29';
export const YESTERDAY = '2026-05-28';
export const TOMORROW = '2026-05-30';

beforeEach(() => {
	freezeTime(TODAY);
});

afterEach(() => {
	vi.useRealTimers();
	validation.reset();
});

/** Example expense part **/
export const makePart = (overrides: Partial<Part> = {}): Part => ({
	// Shoutout MISTY (jag älskar kaffe)
	costcenter: 'Sektionslokalsgruppen',
	secondarycostcenter: 'Allmänt',
	budgetline: 'Metadryck',
	amount: 100,
	...overrides
});

/** Example valid form */
export const makeFormData = (overrides: Partial<InvoiceFormData> = {}): InvoiceFormData => ({
	description: 'Det sista fikat någon i manusgruppen någonsin kommer äta i sina liv',
	'invoice-date': YESTERDAY,
	'due-date': TOMORROW,
	files: [new File(['receipt'], 'receipt.png', { type: 'image/png' })],
	parts: [makePart()],
	...overrides
});

test('invoice-date: yesterday is valid', () => {
	const data = makeFormData({ 'invoice-date': YESTERDAY });
	const result = validation.run(data);
	assert(!result.hasErrors('invoice-date'));
});

test('invoice-date: today is valid', () => {
	const data = makeFormData({ 'invoice-date': TODAY });
	const result = validation.run(data);
	assert(!result.hasErrors('invoice-date'));
});

test('invoice-date: tomorrow is valid', () => {
	const data = makeFormData({ 'invoice-date': TOMORROW });
	const result = validation.run(data);
	assert(!result.hasErrors('invoice-date'));
});

test('due-date: yesterday is valid', () => {
	const data = makeFormData({ 'due-date': YESTERDAY });
	const result = validation.run(data);
	assert(!result.hasErrors('due-date'));
});

test('due-date: today is valid', () => {
	const data = makeFormData({ 'due-date': TODAY });
	const result = validation.run(data);
	assert(!result.hasErrors('due-date'));
});

test('due-date: tomorrow is valid', () => {
	const data = makeFormData({ 'due-date': TOMORROW });
	const result = validation.run(data);
	assert(!result.hasErrors('due-date'));
});
