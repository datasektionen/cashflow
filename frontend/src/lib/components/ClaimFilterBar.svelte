<script module lang="ts">
	import { TRISTATE_KEYS } from '#lib/api/claimFilter.ts';

	export type Filter =
		| (typeof TRISTATE_KEYS)[number]
		| 'voucher_series'
		| 'reimbursement'
		| 'description'
		| 'verification'
		| 'invoice_number';
</script>

<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import {
		Banknote,
		CircleCheck,
		Eraser,
		Flag,
		Hash,
		ListRestart,
		Receipt,
		Search,
		Stamp,
		SlidersHorizontal,
		HandCoins,
		FileDigit
	} from '@lucide/svelte';
	import { _ } from 'svelte-i18n';
	import { onMount } from 'svelte';
	import TextInput from '#lib/components/TextInput.svelte';
	import type { ComboboxColumn } from '#lib/components/AdvancedCombobox.svelte';
	import AdvancedCombobox from '#lib/components/AdvancedCombobox.svelte';
	import type {
		BudgetLine,
		CostCentre,
		SecondaryCostCentre,
		VoucherSeries
	} from '#lib/api/types.ts';
	import { api } from '#lib/api/index.ts';
	import { fetchAllPages } from '#lib/api/util.ts';
	import { budget } from '#lib/stores/budget.ts';
	import { isErrorResponse } from '#lib/api/errors.ts';
	import { error } from '#lib/stores/alerts.ts';
	import { logger } from '#lib/logger.ts';
	import { Button, Checkbox, Combobox } from '#lib/components/ui/index.ts';

	let {
		includeBudget = true,
		includeChecks = true,
		exclude = []
	}: {
		includeBudget?: boolean;
		includeChecks?: boolean;
		exclude?: Filter[];
	} = $props();

	const showChecks = $derived(
		includeChecks && !TRISTATE_KEYS.every((key) => exclude.includes(key))
	);

	let showAllFilters: boolean = $state(false);

	let costCentres: CostCentre[] = $state([]);
	let secondaryCostCentres: SecondaryCostCentre[] = $state([]);
	let budgetLines: BudgetLine[] = $state([]);

	let voucherSeries: VoucherSeries[] = $state([]);

	// The fallback budget line list spans all secondary cost centres, so names can repeat
	const names = (items: { name: string }[]) => [...new Set(items.map((it) => it.name))];

	onMount(async () => {
		costCentres = await budget.costCentres();

		voucherSeries = await fetchAllPages((page, perPage) =>
			api.voucherSeries.list(page, perPage)
		).catch(async (err) => {
			if (isErrorResponse(err)) {
				logger.error(err);
				if (err.type.endsWith('/fortnox_service_not_available/')) {
					// Attempt to fetch voucher series from existing expenses instead
					try {
						return await api.voucherSeries.list(1, 100, false).then((res) => res.data);
					} catch (fallbackErr) {
						logger.error(fallbackErr);
					}
				}
			}
			error($_('voucher_series_fetch_error'));
			return [];
		});

		const selectedCostCentre = costCentres.find((cc) => cc.name === filterValue('cost_centre'));
		if (selectedCostCentre) {
			secondaryCostCentres = await budget.secondaryCostCentres(selectedCostCentre);
		}

		const selectedSecondaryCostCentre = secondaryCostCentres.find(
			(scc) => scc.name === filterValue('secondary_cost_centre')
		);
		if (selectedSecondaryCostCentre) {
			budgetLines = await budget.budgetLines(selectedSecondaryCostCentre);
		}
	});

	const filterKeys = [
		'cost_centre',
		'secondary_cost_centre',
		'budget_line',
		'voucher_series',
		'verification',
		'reimbursement',
		'invoice_number'
	] as const;

	const textFilters = [
		{ key: 'invoice_number', icon: FileDigit, placeholder: 'search_invoice_number' },
		{ key: 'verification', icon: Hash, placeholder: 'search_voucher_number' },
		{ key: 'reimbursement', icon: HandCoins, placeholder: 'search_reimbursement' }
	] as const;

	const voucherSeriesColumns: ComboboxColumn<VoucherSeries>[] = [
		{
			field: 'code',
			render: VoucherSeriesCodeSnippet
		},
		{
			field: 'description',
			render: VoucherSeriesDescriptionSnippet
		}
	];

	let resetKey = $state(0);
	let resetting = $state(false);

	function resetFilter() {
		clearTimeout(queryTimeout);
		resetting = true;
		resetKey++;
		navigate((params) => {
			for (const key of [...filterKeys, 'q', ...visibleTristateKeys()]) params.delete(key);
		}, false).then(() => (resetting = false));
	}

	function filterValue(key: string) {
		return resetting ? '' : (page.url.searchParams.get(key) ?? '');
	}

	function visibleTristateKeys() {
		return TRISTATE_KEYS.filter((key) => !exclude.includes(key));
	}

	function tristateChecked(key: (typeof TRISTATE_KEYS)[number], want: 'true' | 'false') {
		const other = want === 'true' ? 'false' : 'true';
		return filterValue(key) !== other && filterValue(key) !== 'none';
	}

	const setTristateFilter = (
		key: (typeof TRISTATE_KEYS)[number],
		positive: boolean,
		negative: boolean
	) => setFilter(key, positive ? (negative ? '' : 'true') : negative ? 'false' : 'none');

	const tristateFilters = [
		{ key: 'attested', icon: Stamp },
		{ key: 'confirmed', icon: CircleCheck },
		{ key: 'paid', icon: Banknote },
		{ key: 'accounted', icon: Receipt },
		{ key: 'flagged', icon: Flag }
	] as const;

	function navigate(update: (params: URLSearchParams) => void, resetPage = true) {
		const url = new URL(page.url.href);
		update(url.searchParams);
		if (resetPage) url.searchParams.delete('page');
		return goto(url, { reset: false, replaceState: true });
	}

	const clearTristateFilters = () =>
		navigate((params) => {
			for (const key of visibleTristateKeys()) params.set(key, 'none');
		});

	async function setFilter(
		key: (typeof filterKeys)[number] | (typeof TRISTATE_KEYS)[number] | 'q',
		value: string
	) {
		if (key === 'cost_centre') {
			const costCentre = costCentres.find((cc) => cc.name === value);
			secondaryCostCentres = costCentre ? await budget.secondaryCostCentres(costCentre) : [];
			budgetLines = [];
		} else if (key === 'secondary_cost_centre') {
			const secondaryCostCentre = secondaryCostCentres.find((scc) => scc.name === value);
			budgetLines =
				secondaryCostCentre?.id != null
					? await budget.budgetLines(secondaryCostCentre)
					: await api.budget.listBudgetLines(1, 100).then((res) => res.data);
		}

		await navigate((params) => {
			if (value) params.set(key, value);
			else params.delete(key);
			// Clear the filters below the changed one
			if (key === 'cost_centre') params.delete('secondary_cost_centre');
			if (key === 'cost_centre' || key === 'secondary_cost_centre') params.delete('budget_line');
		});
	}

	let queryTimeout: ReturnType<typeof setTimeout>;

	function setQuery(query: string) {
		clearTimeout(queryTimeout);
		queryTimeout = setTimeout(() => setFilter('q', query), 500);
	}
