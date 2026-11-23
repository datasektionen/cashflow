<script lang="ts">
	import CostCentreCell from '#lib/components/CostCentreCell.svelte';
	import { api } from '#lib/api/index.ts';
	import type { Payment } from '#lib/api/types.ts';
	import { Skeleton } from '#lib/components/ui/index.ts';
	import { ExternalLink } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';
	import { formatDineroAmount, sumDinero, claimTotal } from '#lib/money.ts';

	let { payment }: { payment: Payment } = $props();

	let expensesPromise = $derived(api.expenses.list(1, 100, { reimbursement: payment.id }));
</script>

<div class="flex flex-col pb-2 md:pl-8">
	{#await expensesPromise}
		{#each { length: 2 }, i (i)}
			<div class="flex items-start gap-4 py-2 pr-4 pl-3">
				<div class="flex flex-1 flex-col gap-1">
					<Skeleton class="h-5 w-48" />
					<Skeleton class="h-6 w-24" />
				</div>
				<Skeleton class="h-5 w-20" />
			</div>
		{/each}
	{:then resolved}
		{#each resolved.data as expense}
			<div class="flex flex-row items-stretch">
				<div class="flex min-w-0 flex-1 flex-col gap-y-1 py-2 pl-3">
					<a
						href="/admin/expenses/{expense.id}"
						target="_blank"
						rel="noopener noreferrer"
						class="group flex min-w-0 items-center gap-x-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
					>
						<span class="hidden font-mono text-xs md:block">#{expense.id}</span>
						<span class="min-w-0 truncate">{expense.description}</span>
						<ExternalLink
							class="size-3.5 shrink-0 opacity-50 transition-opacity group-hover:opacity-100"
						/>
					</a>
					<CostCentreCell parts={expense.parts} />
				</div>
				<div
					class="flex w-36 shrink-0 items-start justify-end px-4 py-2 text-sm font-medium tabular-nums"
				>
					{formatDineroAmount(claimTotal(expense))} kr
				</div>
			</div>
		{/each}

		{#if resolved.data.length > 0}
			{@const grandTotal = sumDinero(resolved.data.map((e) => claimTotal(e)))}
			<div class="mt-2 flex items-center justify-end border-t border-border pt-3 pr-4">
				<span class="text-sm font-medium tabular-nums">{formatDineroAmount(grandTotal)} kr</span>
			</div>
		{/if}
	{:catch}
		<p class="p-4 text-sm text-danger-text">{$_('admin_pay.load_error')}</p>
	{/await}
</div>
