import { create, test, only, enforce } from 'vest';
import { getLocalTimeZone, today, type DateValue } from '@internationalized/date';
import type { ExpenseCreate, PartCreateUpdate } from '#lib/api/types.ts';
import { logger } from '#lib/logger.ts';
import { testParts, type BudgetLineUsage } from '#lib/budgetUsage.ts';

export type NewExpenseFormData = {
	description: string;
	files: File[];
	parts: PartCreateUpdate[];
	budgetUsage: (BudgetLineUsage | null)[];
	date: DateValue | undefined;
};

/** Converts the form data into the format the API expects. */
export function validateFormData(formData: NewExpenseFormData): ExpenseCreate {
	if (!formData.date) {
		logger.error(formData, 'Expected valid date in form data');
		throw new Error('Date is required');
	}

	return {
		description: formData.description,
		expense_date: formData.date.toString(),
		files: formData.files,
		parts: formData.parts
	};
}

/** Rules shared with the update form. */
export function testExpenseFields(data: NewExpenseFormData) {
	test('description', 'description_required', () => {
		enforce(data.description).isNotBlank();
	});

	test('expense-date', 'expense_date_required', () => {
		enforce(data.date).isNotEmpty();
	});

	test('expense-date', 'expense_date_future', () => {
		if (!data.date) return;
		enforce(data.date.compare(today(getLocalTimeZone())) <= 0).isTruthy();
	});
}

const validation = create((data: NewExpenseFormData, currentField?: string) => {
	only(currentField);

	testExpenseFields(data);

	test('files', 'files_required', () => {
		enforce(data.files).isArray().longerThan(0);
	});

	testParts(data.parts, data.budgetUsage);
});

export default validation;
