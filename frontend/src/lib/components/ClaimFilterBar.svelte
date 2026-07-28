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
		SlidersHorizontal
	} from '@lucide/svelte';
	import { _ } from 'svelte-i18n';
	import { onMount } from 'svelte';
	import ComboBox from '$lib/components/ComboBox.svelte';
	import TextInput from '$lib/components/TextInput.svelte';
	import Checkbox from '$lib/components/Checkbox.svelte';
	import type { ComboboxColumn } from '$lib/components/AdvancedCombobox.svelte';
	import AdvancedCombobox from '$lib/components/AdvancedCombobox.svelte';
	import type { BudgetLine, CostCentre, SecondaryCostCentre, VoucherSeries } from '$lib/api/types';
	import { api } from '$lib/api';
	import {
		cachedCostCentres,
		cachedSecondaryCostCentres,
		cachedBudgetLines
	} from '$lib/stores/state.svelte';
	import { isErrorResponse } from '$lib/api/errors';
	import { alerts, error } from '$lib/stores/alerts';
	import { logger } from '$lib/logger';

	let {
		includeReset = true,
		includeChecks = true,
		exclude = []
	}: {
		includeReset?: boolean;
		includeChecks?: boolean;
		exclude?: ((typeof tristateKeys)[number] | 'voucher_series' | 'voucher_number')[];
	} = $props();

	let showAllFilters: boolean = $state(false);

	// These bind to the comboboxes search strings, and are used to clear e.g. budget line when cost centre is changed
	let budgetSearchValues = $state({
		costCentre: '',
		secondaryCostCentre: '',
		budgetLine: ''
	});

	let costCentres: CostCentre[] = $state([]);
	let secondaryCostCentres: SecondaryCostCentre[] = $state([]);
	let budgetLines: BudgetLine[] = $state([]);

	let voucherSeries: VoucherSeries[] = $state([]);

	// Get-or-fetch helpers backed by the module-level caches shared with the
	// expense form. The cache holds the full list per key; this filter bar shows
	// all of them (incl. inactive), so no client-side filtering is applied.
	async function fetchSecondaryCostCentres(costCentre: CostCentre): Promise<SecondaryCostCentre[]> {
		const existing = cachedSecondaryCostCentres.get(costCentre);
		if (existing != null) {
			logger.debug({ costCentre: costCentre.name }, 'secondary cost centres: cache hit');
			return existing;
		}
		logger.debug({ costCentre: costCentre.name }, 'secondary cost centres: cache miss, fetching');
		const fetched = await api.budget
			.listSecondaryCostCentres(1, 100, { cost_centre: costCentre.id! })
			.then((res) => res.data);
		cachedSecondaryCostCentres.set(costCentre, fetched);
		return fetched;
	}

	async function fetchBudgetLines(secondaryCostCentre: SecondaryCostCentre): Promise<BudgetLine[]> {
		const existing = cachedBudgetLines.get(secondaryCostCentre);
		if (existing != null) {
			logger.debug({ secondaryCostCentre: secondaryCostCentre.name }, 'budget lines: cache hit');
			return existing;
		}
		logger.debug(
			{ secondaryCostCentre: secondaryCostCentre.name },
			'budget lines: cache miss, fetching'
		);
		const fetched = await api.budget
			.listBudgetLines(1, 100, { secondary_cost_centre: secondaryCostCentre.id! })
			.then((res) => res.data);
		cachedBudgetLines.set(secondaryCostCentre, fetched);
		return fetched;
	}

	onMount(async () => {
		if (cachedCostCentres.length === 0) {
			logger.debug('cost centres: cache miss, fetching');
			costCentres = await api.budget.listCostCentres(1, 100).then((res) => res.data);
			cachedCostCentres.push(...costCentres);
		} else {
			logger.debug('cost centres: cache hit');
			costCentres = cachedCostCentres;
		}
		voucherSeries = await api.voucherSeries
			.list(1, 100)
			.then((res) => res.data)
			.catch(async (err) => {
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
				alerts.update((a) => [...a, error($_('voucher_series_fetch_error'))]);
				return [];
			});

		const selectedCostCentre = costCentres.find((cc) => cc.name === filterValue('cost_centre'));
		secondaryCostCentres =
			selectedCostCentre?.id != null
				? await fetchSecondaryCostCentres(selectedCostCentre)
				: await api.budget.listSecondaryCostCentres(1, 100).then((res) => res.data);

		const selectedSecondaryCostCentre = secondaryCostCentres.find(
			(scc) => scc.name === filterValue('secondary_cost_centre')
		);
		budgetLines =
			selectedSecondaryCostCentre?.id != null
				? await fetchBudgetLines(selectedSecondaryCostCentre)
				: await api.budget.listBudgetLines(1, 100).then((res) => res.data);
	});

	const filterKeys = [
		'cost_centre',
		'secondary_cost_centre',
		'budget_line',
		'voucher_series',
		'voucher_number'
	] as const;

	const voucherSeriesColumns: ComboboxColumn<VoucherSeries>[] = [
		{
			label: 'Kod',
			field: 'code',
			render: VoucherSeriesCodeSnippet
		},
		{
			label: 'Beskrivning',
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
		const url = new URL(page.url);
		for (const key of filterKeys) {
			url.searchParams.delete(key);
		}
		url.searchParams.delete('q');
		for (const key of visibleTristateKeys()) {
			url.searchParams.delete(key);
		}
		goto(url, { keepFocus: true, noScroll: true, replaceState: true }).then(
			() => (resetting = false)
		);
	}

	function filterValue(key: string) {
		return resetting ? '' : (page.url.searchParams.get(key) ?? '');
	}

	const tristateKeys = ['attested', 'confirmed', 'paid', 'accounted', 'flagged'] as const;

	function visibleTristateKeys() {
		return tristateKeys.filter((key) => !exclude.includes(key));
	}

	function tristateChecked(key: (typeof tristateKeys)[number], want: 'true' | 'false') {
		const other = want === 'true' ? 'false' : 'true';
		return filterValue(key) !== other && filterValue(key) !== 'none';
	}

	function setTristateFilter(
		key: (typeof tristateKeys)[number],
		positive: boolean,
		negative: boolean
	) {
		if (positive && negative) setFilter(key, '');
		else if (positive) setFilter(key, 'true');
		else if (negative) setFilter(key, 'false');
		else setFilter(key, 'none');
	}

	function tristateActive(key: (typeof tristateKeys)[number]) {
		return filterValue(key) !== '';
	}

	function clearTristateFilters() {
		const url = new URL(page.url);
		for (const key of visibleTristateKeys()) {
			url.searchParams.set(key, 'none');
		}
		goto(url, { keepFocus: true, noScroll: true, replaceState: true });
	}

	async function setFilter(
		key: (typeof filterKeys)[number] | (typeof tristateKeys)[number],
		value: string
	) {
		const url = new URL(page.url);
		if (value) {
			url.searchParams.set(key, value);
		} else {
			url.searchParams.delete(key);
		}

		if (key === 'cost_centre') {
			const costCentre = costCentres.find((cc) => cc.name === value);
			// Cost centres with no GOrdian id (inactive/legacy) can't be used to
			// scope secondary cost centres, so show none rather than the full
			// unfiltered list.
			secondaryCostCentres =
				costCentre?.id != null ? await fetchSecondaryCostCentres(costCentre) : [];
			budgetLines = [];
			budgetSearchValues.secondaryCostCentre = '';
			budgetSearchValues.budgetLine = '';
			url.searchParams.delete('secondary_cost_centre');
			url.searchParams.delete('budget_line');
		} else if (key === 'secondary_cost_centre') {
			const secondaryCostCentre = secondaryCostCentres.find((scc) => scc.name === value);
			budgetLines =
				secondaryCostCentre?.id != null
					? await fetchBudgetLines(secondaryCostCentre)
					: await api.budget.listBudgetLines(1, 100).then((res) => res.data);
			budgetSearchValues.budgetLine = '';
			url.searchParams.delete('budget_line');
		}

		await goto(url, { keepFocus: true, noScroll: true, replaceState: true });
	}

	let queryTimeout: ReturnType<typeof setTimeout>;

	function setQuery(query: string) {
		clearTimeout(queryTimeout);
		queryTimeout = setTimeout(() => {
			const url = new URL(page.url);
			if (query) {
				url.searchParams.set('q', query);
				url.searchParams.delete('page');
			} else {
				url.searchParams.delete('q');
			}
			goto(url, { keepFocus: true, noScroll: true, replaceState: true });
		}, 500);
	}
</script>

{#snippet VoucherSeriesDisplay(vs: VoucherSeries)}
	<span>{vs.code}</span>
	{#if vs.description}
		<span class="dark:dark-base-subtle ml-2 text-xs font-medium text-base-subtle uppercase">
			{vs.description}
		</span>
	{/if}
{/snippet}
{#snippet VoucherSeriesCodeSnippet(vs: VoucherSeries)}
	<span>{vs.code}</span>
{/snippet}
{#snippet VoucherSeriesDescriptionSnippet(vs: VoucherSeries)}
	<span class="dark:dark-base-subtle ml-2 text-xs font-medium text-base-subtle uppercase">
		{vs.description}
	</span>
{/snippet}

<div
	class="mb-4 flex flex-col items-center space-y-1 space-x-2 border-b border-base-500 pb-4 md:flex-row dark:border-dark-base-200"
>
	{#key resetKey}
		<ComboBox
			name="cost-centre"
			class="text-sm"
			value={filterValue('cost_centre')}
			bind:searchValue={budgetSearchValues.costCentre}
			onchange={(v) => setFilter('cost_centre', v)}
			placeholder={$_('cost_centre')}
			items={costCentres.map((it) => it.name)}
		/>
		<ComboBox
			name="secondary-cost-centre"
			class="text-sm"
			value={filterValue('secondary_cost_centre')}
			bind:searchValue={budgetSearchValues.secondaryCostCentre}
			onchange={(v) => setFilter('secondary_cost_centre', v)}
			placeholder={$_('secondary_cost_centre')}
			items={secondaryCostCentres.map((it) => it.name)}
		/>
		<ComboBox
			name="budget-line"
			class="text-sm"
			value={filterValue('budget_line')}
			bind:searchValue={budgetSearchValues.budgetLine}
			onchange={(v) => setFilter('budget_line', v)}
			placeholder={$_('budget_line')}
			items={budgetLines.map((it) => it.name)}
		/>
		{#if !exclude.includes('voucher_series')}
			<AdvancedCombobox
				name="voucher-series"
				class="text-sm"
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
		{#snippet searchIcon()}
			<Search class="size-4" />
		{/snippet}
		<TextInput
			class="text-sm"
			value={filterValue('q')}
			onchange={setQuery}
			placeholder={$_('search_description')}
			icon={searchIcon}
		/>
		{#snippet voucherIcon()}
			<Hash class="size-4" />
		{/snippet}
		{#if !exclude.includes('voucher_number')}
			<TextInput
				class="text-sm"
				value={filterValue('voucher_number')}
				onchange={(v) => setFilter('voucher_number', v ?? '')}
				placeholder={$_('search_voucher_number')}
				icon={voucherIcon}
			/>
		{/if}
	{/key}

	<div class="flex w-full flex-row gap-2 md:justify-between">
		<button
			class="group flex min-w-fit flex-1 cursor-pointer flex-row items-center justify-center gap-1.5 border border-base-500 px-3 py-1.5 text-base-subtle transition-colors hover:text-base-text md:hidden dark:border-dark-base-200 dark:text-dark-base-subtle dark:hover:text-dark-base-text"
			onclick={() => (showAllFilters = !showAllFilters)}
		>
			<SlidersHorizontal class="size-4 shrink-0 transition-transform group-hover:scale-125" />
			<span class="text-xs uppercase">{$_('show_all_filters')}</span>
		</button>

		{#if includeReset}
			<button
				onclick={resetFilter}
				class="group flex min-w-fit flex-1 cursor-pointer flex-row items-center justify-center gap-1.5 border border-base-500 px-3 py-1.5 text-base-subtle transition-colors hover:text-base-text md:flex-none md:justify-start md:border-0 md:px-0 md:py-0 dark:border-dark-base-200 dark:text-dark-base-subtle dark:hover:text-dark-base-text"
			>
				<ListRestart class="size-4 shrink-0 transition-transform group-hover:scale-125" />
				<span class="text-xs uppercase">{$_('reset')}</span>
			</button>
		{/if}
	</div>
</div>
{#if includeChecks}
	<div
		class={[
			'mb-4 flex-col items-start space-x-2 gap-y-3 border-b border-base-500 pb-4 md:flex md:flex-row md:items-center md:gap-y-0 dark:border-dark-base-200',
			showAllFilters ? 'flex' : 'hidden'
		]}
	>
		<div
			class="grid grid-cols-[auto_auto_auto] items-center justify-items-end gap-x-3 gap-y-2.5 md:flex md:flex-1 md:flex-wrap md:justify-items-start md:gap-0 md:divide-x md:divide-base-400 dark:md:divide-dark-base-150"
		>
			{#if !exclude.includes('attested')}
				<div class="contents md:flex md:items-center md:gap-1.5 md:py-1 md:pr-4">
					<Stamp
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('attested')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
					<div class="contents md:flex md:flex-wrap md:items-center md:justify-end md:gap-1.5">
						<Checkbox
							checked={tristateChecked('attested', 'true')}
							onCheckedChange={(v) =>
								setTristateFilter('attested', v, tristateChecked('attested', 'false'))}
						>
							{$_('attested')}
						</Checkbox>
						<Checkbox
							checked={tristateChecked('attested', 'false')}
							onCheckedChange={(v) =>
								setTristateFilter('attested', tristateChecked('attested', 'true'), v)}
						>
							{$_('not_attested')}
						</Checkbox>
					</div>
				</div>
			{/if}
			{#if !exclude.includes('confirmed')}
				<div class="contents md:flex md:items-center md:gap-1.5 md:py-1 md:pr-4">
					<CircleCheck
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('confirmed')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
					<div class="contents md:flex md:flex-wrap md:items-center md:justify-end md:gap-1.5">
						<Checkbox
							checked={tristateChecked('confirmed', 'true')}
							onCheckedChange={(v) =>
								setTristateFilter('confirmed', v, tristateChecked('confirmed', 'false'))}
						>
							{$_('confirmed')}
						</Checkbox>
						<Checkbox
							checked={tristateChecked('confirmed', 'false')}
							onCheckedChange={(v) =>
								setTristateFilter('confirmed', tristateChecked('confirmed', 'true'), v)}
						>
							{$_('not_confirmed')}
						</Checkbox>
					</div>
				</div>
			{/if}
			{#if !exclude.includes('paid')}
				<div class="contents md:flex md:items-center md:gap-1.5 md:px-4 md:py-1">
					<Banknote
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('paid')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
					<div class="contents md:flex md:flex-wrap md:items-center md:justify-end md:gap-1.5">
						<Checkbox
							checked={tristateChecked('paid', 'true')}
							onCheckedChange={(v) =>
								setTristateFilter('paid', v, tristateChecked('paid', 'false'))}
						>
							{$_('paid')}
						</Checkbox>
						<Checkbox
							checked={tristateChecked('paid', 'false')}
							onCheckedChange={(v) => setTristateFilter('paid', tristateChecked('paid', 'true'), v)}
						>
							{$_('not_paid')}
						</Checkbox>
					</div>
				</div>
			{/if}
			{#if !exclude.includes('accounted')}
				<div class="contents md:flex md:items-center md:gap-1.5 md:px-4 md:py-1">
					<Receipt
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('accounted')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
					<div class="contents md:flex md:flex-wrap md:items-center md:justify-end md:gap-1.5">
						<Checkbox
							checked={tristateChecked('accounted', 'true')}
							onCheckedChange={(v) =>
								setTristateFilter('accounted', v, tristateChecked('accounted', 'false'))}
						>
							{$_('accounted')}
						</Checkbox>
						<Checkbox
							checked={tristateChecked('accounted', 'false')}
							onCheckedChange={(v) =>
								setTristateFilter('accounted', tristateChecked('accounted', 'true'), v)}
						>
							{$_('not_accounted')}
						</Checkbox>
					</div>
				</div>
			{/if}
			{#if !exclude.includes('flagged')}
				<div class="contents md:flex md:items-center md:gap-1.5 md:py-1 md:pl-4">
					<Flag
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('flagged')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
					<div class="contents md:flex md:flex-wrap md:items-center md:justify-end md:gap-1.5">
						<Checkbox
							checked={tristateChecked('flagged', 'true')}
							onCheckedChange={(v) =>
								setTristateFilter('flagged', v, tristateChecked('flagged', 'false'))}
						>
							{$_('flagged')}
						</Checkbox>
						<Checkbox
							checked={tristateChecked('flagged', 'false')}
							onCheckedChange={(v) =>
								setTristateFilter('flagged', tristateChecked('flagged', 'true'), v)}
						>
							{$_('not_flagged')}
						</Checkbox>
					</div>
				</div>
			{/if}
		</div>
		<button
			onclick={clearTristateFilters}
			class="flex shrink-0 cursor-pointer flex-row items-center gap-1.5 border border-base-500 px-3 py-1.5 text-base-subtle transition-colors hover:text-base-text md:ml-auto md:border-0 md:px-0 md:py-0 dark:border-dark-base-200 dark:text-dark-base-subtle dark:hover:text-dark-base-text"
		>
			<Eraser class="size-4" />
			<span class="text-xs uppercase">{$_('clear_all')}</span>
		</button>
	</div>
{/if}
