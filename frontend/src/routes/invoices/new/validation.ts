import { create, enforce, only, test } from 'vest';
import { type DateValue } from '@internationalized/date';
import type { InvoiceCreate, PartCreateUpdate } from '#lib/api/types.ts';
import { logger } from '#lib/logger.ts';
import { testParts, type BudgetLineUsage } from '#lib/budgetUsage.ts';

export type NewInvoiceFormData = {
	description: string;
	files: File[];
	parts: PartCreateUpdate[];
	// Set by ExpenseParts, used to warn about exceeded budget lines
	budgetUsage: (BudgetLineUsage | null)[];
	invoiceDate: DateValue | undefined;
	invoiceNumber: string;
	dueDate: DateValue | undefined;
};

type InvoiceFields = Omit<NewInvoiceFormData, 'invoiceNumber'>;

/** Converts the fields shared with the update form for the API. */
export function invoiceFields(formData: InvoiceFields) {
	if (!formData.invoiceDate || !formData.dueDate) {
		logger.error(formData, 'Expected valid invoice and due dates in form data');
		throw new Error('Invoice and due dates are required');
	}

	return {
		description: formData.description,
		invoice_date: formData.invoiceDate.toString(),
		due_date: formData.dueDate.toString(),
		files: formData.files,
		parts: formData.parts
	};
}

/** Converts the form data into the format the API expects. */
export const validateFormData = (formData: NewInvoiceFormData): InvoiceCreate => ({
	...invoiceFields(formData),
	invoice_number: formData.invoiceNumber
});

/** Rules shared with the update form. */
export function testInvoiceFields(data: InvoiceFields) {
	test('description', 'description_required', () => {
		enforce(data.description).isNotBlank();
	});

	test('invoice-date', 'invoice_date_required', () => {
		enforce(data.invoiceDate).isNotEmpty();
	});

	test('due-date', 'due_date_required', () => {
		enforce(data.dueDate).isNotEmpty();
	});
}

const validation = create((data: NewInvoiceFormData, currentField?: string) => {
	only(currentField);

	testInvoiceFields(data);

	test('files', 'files_required', () => {
		enforce(data.files).isArray().longerThan(0);
	});

	testParts(data.parts, data.budgetUsage);

	test('invoice-number', 'invoice_number_required', () => {
		enforce(data.invoiceNumber).isNotBlank();
	});
});

export default validation;
