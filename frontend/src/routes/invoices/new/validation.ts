import { create, enforce, test } from 'vest';
import 'vest/date';
import { getLocalTimeZone, today } from '@internationalized/date';

export type Part = {
	costcenter?: string;
	secondarycostcenter?: string;
	budgetline?: string;
	amount?: number | null;
};

export type InvoiceFormData = {
	description?: string;
	'invoice-date'?: string;
	'due-date'?: string;
	files?: File[];
	parts?: Part[];
};

const validation = create((data: InvoiceFormData, currentField?: string) => {
	test('description', 'description_required', () => {
		enforce(data.description).isNotBlank();
	});

	test('invoice-date', 'invoice_date_required', () => {
		enforce(data['invoice-date']).isNotBlank();
	});

	test('invoice-date', 'invoice_date_not_in_future', () => {
		enforce(data['invoice-date'])
			.isDate()
			.isBefore(today(getLocalTimeZone()).add({ days: 1 }).toString());
	});

	test('due-date', 'due_date_today_or_after', () => {
		enforce(data['due-date'])
			.isDate()
			.isAfter(today(getLocalTimeZone()).subtract({ days: 1 }).toString());
	});

	test('due-date', 'due_date_required', () => {
		enforce(data['due-date']).isNotBlank();
	});
	test('files', 'files_required', () => {
		enforce(data.files).isArray().longerThan(0);
	});

	test('parts', 'parts_required', () => {
		data.parts?.forEach((part, i) => {
			test(`part-${i}-costcenter`, 'cost_center_required', () => {
				enforce(part.costcenter).isNotBlank();
			});
			test(`part-${i}-secondarycostcenter`, 'secondary_cost_center_required', () => {
				enforce(part.secondarycostcenter).isNotBlank();
			});
			test(`part-${i}-budgetline`, 'budget_line_required', () => {
				enforce(part.budgetline).isNotBlank();
			});
			test(`part-${i}-amount`, 'amount_required', () => {
				enforce(part.amount).isNotNull();
			});
			test(`part-${i}-amount`, 'amount_negative', () => {
				enforce(part.amount).isNumber().greaterThan(0);
			});
			test(`part-${i}-amount`, 'amount_too_large', () => {
				enforce(part.amount).isNumber().lessThanOrEquals(9999999.99);
			});
		});
	});
});

export default validation;
