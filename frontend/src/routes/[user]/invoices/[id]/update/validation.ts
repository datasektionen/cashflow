import { create, only, enforce, test } from 'vest';
import { type DateValue } from '@internationalized/date';
import type { InvoiceUpdate, PartCreateUpdate } from '$lib/api/types';
import { dinero, greaterThan, isZero, lessThan } from 'dinero.js';
import { SEK } from 'dinero.js/currencies';
import { logger } from '$lib/logger';
import { testBudgetLineExceeded, type BudgetLineUsage } from '$lib/budgetUsage';

export type UpdateInvoiceFormData = {
	description: string;
	files: File[];
	deletedFiles: Set<number>;
	parts: PartCreateUpdate[];
	// Set by ExpenseParts, used to warn about exceeded budget lines
	budgetUsage: (BudgetLineUsage | null)[];
	invoiceDate: DateValue | undefined;
	dueDate: DateValue | undefined;
};

//*
// Takes the form data and converts it into the format expected by the API.
// Parts are left out when `includeParts` is false, e.g. when some part is already attested.
//*
export function validateFormData(
	formData: UpdateInvoiceFormData,
	includeParts: boolean
): InvoiceUpdate {
	if (!formData.invoiceDate) {
		logger.error(formData, 'Expected valid invoice date in form data');
		throw new Error('Invoice date is required');
	}
	if (!formData.dueDate) {
		logger.error(formData, 'Expected valid due date in form data');
		throw new Error('Due date is required');
	}

	return {
		description: formData.description,
		invoice_date: formData.invoiceDate.toString(),
		due_date: formData.dueDate.toString(),
		files: formData.files,
		...(includeParts && formData.parts.length > 0 && { parts: formData.parts }),
		...(formData.deletedFiles.size > 0 && { delete_files: [...formData.deletedFiles] })
	};
}

const validation = create((data: UpdateInvoiceFormData, currentField?: string) => {
	only(currentField);

	test('description', 'description_required', () => {
		enforce(data.description).isNotBlank();
	});

	test('invoice-date', 'invoice_date_required', () => {
		enforce(data.invoiceDate).isNotEmpty();
	});

	test('due-date', 'due_date_required', () => {
		enforce(data.dueDate).isNotEmpty();
	});

	data.parts?.forEach((part, i) => {
		testBudgetLineExceeded(data.parts, data.budgetUsage, i);
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
