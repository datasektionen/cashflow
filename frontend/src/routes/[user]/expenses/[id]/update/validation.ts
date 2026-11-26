import { create, only } from 'vest';
import type { ExpenseUpdate } from '#lib/api/types.ts';
import { testParts } from '#lib/budgetUsage.ts';
import {
	testExpenseFields,
	validateFormData as createPayload,
	type NewExpenseFormData
} from '../../../../expenses/new/validation';

export type UpdateExpenseFormData = NewExpenseFormData & { deletedFiles: Set<number> };

/** Converts the form data for the API; parts are left out unless `includeParts`. */
export function validateFormData(
	formData: UpdateExpenseFormData,
	includeParts: boolean
): ExpenseUpdate {
	const { parts, ...expense } = createPayload(formData);
	return {
		...expense,
		...(includeParts && parts.length > 0 && { parts }),
		...(formData.deletedFiles.size > 0 && { delete_files: [...formData.deletedFiles] })
	};
}

const validation = create((data: UpdateExpenseFormData, currentField?: string) => {
	only(currentField);
	testExpenseFields(data);
	testParts(data.parts, data.budgetUsage);
});

export default validation;
