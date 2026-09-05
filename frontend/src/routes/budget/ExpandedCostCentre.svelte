<script lang="ts">
	import { api } from '$lib/api';
	import type { CostCentre } from '$lib/api/types';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import { formatAmount } from '$lib/money';
	import { _ } from 'svelte-i18n';
	import { TriangleAlert } from '@lucide/svelte';

	let { costCentre }: { costCentre: CostCentre } = $props();

	let detailedRes = $derived.by(() => {
		return api.budget.retrieveCostCentre(costCentre.id!).then((detail) => {
			console.log('cost centre detail', detail);
			return detail;
		});
	});
</script>

{#await detailedRes}
	<CashSpinner class="mx-auto text-money-green-500 opacity-50" />
{:then detail}
	<div class="w-full">
		<div
			class="hidden items-center gap-4 px-4 pb-2 text-xs font-medium tracking-wide text-base-subtle uppercase md:flex dark:text-dark-base-subtle"
		>
			<div class="w-64 shrink-0"></div>
			<div class="flex-1"></div>
			<div class="w-32 shrink-0 text-right">{$_('budget.total')}</div>
			<div class="w-32 shrink-0 text-right">{$_('budget.rest')}</div>
		</div>

		{#each detail.secondary_cost_centres ?? [] as scc}
			<div
				class="px-4 pt-8 pb-2 text-sm font-semibold tracking-wide text-base-subtle uppercase dark:text-dark-base-subtle"
			>
				{scc.name}
			</div>

			{#each scc.budget_lines ?? [] as bl}
				<div
					class="flex flex-col gap-4 border-b border-base-500 px-4 py-4 hover:bg-base-200 md:flex-row md:items-center dark:border-dark-base-200 dark:hover:bg-dark-base-200"
				>
					<div class="w-64 shrink-0 font-medium">{bl.name}</div>

					<div class="flex-1">
						{#if bl.expense}
							{@const num = (v?: string) => parseFloat(v ? v : '0')}
							{@const pct = (v?: string) =>
								Math.max(0, Math.min(100, (num(v) / Math.abs(bl.expense!)) * 100))}
							{@const blown = num(bl.amount_paid) > Math.abs(bl.expense!)}
							{@const alert = num(bl.amount_uploaded) > Math.abs(bl.expense!)}
							{@const barColor = blown
								? 'bg-red-400'
								: alert
									? 'bg-amber-400'
									: 'bg-money-green-500'}

							<div class="relative h-4 w-full bg-base-600 dark:bg-dark-base-50">
								<span
									class={['absolute top-0 left-0 hidden h-full opacity-40 md:flex', barColor]}
									style="width: {pct(bl.amount_uploaded)}%"
								></span>
								<span
									class={['absolute top-0 left-0 hidden h-full opacity-70 md:flex', barColor]}
									style="width: {pct(bl.amount_attested)}%"
								></span>
								<span
									class={['absolute top-0 left-0 h-full', barColor]}
									style="width: {pct(bl.amount_paid)}%"
								></span>
							</div>
							<div
								class="mt-1 flex flex-wrap gap-3 text-xs text-base-subtle dark:text-dark-base-subtle"
							>
								<span
									class={[
										'hidden items-center gap-1 md:flex',
										blown && 'font-bold text-base-text dark:text-dark-base-text'
									]}
								>
									<span class={['inline-block size-2', barColor]}></span>
									{$_('budget.paid')}
									{formatAmount(bl.amount_paid ?? '0')}
								</span>
								<span class="hidden items-center gap-1 md:flex">
									<span class={['inline-block size-2 opacity-70', barColor]}></span>
									{$_('budget.attested')}
									{formatAmount(bl.amount_attested ?? '0')}
								</span>
								<span
									class={[
										'hidden items-center gap-1 md:flex',
										alert && 'font-bold text-base-text dark:text-dark-base-text'
									]}
								>
									<span class={['inline-block size-2 opacity-40', barColor]}></span>
									{$_('budget.uploaded')}
									{formatAmount(bl.amount_uploaded ?? '0')}
								</span>
							</div>
						{/if}
					</div>

					<div
						class="w-full shrink-0 text-left whitespace-nowrap tabular-nums md:w-32 md:text-right"
					>
						{#if bl.expense}
							{@const num = (v?: string) => parseFloat(v ? v : '0')}
							{@const blown =
								num(bl.amount_attested) > Math.abs(bl.expense!) ||
								num(bl.amount_paid) > Math.abs(bl.expense!)}
							{@const alert = num(bl.amount_uploaded) > Math.abs(bl.expense!)}
							<span
								class={[
									'font-medium md:hidden',
									blown
										? 'text-red-400'
										: alert
											? 'text-amber-400'
											: 'text-money-green-600 dark:text-money-green-400'
								]}
							>
								{formatAmount(bl.amount_paid ?? '0')}
							</span>
							<span class="text-base-subtle md:hidden dark:text-dark-base-subtle">/</span>
							{formatAmount(Math.abs(bl.expense))}
						{/if}
					</div>

					<div
						class="w-full shrink-0 text-left whitespace-nowrap tabular-nums md:w-32 md:text-right"
					>
						{#if bl.expense}
							{@const rest = Math.abs(bl.expense) - parseFloat(bl.amount_paid ?? '0')}
							<span class={rest < 0 ? 'text-red-400' : undefined}>
								{formatAmount(rest)}
							</span>
						{/if}
					</div>
				</div>
			{/each}
		{/each}
	</div>
{:catch}
	<div class="flex items-center gap-2 px-4 py-4 text-sm text-red-400">
		<TriangleAlert class="size-4 shrink-0" />
		{$_('budget.load_error')}
	</div>
{/await}
