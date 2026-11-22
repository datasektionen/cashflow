import { create, only } from 'vest';
import type { InvoiceUpdate } from '#lib/api/types.ts';
import { testParts } from '#lib/budgetUsage.ts';
import {
	invoiceFields,
	testInvoiceFields,
	type NewInvoiceFormData
} from '../../../../invoices/new/validation';

export type UpdateInvoiceFormData = Omit<NewInvoiceFormData, 'invoiceNumber'> & {
	deletedFiles: Set<number>;
};

/** Converts the form data for the API; parts are left out unless `includeParts`. */
export function validateFormData(
	formData: UpdateInvoiceFormData,
	includeParts: boolean
): InvoiceUpdate {
	const { parts, ...invoice } = invoiceFields(formData);
	return {
		...invoice,
		...(includeParts && parts.length > 0 && { parts }),
		...(formData.deletedFiles.size > 0 && { delete_files: [...formData.deletedFiles] })
	};
}

const validation = create((data: UpdateInvoiceFormData, currentField?: string) => {
	only(currentField);
	testInvoiceFields(data);
	testParts(data.parts, data.budgetUsage);
});

export default validation;
