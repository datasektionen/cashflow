import type { Actions } from './$types';
import { API } from '$lib/api';
import { fail } from '@sveltejs/kit';
import { logger } from '$lib/logger';
import type { ExpenseCreate, ExpensePart } from '$lib/api/types';

export const actions: Actions = {
	// This action handles the form submit when creating new expenses
	default: async (event) => {
		const api = new API('http://localhost:8000/api/', event.fetch);

		const data = await event.request.formData();

		const description = data.get('description');
		if (description == null || description.toString().trim() === '') {
			return fail(400, { error: 'Description is required' });
		}
		const expenseDate = data.get('expense-date');
		if (expenseDate == null) {
			return fail(400, { error: 'expense_date is required' });
		}
		const files = data.getAll('files').filter((f): f is File => f instanceof File);

		// We need to parse expense parts into a JSON string for the API post request
		const parts: ExpensePart[] = [];
		let i = 0;
		for (const field of data) {
			if (field[0].startsWith(`part-${i}-`)) {
				const cost_centre = data.get(`part-${i}-costcenter`);
				if (cost_centre == null) {
					return fail(400, { error: `cost_centre is required for part ${i}` });
				}
				const secondary_cost_centre = data.get(`part-${i}-secondarycostcenter`);
				if (secondary_cost_centre == null) {
					return fail(400, { error: `secondary_cost_centre is required for part ${i}` });
				}
				const budget_line = data.get(`part-${i}-budgetline`);
				if (budget_line == null) {
					return fail(400, { error: `budget_line is required for part ${i}` });
				}
				const amount = data.get(`part-${i}-amount`);
				if (amount == null) {
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

		const expense: ExpenseCreate = {
			description: description.toString(),
			expense_date: expenseDate.toString(),
			parts: parts,
			files: files
		};

		logger.debug({ parts: parts.length, files: files.length }, 'creating expense');
		try {
			const result = await api.expenses.create(expense);
			logger.info({ id: result.id }, 'expense created');
		} catch (err) {
			logger.error({ err }, 'failed to create expense');
			throw err;
		}
	}
};
