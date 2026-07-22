import { test, assert, afterEach, beforeEach, vi } from 'vitest';
import { freezeTime } from '$lib/test/helpers';
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

type Part = {
	costcenter?: string;
	secondarycostcenter?: string;
	budgetline?: string;
	amount?: number | null;
};

type ExpenseFormData = {
	description?: string;
	'expense-date'?: string;
	files?: File[];
	parts?: Part[];
};

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
export const makeFormData = (overrides: Partial<ExpenseFormData> = {}): ExpenseFormData => ({
	description: 'Det sista fikat någon i manusgruppen någonsin kommer äta i sina liv',
	'expense-date': YESTERDAY,
	files: [new File(['receipt'], 'receipt.png', { type: 'image/png' })],
	parts: [makePart()],
	...overrides
});

test('description: missing is invalid', () => {
	const data = makeFormData({ description: '' });
	const result = validation.run(data);
	assert(result.hasErrors('description'));
	const errors = result.getErrors('description');
	assert(errors.length === 1);
	assert(errors[0] === 'description_required');
});

test('description: whitespace only is invalid', () => {
	const data = makeFormData({ description: '  ' });
	const result = validation.run(data);
	assert(result.hasErrors('description'));
	assert(result.getErrors('description')[0] === 'description_required');
});

test('description: surrounding whitespace is valid', () => {
	const data = makeFormData({ description: '  Lunch with the board  ' });
	const result = validation.run(data);
	assert(!result.hasErrors('description'));
});

test('expense-date: yesterday is valid', () => {
	const data = makeFormData({ 'expense-date': YESTERDAY });
	const result = validation.run(data);
	assert(!result.hasErrors('expense-date'));
});

test('expense-date: today is valid', () => {
	const data = makeFormData({ 'expense-date': TODAY });
	const result = validation.run(data);
	assert(!result.hasErrors('expense-date'));
});

test('expense-date: tomorrow is invalid', () => {
	const data = makeFormData({ 'expense-date': TOMORROW });
	const result = validation.run(data);
	assert(result.hasErrors('expense-date'));
	const errors = result.getErrors('expense-date');
	assert(errors.length === 1);
	assert(errors[0] === 'expense_date_future');
});

test('files: empty array is invalid', () => {
	const data = makeFormData({ files: [] });
	const result = validation.run(data);
	assert(result.hasErrors('files'));
	const errors = result.getErrors('files');
	assert(errors.length === 1);
	assert(errors[0] === 'files_required');
});

test('files: one file is valid', () => {
	const data = makeFormData({
		files: [new File(['receipt'], 'receipt.png', { type: 'image/png' })]
	});
	const result = validation.run(data);
	assert(!result.hasErrors('files'));
});

test('files: missing is invalid', () => {
	const data = makeFormData({ files: undefined });
	const result = validation.run(data);
	assert(result.hasErrors('files'));
	assert(result.getErrors('files')[0] === 'files_required');
});
