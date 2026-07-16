import { API_URL } from '$lib/config';
import type { Actions } from './$types';
import { API } from '$lib/api';
import { fail, redirect } from '@sveltejs/kit';
import { logger } from '$lib/logger';
import type { InvoiceUpdate, PartUpdate } from '$lib/api/types';

export const actions: Actions = {
	default: async (event) => {
		const user = event.locals.user;
		if (!user) {
			throw redirect(303, '/login');
		}
		const api = new API(API_URL, event.fetch);
		const id = parseInt(event.params.id!);

		const data = await event.request.formData();

		const description = data.get('description');
		if (description == null || description.toString().trim() === '') {
			return fail(400, { error: 'Description is required' });
		}
		const invoiceDate = data.get('invoice-date');
		if (invoiceDate == null) {
			return fail(400, { error: 'invoice_date is required' });
		}
		const dueDate = data.get('due-date');
		if (dueDate == null) {
			return fail(400, { error: 'due_date is required' });
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

		const update: InvoiceUpdate = {
			description: description.toString(),
			invoice_date: invoiceDate.toString(),
			due_date: dueDate.toString(),
			files,
			...(parts.length > 0 && { parts })
		};

		logger.debug({ id, files: files.length, parts: parts.length }, 'updating invoice');
		try {
			await api.invoices.update(id, update);
		} catch (err) {
			logger.error({ err }, 'failed to update invoice');
			throw err;
		}

		throw redirect(303, `/${user.username}/invoices/${id}`);
	}
};
