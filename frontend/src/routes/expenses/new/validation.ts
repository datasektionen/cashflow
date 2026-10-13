import { create, test, only, enforce } from 'vest';
import { type DateValue } from '@internationalized/date';
import type { ExpenseCreate, PartCreateUpdate } from '$lib/api/types';
import { dinero, greaterThan, isZero, lessThan } from 'dinero.js';
import { SEK } from 'dinero.js/currencies';
import { logger } from '$lib/logger';

export type NewExpenseFormData = {
	description: string;
	files: File[];
	// parts: {
	// 	cost_centre: string;
	// 	secondary_cost_centre: string;
	// 	budget_line: string;
	// 	amount: string;
	// }[];
	parts: PartCreateUpdate[];
	date: DateValue | undefined;
};

//*
// Takes the form data and converts it into the format expected by the API.
//*
export function validateFormData(formData: NewExpenseFormData): ExpenseCreate {
	if (!formData.date) {
		logger.error(formData, 'Expected valid date in form data');
		throw new Error('Date is required');
	}
	const expense_date = formData.date.toString();

	return {
		description: formData.description,
		expense_date,
		files: formData.files,
		parts: formData.parts
	};
}

const validation = create((data: NewExpenseFormData, currentField?: string) => {
	only(currentField);

	test('description', 'description_required', () => {
		enforce(data.description).isNotBlank();
	});

	test('expense-date', 'expense_date_required', () => {
		enforce(data.date).isNotEmpty();
	});

	test('expense-date', 'expense_date_future', () => {
		const dateStr = data.date?.toString();
		if (!dateStr) return;
		const today = new Date().toISOString().slice(0, 10);
		enforce(dateStr <= today).isTruthy();
	});

	test('files', 'files_required', () => {
		enforce(data.files).isArray().longerThan(0);
	});

	data.parts?.forEach((part, i) => {
		test(`part-${i}-costcenter`, 'cost_center_required', () => {
			enforce(part.cost_centre).isNotBlank();
		});
		test(`part-${i}-secondarycostcenter`, 'secondary_cost_center_required', () => {
			enforce(part.secondary_cost_centre).isNotBlank();
		});
		test(`part-${i}-budgetline`, 'budget_line_required', () => {
			enforce(part.budget_line).isNotBlank();
		});
		test(`part-${i}-amount`, 'amount_required', () => {
			enforce(isZero(part.amount)).isFalsy();
		});
		test(`part-${i}-amount`, 'amount_negative', () => {
			const zero = dinero({ amount: 0, currency: SEK });
			enforce(greaterThan(part.amount, zero)).isTruthy();
		});
		test(`part-${i}-amount`, 'amount_too_large', () => {
			const maxAmount = dinero({ amount: 999999999, currency: SEK });
			enforce(lessThan(part.amount, maxAmount)).isTruthy();
		});
	});
});

export default validation;
