<script lang="ts">
	import type { PageProps } from './$types';
	import type { Invoice, PaginatedResponse } from '$lib/api/types';
	import { api } from '$lib/api';
	import { invalidateAll } from '$app/navigation';
	import { ExternalLink } from '@lucide/svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import { alerts, error, success } from '$lib/stores/alerts.ts';
	import { isErrorResponse } from '$lib/api/errors.ts';
	import { logger } from '$lib/logger';

	type pageData = {
		invoices: PaginatedResponse<Invoice>;
	};

	let { data }: PageProps = $props();
	let { invoices }: pageData = $derived(data);

	let paying = new SvelteSet<number>();

	function total(invoice: Invoice): number {
		return invoice.parts.reduce((sum, part) => sum + parseFloat(part.amount), 0);
	}

	function costCentres(invoice: Invoice): string[] {
		return [...new Set(invoice.parts.map((p) => p.cost_centre))];
	}

	async function handlePay(invoice: Invoice) {
		if (paying.has(invoice.id)) return;
		paying.add(invoice.id);
		try {
			const paid = await api.invoices.pay(invoice.id);
			alerts.update((a) => [...a, success(`Faktura #${paid.id} betald`)]);
			await invalidateAll();
		} catch (e) {
			logger.error(e);
			const msg = isErrorResponse(e) ? e.detail : 'Något gick fel';
			alerts.update((a) => [...a, error(msg)]);
		} finally {
			paying.delete(invoice.id);
		}
	}
</script>

<div class="max-w-4xl border border-base-500 p-2 dark:border-dark-base-200">
	<table class="w-full table-fixed text-sm">
		<thead>
			<tr class="flex">
				<th
					class="flex-1 px-4 py-3 text-left text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
				>
					Faktura
				</th>
				<th
					class="hidden w-32 px-4 py-3 text-right text-xs font-medium text-base-subtle uppercase sm:block dark:text-dark-base-subtle"
				>
					Förfaller
				</th>
				<th
					class="w-32 px-4 py-3 text-right text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
				>
					Total
				</th>
				<th class="w-24 py-2 pr-4"></th>
			</tr>
		</thead>
		<tbody>
			{#each invoices.data as invoice (invoice.id)}
				<tr
					class="flex items-center border-b border-b-base-400 hover:bg-base-200 dark:border-dark-base-150 dark:hover:bg-dark-base-200"
				>
					<td class="flex min-w-0 flex-1 flex-col gap-y-1 px-4 py-2">
						<a
							href="/admin/invoices/{invoice.id}"
							target="_blank"
							rel="noopener noreferrer"
							class="group dark:hover:text-dark-base flex min-w-0 items-center gap-x-1.5 text-sm dark:text-dark-base-subtle"
						>
							<span class="min-w-0 truncate font-medium">{invoice.description}</span>
							<ExternalLink
								class="size-3.5 shrink-0 opacity-50 transition-opacity group-hover:opacity-100"
							/>
						</a>
						<div class="flex flex-wrap items-center gap-1">
							<span class="text-xs text-base-subtle dark:text-dark-base-subtle">
								{invoice.owner.first_name}
								{invoice.owner.last_name}
							</span>
							{#each costCentres(invoice) as cc}
								<span class="bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
							{/each}
						</div>
					</td>
					<td
						class="hidden w-32 px-4 py-2 text-right text-sm text-base-subtle tabular-nums sm:block dark:text-dark-base-subtle"
					>
						{invoice.due_date}
					</td>
					<td class="w-32 px-4 py-2 text-right font-semibold tabular-nums">
						{total(invoice).toLocaleString('sv-SE', {
							minimumFractionDigits: 2,
							maximumFractionDigits: 2
						})} kr
					</td>
					<td class="flex w-24 justify-end py-2 pr-4">
						<button
							onclick={() => handlePay(invoice)}
							disabled={paying.has(invoice.id)}
							class="cursor-pointer bg-money-green-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-money-green-700 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-money-green-600"
						>
							{paying.has(invoice.id) ? 'Betalar…' : 'Betala'}
						</button>
					</td>
				</tr>
			{/each}

			{#if invoices.data.length === 0}
				<tr class="flex">
					<td
						class="flex-1 px-4 py-8 text-center text-sm text-base-subtle dark:text-dark-base-subtle"
					>
						Inga fakturor att betala
					</td>
				</tr>
			{/if}
		</tbody>
	</table>
</div>
