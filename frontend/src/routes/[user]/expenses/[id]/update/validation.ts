import { create, only, enforce, test } from 'vest';

type Part = {
	costcenter?: string;
	secondarycostcenter?: string;
	budgetline?: string;
	amount?: number | null;
};

type ExpenseUpdateFormData = {
	description?: string;
	'expense-date'?: string;
	parts?: Part[];
};

const validation = create((data: ExpenseUpdateFormData, currentField?: string) => {
	only(currentField);

	test('description', 'description_required', () => {
		enforce(data.description).isNotBlank();
	});

	test('expense-date', 'expense_date_required', () => {
		enforce(data['expense-date']).isNotBlank();
	});

	test('expense-date', 'expense_date_future', () => {
		const dateStr = data['expense-date'];
		if (!dateStr) return;
		const today = new Date().toISOString().slice(0, 10);
		enforce(dateStr <= today).isTruthy();
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
