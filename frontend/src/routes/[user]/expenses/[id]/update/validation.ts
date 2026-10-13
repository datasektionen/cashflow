import { create, only, enforce, test } from 'vest';
import { type DateValue } from '@internationalized/date';
import type { ExpenseUpdate, PartCreateUpdate } from '$lib/api/types';
import { dinero, greaterThan, isZero, lessThan } from 'dinero.js';
import { SEK } from 'dinero.js/currencies';
import { logger } from '$lib/logger';

export type UpdateExpenseFormData = {
	description: string;
	files: File[];
	deletedFiles: Set<number>;
	parts: PartCreateUpdate[];
	date: DateValue | undefined;
};

//*
// Takes the form data and converts it into the format expected by the API.
// Parts are left out when `includeParts` is false, e.g. when some part is already attested.
//*
export function validateFormData(
	formData: UpdateExpenseFormData,
	includeParts: boolean
): ExpenseUpdate {
	if (!formData.date) {
		logger.error(formData, 'Expected valid date in form data');
		throw new Error('Date is required');
	}
	const expense_date = formData.date.toString();

	return {
		description: formData.description,
		expense_date,
		files: formData.files,
		...(includeParts && formData.parts.length > 0 && { parts: formData.parts }),
		...(formData.deletedFiles.size > 0 && { delete_files: [...formData.deletedFiles] })
	};
}

const validation = create((data: UpdateExpenseFormData, currentField?: string) => {
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
