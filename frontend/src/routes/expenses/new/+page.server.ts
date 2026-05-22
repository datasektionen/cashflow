import type { Actions } from './$types';
import { API } from '$lib/api';
import { fail } from '@sveltejs/kit';
import type { ExpenseCreate, ExpensePart } from '$lib/api/types';

export const actions: Actions = {
	// This action handles the form submit when creating new expenses
	default: async (event) => {
		console.log('[new-expense] form submit received');
		const api = new API('http://localhost:8000/api/', event.fetch);

		const data = await event.request.formData();
		console.log('[new-expense] form fields:', [...data.keys()]);

		const description = data.get('description');
		if (description == null || description.toString().trim() === '') {
			console.warn('[new-expense] missing description');
			return fail(400, { error: 'Description is required' });
		}
		const expenseDate = data.get('expense-date');
		if (expenseDate == null) {
			console.warn('[new-expense] missing expense-date');
			return fail(400, { error: 'expense_date is required' });
		}
		const files = data.getAll('files').filter((f): f is File => f instanceof File);
		console.log(
			'[new-expense] files:',
			files.map((f) => ({ name: f.name, size: f.size, type: f.type }))
		);

		// We need to parse expense parts into a JSON string for the API post request
		const parts: ExpensePart[] = [];
		let i = 0;
		for (const field of data) {
			if (field[0].startsWith(`part-${i}-`)) {
				const cost_centre = data.get(`part-${i}-costcenter`);
				if (cost_centre == null) {
					console.warn(`[new-expense] part ${i} missing cost_centre`);
					return fail(400, { error: `cost_centre is required for part ${i}` });
				}
				const secondary_cost_centre = data.get(`part-${i}-secondarycostcenter`);
				if (secondary_cost_centre == null) {
					console.warn(`[new-expense] part ${i} missing secondary_cost_centre`);
					return fail(400, { error: `secondary_cost_centre is required for part ${i}` });
				}
				const budget_line = data.get(`part-${i}-budgetline`);
				if (budget_line == null) {
					console.warn(`[new-expense] part ${i} missing budget_line`);
					return fail(400, { error: `budget_line is required for part ${i}` });
				}
				const amount = data.get(`part-${i}-amount`);
				if (amount == null) {
					console.warn(`[new-expense] part ${i} missing amount`);
					return fail(400, { error: `amount is required for part ${i}` });
				}

				parts.push({
					cost_centre: cost_centre.toString(),
					secondary_cost_centre: secondary_cost_centre.toString(),
					budget_line: budget_line.toString(),
					amount: amount.toString()
				});

				i++;
			}
		}
		console.log(`[new-expense] parsed ${parts.length} parts:`, parts);

		const expense: ExpenseCreate = {
			description: description.toString(),
			expense_date: expenseDate.toString(),
			parts: parts,
			files: files
		};

		console.log('[new-expense] calling api.expenses.create');
		try {
			const result = await api.expenses.create(expense);
			console.log('[new-expense] api success:', result);
		} catch (err) {
			console.error('[new-expense] api error:', err);
			throw err;
		}
	}
};
