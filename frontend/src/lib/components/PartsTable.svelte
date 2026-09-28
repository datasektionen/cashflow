<script lang="ts">
	import { Check, X } from '@lucide/svelte';
	import type { BudgetLine, ExpensePart, InvoicePart, Profile, User } from '$lib/api/types';
	import { _ } from 'svelte-i18n';
	import { api } from '$lib/api';
	import { alerts, error, success } from '$lib/stores/alerts';
	import { sumAmounts, formatAmountPlain } from '$lib/money';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import { logger } from '$lib/logger';

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

	// Fetch information about included cost centres
	// This is done to see if any included budget lines are exceeded

	type BudgetEntry = {
		name: string;
		children: {
			name: string;
			children: BudgetLine[];
		}[];
	};

	let blownBudgetLines: Promise<BudgetEntry[]> = $derived.by(() => {
		logger.debug('fetching budget info');
		let uniqueCostCentres: SvelteSet<string> = new SvelteSet<string>();
		parts.forEach((part) => {
			console.log(part.cost_centre);
			uniqueCostCentres.add(part.cost_centre);
		});
		return (
			api.budget
				.listCostCentres(1, 100, { active: true, contains_blown: true })
				.then((res) => {
					logger.debug(res, 'got response');
					return res.data.filter((cc) => uniqueCostCentres.has(cc.name));
				})
				// I regret writing this
				.then((costCentres) => {
					const ids: number[] = [];
					for (const cc of costCentres) {
						if (cc.id != null) {
							ids.push(cc.id);
						}
					}
					return Promise.all(ids.map((id) => api.budget.retrieveCostCentre(id)));
				})
				.then((costCentres) => {
					return costCentres
						.map((cc) => {
							return { name: cc.name, children: cc.secondary_cost_centres ?? [] };
						})
						.map((obj) => {
							return {
								...obj,
								children: obj.children.map((scc) => {
									return {
										name: scc.name,
										children: scc.budget_lines ? scc.budget_lines.filter((bl) => bl.blown) : []
									};
								})
							};
						});
				})
		);
	});

	function partIsBlown(part: ExpensePart | InvoicePart, budget: BudgetEntry[]) {
		return budget
			.find((b) => b.name === part.cost_centre)
			?.children.find((scc) => scc.name === part.secondary_cost_centre)
			?.children.map((bl) => bl.name)
			.includes(part.budget_line);
	}

	let currentlyAttesting: Set<number> = $state(new Set());
	let attested: Set<number> = $state(new Set());
	let currentlyUnattesting: Set<number> = $state(new Set());
	let unattested: Set<number> = $state(new Set());
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
				unattested = new Set([...unattested].filter((id) => id !== part.id));
				alerts.update((a) => [...a, success($_(`alerts.${partType}_part_attested`))]);
			})
			.catch((err) => {
				currentlyAttesting = new Set([...currentlyAttesting].filter((id) => id !== part.id));
				alerts.update((a) => [...a, error(err)]);
			});
	};

	const unattestCallback = async (part: ExpensePart) => {
		currentlyUnattesting = new Set([...currentlyUnattesting, part.id]);
		const unattestFn =
			partType === 'invoice'
				? (id: number) => api.invoices.unattestPart(id)
				: (id: number) => api.expenses.unattestPart(id);
		await unattestFn(part.id)
			.then(() => {
				currentlyUnattesting = new Set([...currentlyUnattesting].filter((id) => id !== part.id));
				unattested = new Set([...unattested, part.id]);
				attested = new Set([...attested].filter((id) => id !== part.id));
				alerts.update((a) => [...a, success($_(`alerts.${partType}_part_unattested`))]);
			})
			.catch((err) => {
				currentlyUnattesting = new Set([...currentlyUnattesting].filter((id) => id !== part.id));
				alerts.update((a) => [...a, error(err)]);
			});
	};

	const resolvedTotalAmount = $derived(totalAmount ?? sumAmounts(parts.map((part) => part.amount)));
</script>

<div class="overflow-x-auto">
	<table class={['w-full min-w-136 table-fixed wrap-break-word', dense ? 'text-xs' : 'text-sm']}>
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
					<td class="py-3 pr-4 text-left">
						<a href="/budget/#{part.cost_centre}" class="hover:underline">
							{part.cost_centre}
						</a>
					</td>
					<td class="px-4 py-3 text-left">
						<a href="/budget/#{part.cost_centre}" class="hover:underline">
							{part.secondary_cost_centre}
						</a>
					</td>
					<td class="flex flex-row px-4 py-3 text-left">
						<a href="/budget/#{part.cost_centre}" class="hover:underline">
							{part.budget_line}
						</a>
						{#await blownBudgetLines then result}
							{#if partIsBlown(part, result)}
								<div
									class="my-auto ml-auto size-2 animate-pulse rounded-full bg-amber-500 opacity-75"
								></div>
							{/if}
						{/await}
					</td>
					<td class="py-3 pl-4 text-right"
						>{formatAmountPlain(part.amount)}
						<span class="text-xs text-base-subtle dark:text-dark-base-subtle">SEK</span></td
					>
					{#if includeAttest}
						<td class="w-40 py-3 pl-4 text-right">
							{#if currentlyUnattesting.has(part.id)}
								<CashSpinner />
							{:else if (attested.has(part.id) || ('attested_by' in part && part.attested_by)) && !unattested.has(part.id)}
								{@const attestedBy = attested.has(part.id)
									? (currentUser ?? null)
									: part.attested_by}
								{@const mayUnattest =
									!!currentUser &&
									currentUser.permissions.attest.includes(part.cost_centre) &&
									(partType === 'invoice' || owner.username !== currentUser.username)}
								<div class="flex items-center justify-end gap-1.5">
									<Check class="size-5 shrink-0 text-money-green-500" />
									{#if attestedBy}
										<span class="truncate text-xs text-base-subtle dark:text-dark-base-subtle"
											>{attestedBy.first_name} {attestedBy.last_name}</span
										>
									{/if}
									{#if mayUnattest}
										<button
											onclick={() => unattestCallback(part)}
											title={$_('tasks.unattest')}
											aria-label={$_('tasks.unattest')}
											class="cursor-pointer rounded-full p-0.5 text-base-subtle transition-colors hover:scale-110 dark:text-dark-base-subtle"
										>
											<X class="size-3.5" />
										</button>
									{/if}
								</div>
							{:else if currentlyAttesting.has(part.id)}
								<CashSpinner />
							{:else}
								{@const mayAttest =
									!!currentUser &&
									currentUser.permissions.attest.includes(part.cost_centre) &&
									(partType === 'invoice' || owner.username !== currentUser.username)}
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
					>{formatAmountPlain(resolvedTotalAmount)}
					<span class="text-xs text-base-subtle dark:text-dark-base-subtle">SEK</span></td
				>
				{#if includeAttest}<td></td>{/if}
			</tr>
		</tfoot>
	</table>
</div>
