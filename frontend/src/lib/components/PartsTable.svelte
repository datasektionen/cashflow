<script lang="ts">
	import { Check } from '@lucide/svelte';
	import type { ExpensePart, InvoicePart, Profile, User } from '$lib/api/types.ts';
	import { _ } from 'svelte-i18n';
	import { api } from '$lib/api';
	import { alerts, error, success } from '$lib/stores/alerts.ts';
	import { sumAmounts } from '$lib/money';
	import CashSpinner from '$lib/components/CashSpinner.svelte';

	export type ClaimPartsTableProps = {
		parts: (ExpensePart | InvoicePart)[];
		owner: Profile;
		currentUser?: User;
		totalAmount?: number;
		includeAttest?: boolean;
		attestDisabled?: boolean;
		partType?: 'expense' | 'invoice';
		dense?: boolean;
	};

	const {
		parts,
		owner,
		currentUser,
		totalAmount,
		includeAttest = false,
		attestDisabled = false,
		partType = 'expense',
		dense = false
	}: ClaimPartsTableProps = $props();

	let currentlyAttesting: Set<number> = $state(new Set());
	let attested: Set<number> = $state(new Set());
	const attestCallback = async (part: ExpensePart) => {
		currentlyAttesting = new Set([...currentlyAttesting, part.id]);
		const attestFn =
			partType === 'invoice'
				? (id: number) => api.invoices.attestPart(id)
				: (id: number) => api.expenses.attestPart(id);
		await attestFn(part.id)
			.then(() => {
				currentlyAttesting = new Set([...currentlyAttesting].filter((id) => id !== part.id));
				attested = new Set([...attested, part.id]);
				alerts.update((a) => [...a, success($_(`alerts.${partType}_part_attested`))]);
			})
			.catch((err) => {
				currentlyAttesting = new Set([...currentlyAttesting].filter((id) => id !== part.id));
				alerts.update((a) => [...a, error(err)]);
			});
	};

	const resolvedTotalAmount = $derived(totalAmount ?? sumAmounts(parts.map((part) => part.amount)));
</script>

<table class={['w-full table-fixed', dense ? 'text-xs' : 'text-sm']}>
	<thead
		class="text-xxs text-left font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
	>
		<tr class="text-xs">
			<td class="py-3 pr-4">{$_('cost_centre')}</td>
			<td class="px-4 py-3">{$_('secondary_cost_centre')}</td>
			<td class="px-4 py-3">{$_('budget_line')}</td>
			<td class="py-3 pl-4 text-right">{$_('amount')}</td>
			{#if includeAttest}<td class="w-40 py-3 pl-4 text-right"></td>{/if}
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
				{#if includeAttest}
					<td class="w-40 py-3 pl-4 text-right">
						{#if attested.has(part.id) || ('attested_by' in part && part.attested_by)}
							{@const attestedBy = attested.has(part.id)
								? (currentUser ?? null)
								: 'attested_by' in part
									? part.attested_by
									: null}
							<div class="flex items-center justify-end gap-1.5">
								<Check class="size-5 shrink-0 text-money-green-500" />
								{#if attestedBy}
									<span class="truncate text-xs text-base-subtle dark:text-dark-base-subtle"
										>{attestedBy.first_name} {attestedBy.last_name}</span
									>
								{/if}
							</div>
						{:else if currentlyAttesting.has(part.id)}
							<CashSpinner />
						{:else}
							{@const mayAttest =
								!!currentUser &&
								currentUser.permissions.attest.includes(part.cost_centre) &&
								owner.username !== currentUser.username}
							{#if mayAttest}
								<button
									onclick={() => attestCallback(part)}
									disabled={attestDisabled}
									title={attestDisabled ? $_('attest_disabled_flagged') : undefined}
									class="cursor-pointer bg-money-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-money-green-500 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-money-green-700 dark:hover:bg-money-green-600"
									>{$_('tasks.attest')}</button
								>
							{/if}
						{/if}
					</td>
				{/if}
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
			{#if includeAttest}<td></td>{/if}
		</tr>
	</tfoot>
</table>
