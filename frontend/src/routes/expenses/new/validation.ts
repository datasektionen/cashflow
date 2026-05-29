import { create, test, only, enforce } from 'vest';
import { get } from 'svelte/store';
import { _ } from 'svelte-i18n';

type Part = {
	costcenter?: string;
	secondarycostcenter?: string;
	budgetline?: string;
	amount?: number | null;
};

type ExpenseFormData = {
	description?: string;
	'expense-date'?: string;
	files?: File[];
	parts?: Part[];
};

const validation = create((data: ExpenseFormData, currentField?: string) => {
	only(currentField);
	const t = get(_);

	test('description', t('description_required'), () => {
		enforce(data.description).isNotBlank();
	});

	test('expense-date', t('expense_date_required'), () => {
		enforce(data['expense-date']).isNotBlank();
	});

	test('expense-date', t('expense_date_future'), () => {
		const dateStr = data['expense-date'];
		if (!dateStr) return;
		const today = new Date().toISOString().slice(0, 10);
		enforce(dateStr <= today).isTruthy();
	});

	test('files', t('files_required'), () => {
		enforce(data.files).isArray().longerThan(0);
	});

	data.parts?.forEach((part, i) => {
		test(`part-${i}-costcenter`, t('cost_center_required'), () => {
			enforce(part.costcenter).isNotBlank();
		});
		test(`part-${i}-secondarycostcenter`, t('secondary_cost_center_required'), () => {
			enforce(part.secondarycostcenter).isNotBlank();
		});
		test(`part-${i}-budgetline`, t('budget_line_required'), () => {
			enforce(part.budgetline).isNotBlank();
		});
		test(`part-${i}-amount`, t('amount_required'), () => {
			enforce(part.amount).isNotNull();
		});
		test(`part-${i}-amount`, t('amount_negative'), () => {
			enforce(part.amount).isNumber().greaterThan(0);
		});
		test(`part-${i}-amount`, t('amount_too_large'), () => {
			enforce(part.amount).isNumber().lessThanOrEquals(9999999.99);
		});
	});
});

export default validation;
