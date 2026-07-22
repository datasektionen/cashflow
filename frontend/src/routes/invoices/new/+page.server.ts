import { API_URL } from '$lib/config';
import type { Actions } from './$types';
import { fail, redirect } from '@sveltejs/kit';
import { type InvoiceCreate, type InvoicePart } from '$lib/api/types';
import { API, ApiClient } from '$lib/api';
import { logger } from '$lib/logger';

export const actions: Actions = {
	default: async (event) => {
		const api = new API(API_URL, event.fetch);
		const user = event.locals.user;
		if (!user) {
			redirect(303, 'login/');
		}

		const data = await event.request.formData();

		const description = data.get('description');
		if (!description || description.toString().trim() === '') {
			return fail(400, { error: 'Description is required' });
		}
		const files = data.getAll('files').filter((f): f is File => f instanceof File);
		if (!files || files.length < 1) {
			return fail(400, { error: 'A file is required.' });
		}
		const invoice_date = data.get('invoice-date');
		if (!invoice_date) {
			return fail(400, { error: 'Invoice date is required' });
		}
		const due_date = data.get('due-date');
		if (!due_date) {
			return fail(400, { error: 'Due date is required' });
		}

		const parts: InvoicePart[] = [];
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
		const Invoice: InvoiceCreate = {
			description: description.toString(),
			invoice_date: invoice_date.toString(),
			due_date: due_date.toString(),
			parts,
			files
		};

		logger.debug({ parts: parts.length, files: files.length }, 'creating invoice');
		try {
			const result = await api.invoices.create(Invoice);
			logger.info({ id: result.id }, 'invoice created');
		} catch (err) {
			logger.error({ err }, 'failed to create invoice');
			throw err;
		}

		redirect(303, `/${user.username}/claims/?createSuccess=true`);
	}
};
