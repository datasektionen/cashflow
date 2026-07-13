import type { Actions } from './$types';
import { API } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import { logger } from '$lib/logger';
import type { ExpenseUpdate, PartUpdate } from '$lib/api/types';

export const actions: Actions = {
	default: async (event) => {
		const user = event.locals.user;
		if (!user) {
			throw redirect(303, '/login');
		}
		const api = new API('http://localhost:8000/api/', event.fetch);
		const id = parseInt(event.params.id!);

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

		// Parts are only present in the form when they're still editable (the
		// parts editor is swapped for a read-only table once any part is
		// attested), so an empty list here means "leave parts unchanged".
		const parts: PartUpdate[] = [];
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

		const update: ExpenseUpdate = {
			description: description.toString(),
			expense_date: expenseDate.toString(),
			files,
			...(parts.length > 0 && { parts })
		};

		logger.debug({ id, files: files.length, parts: parts.length }, 'updating expense');
		try {
			await api.expenses.update(id, update);
		} catch (err) {
			logger.error({ err }, 'failed to update expense');
			throw err;
		}

		throw redirect(303, `/${user.username}/expenses/${id}`);
	}
};
