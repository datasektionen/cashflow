<script lang="ts">
	import { api } from '$lib/api';
	import type { Payment } from '$lib/api/types';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import { ExternalLink } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';

	let { payment }: { payment: Payment } = $props();

	let expensesPromise = $derived(api.expenses.list(1, 100, { reimbursement: payment.id }));

	const fmt = (n: number) =>
		n.toLocaleString('sv-SE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
</script>

<div class="flex flex-col pb-2 pl-8">
	{#await expensesPromise}
		<div class="p-4">
			<CashSpinner />
		</div>
	{:then resolved}
		{#each resolved.data as expense}
			{@const costCentres = [...new Set(expense.parts.map((p) => p.cost_centre))]}
			<div class="flex flex-row items-stretch">
				<div class="flex min-w-0 flex-1 flex-col gap-y-1 py-2 pl-3">
					<a
						href="/admin/expenses/{expense.id}"
						target="_blank"
						rel="noopener noreferrer"
						class="group flex min-w-0 items-center gap-x-1.5 text-sm text-base-subtle dark:text-dark-base-subtle"
					>
						<span class="my-auto min-w-0 text-xs">#{expense.id}</span>
						<span class="min-w-0 truncate">{expense.description}</span>
						<ExternalLink
							class="size-3.5 shrink-0 opacity-50 transition-opacity group-hover:opacity-100"
						/>
					</a>
					{#if costCentres.length > 0}
						<div class="flex flex-wrap gap-1">
							{#each costCentres as cc}
								<span class="bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
							{/each}
						</div>
					{/if}
				</div>
				<div
					class="flex w-36 shrink-0 items-start justify-end px-4 py-2 text-sm font-medium tabular-nums"
				>
					{fmt(parseFloat(expense.total))} kr
				</div>
			</div>
		{/each}

		{#if resolved.data.length > 0}
			{@const grandTotal = resolved.data.reduce((sum, e) => sum + parseFloat(e.total), 0)}
			<div
				class="mt-2 flex items-center justify-end border-t border-base-400 pt-3 pr-4 dark:border-dark-base-150"
			>
				<span class="text-sm font-medium tabular-nums">{fmt(grandTotal)} kr</span>
			</div>
		{/if}
	{:catch}
		<div class="p-4">
			<span class="text-sm text-red-500">{$_('admin_pay.load_error')}</span>
		</div>
	{/await}
</div>
