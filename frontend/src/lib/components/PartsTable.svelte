<script lang="ts">
	import { Check } from '@lucide/svelte';
	import type { ExpensePart, InvoicePart } from '$lib/api/types.ts';
	import { _ } from 'svelte-i18n';

	export type ClaimPartsTableProps = {
		parts: (ExpensePart | InvoicePart)[];
		totalAmount?: number;
	};

	const { parts, totalAmount }: ClaimPartsTableProps = $props();

	const resolvedTotalAmount = $derived(
		totalAmount ?? parts.reduce((sum, part) => sum + parseFloat(part.amount), 0)
	);
</script>

<table class="w-full text-sm">
	<thead
		class="text-xxs text-left font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
	>
		<tr class="text-xs">
			<td class="py-3 pr-4">{$_('cost_centre')}</td>
			<td class="px-4 py-3">{$_('secondary_cost_centre')}</td>
			<td class="px-4 py-3">{$_('budget_line')}</td>
			<td class="py-3 pl-4 text-right">{$_('amount')}</td>
			<td class="w-8 py-3 pl-4"></td>
		</tr>
	</thead>
	<tbody>
		{#each parts as part}
			<tr class="border-t border-base-500 dark:border-dark-base-200">
				<td class="py-3 pr-4 text-left">{part.cost_centre}</td>
				<td class="px-4 py-3 text-left">{part.secondary_cost_centre}</td>
				<td class="px-4 py-3 text-left">{part.budget_line}</td>
				<td class="py-3 pl-4 text-right"
					>{part.amount.toLocaleString()}
					<span class="text-xs text-base-subtle dark:text-dark-base-subtle">SEK</span></td
				>
				<td class="w-8 py-3 pl-4">
					{#if 'attested_by' in part && part.attested_by}
						<Check class="size-4 text-money-green-600" />
					{/if}
				</td>
			</tr>
		{/each}
	</tbody>
	<tfoot>
		<tr class="border-t border-base-500 font-medium dark:border-dark-base-200">
			<td class="py-3 pr-4 text-right" colspan="3">{$_('total')}</td>
			<td class="py-3 pl-4 text-right"
				>{resolvedTotalAmount}
				<span class="text-xs text-base-subtle dark:text-dark-base-subtle">SEK</span></td
			>
		</tr>
	</tfoot>
</table>
