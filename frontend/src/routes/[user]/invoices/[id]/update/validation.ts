import { create, only, enforce, test } from 'vest';

type Part = {
	costcenter?: string;
	secondarycostcenter?: string;
	budgetline?: string;
	amount?: number | null;
};

type InvoiceUpdateFormData = {
	description?: string;
	'invoice-date'?: string;
	'due-date'?: string;
	parts?: Part[];
};

const validation = create((data: InvoiceUpdateFormData, currentField?: string) => {
	only(currentField);

	test('description', 'description_required', () => {
		enforce(data.description).isNotBlank();
	});

	test('invoice-date', 'invoice_date_required', () => {
		enforce(data['invoice-date']).isNotBlank();
	});

	test('due-date', 'due_date_required', () => {
		enforce(data['due-date']).isNotBlank();
	});

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

export default validation;