</script>

{#snippet VoucherSeriesDisplay(vs: VoucherSeries)}
	<span>{vs.code}</span>
	{#if vs.description}
		<span class="ml-2 truncate text-xs text-muted-foreground">{vs.description}</span>
	{/if}
{/snippet}
{#snippet VoucherSeriesCodeSnippet(vs: VoucherSeries)}
	<span class="font-mono">{vs.code}</span>
{/snippet}
{#snippet VoucherSeriesDescriptionSnippet(vs: VoucherSeries)}
	<span class="text-xs text-muted-foreground">{vs.description}</span>
{/snippet}

<!-- The full budget loads once someone heads for the filters, not on every list -->
<div
	role="search"
	class="mb-4 flex flex-col gap-3"
	onpointerenter={budget.preload}
	onfocusin={budget.preload}
>
	<div class="flex flex-col gap-2 md:flex-row md:items-start">
		<div class="flex flex-1 flex-wrap gap-2 *:min-w-0 *:flex-[1_1_13rem]">
			{#key resetKey}
				{#if includeBudget}
					<Combobox
						clearable
						name="cost-centre"
						value={filterValue('cost_centre')}
						onchange={(v) => setFilter('cost_centre', v)}
						placeholder={$_('cost_centre')}
						items={names(costCentres)}
					/>
					<Combobox
						clearable
						name="secondary-cost-centre"
						value={filterValue('secondary_cost_centre')}
						onchange={(v) => setFilter('secondary_cost_centre', v)}
						placeholder={$_('secondary_cost_centre')}
						items={names(secondaryCostCentres)}
						locked={filterValue('cost_centre') === ''}
						class={filterValue('cost_centre') === '' ? 'max-md:hidden' : undefined}
					/>
					<Combobox
						clearable
						name="budget-line"
						value={filterValue('budget_line')}
						onchange={(v) => setFilter('budget_line', v)}
						placeholder={$_('budget_line')}
						items={names(budgetLines)}
						locked={filterValue('secondary_cost_centre') === ''}
						class={filterValue('secondary_cost_centre') === '' ? 'max-md:hidden' : undefined}
					/>
				{/if}

				{#if !exclude.includes('voucher_series')}
					<AdvancedCombobox
						clearable
						name="voucher-series"
						columns={voucherSeriesColumns}
						items={voucherSeries}
						searchField={['code', 'description']}
						valueField="code"
						value={filterValue('voucher_series')}
						onchange={(v) => setFilter('voucher_series', v ?? '')}
						display={VoucherSeriesDisplay}
						placeholder={$_('voucher_series')}
					/>
				{/if}

				{#if !exclude.includes('description')}
					<TextInput
						value={filterValue('q')}
						onchange={setQuery}
						placeholder={$_('search_description')}
						icon={Search}
					/>
				{/if}

				{#each textFilters.filter((f) => !exclude.includes(f.key)) as filter (filter.key)}
					<TextInput
						value={filterValue(filter.key)}
						onchange={(v) =>
							setFilter(filter.key, filter.key === 'reimbursement' ? v.replace(/^data/i, '') : v)}
						placeholder={$_(filter.placeholder)}
						icon={filter.icon}
					/>
				{/each}
			{/key}
		</div>

		<div class="flex gap-2 md:shrink-0">
			{#if showChecks}
				<Button
					variant="secondary"
					class="flex-1 md:hidden"
					onclick={() => (showAllFilters = !showAllFilters)}
					aria-expanded={showAllFilters}
				>
					<SlidersHorizontal />
					{$_('show_all_filters')}
				</Button>
			{/if}
			<Button variant="secondary" class="flex-1 md:flex-none" onclick={resetFilter}>
				<ListRestart />
				{$_('reset')}
			</Button>
		</div>
	</div>

	{#if showChecks}
		<div
			class={[
				'flex-col items-start gap-3 border border-border bg-card px-3 py-2.5 md:flex md:flex-row md:items-center',
				showAllFilters ? 'flex' : 'hidden'
			]}
		>
			<div
				class="grid w-full auto-rows-[2.5rem] grid-cols-[auto_1fr_1fr] gap-x-3 md:flex md:flex-1 md:flex-wrap md:items-center md:gap-y-2 md:divide-x md:divide-border"
			>
				{#each tristateFilters.filter((f) => !exclude.includes(f.key)) as filter (filter.key)}
					<div class="contents md:flex md:items-center md:gap-3 md:pr-4 md:not-first:pl-4">
						<filter.icon
							class={[
								'size-4 shrink-0 self-center transition-colors',
								filterValue(filter.key) !== '' ? 'text-primary-text' : 'text-muted-foreground'
							]}
						/>
						<Checkbox
							checked={tristateChecked(filter.key, 'true')}
							onCheckedChange={(v) =>
								setTristateFilter(filter.key, v, tristateChecked(filter.key, 'false'))}
						>
							{$_(filter.key)}
						</Checkbox>
						<Checkbox
							checked={tristateChecked(filter.key, 'false')}
							onCheckedChange={(v) =>
								setTristateFilter(filter.key, tristateChecked(filter.key, 'true'), v)}
						>
							{$_(`not_${filter.key}`)}
						</Checkbox>
					</div>
				{/each}
			</div>
			<Button
				variant="ghost"
				size="sm"
				class="shrink-0 text-muted-foreground md:ml-auto"
				onclick={clearTristateFilters}
			>
				<Eraser />
				{$_('clear_all')}
			</Button>
		</div>
	{/if}
</div>
