<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import {
		ListRestart,
		Search,
		SlidersHorizontal,
		Stamp,
		CircleCheck,
		Banknote,
		Receipt,
		Flag,
		Eraser
	} from '@lucide/svelte';
	import { _ } from 'svelte-i18n';
	import { onMount } from 'svelte';
	import ComboBox from '$lib/components/ComboBox.svelte';
	import TextInput from '$lib/components/TextInput.svelte';
	import Checkbox from '$lib/components/Checkbox.svelte';
	import type { BudgetLine, CostCentre, SecondaryCostCentre } from '$lib/api/types.ts';
	import { api } from '$lib/api';

	let {
		includeReset = true,
		includeChecks = true,
		exclude = []
	}: {
		includeReset?: boolean;
		includeChecks?: boolean;
		exclude?: (typeof tristateKeys)[number][];
	} = $props();

	let showAllFilters: boolean = $state(true);

	let costCentres: CostCentre[] = $state([]);
	let secondaryCostCentres: SecondaryCostCentre[] = $state([]);
	let budgetLines: BudgetLine[] = $state([]);

	onMount(async () => {
		costCentres = await api.budget.listCostCentres(1, 100).then((res) => res.data);

		const selectedCostCentre = costCentres.find((cc) => cc.name === filterValue('cost_centre'));
		secondaryCostCentres = await api.budget
			.listSecondaryCostCentres(
				1,
				100,
				selectedCostCentre?.id != null ? { cost_centre: selectedCostCentre.id } : undefined
			)
			.then((res) => res.data);

		const selectedSecondaryCostCentre = secondaryCostCentres.find(
			(scc) => scc.name === filterValue('secondary_cost_centre')
		);
		budgetLines = await api.budget
			.listBudgetLines(
				1,
				100,
				selectedSecondaryCostCentre?.id != null
					? { secondary_cost_centre: selectedSecondaryCostCentre.id }
					: undefined
			)
			.then((res) => res.data);
	});

	const filterKeys = ['cost_centre', 'secondary_cost_centre', 'budget_line'] as const;

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

	// Each tristate filter (attested, confirmed, paid, accounted, flagged) is a
	// single URL param with three effective states (plus absent = show both):
	// 'true' (only the positive box checked), 'false' (only the negative box
	// checked), 'none' (neither box checked -> match nothing).
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
				costCentre?.id != null
					? await api.budget
							.listSecondaryCostCentres(1, 100, { cost_centre: costCentre.id })
							.then((res) => res.data)
					: [];
			budgetLines = [];
			url.searchParams.delete('secondary_cost_centre');
			url.searchParams.delete('budget_line');
		} else if (key === 'secondary_cost_centre') {
			const secondaryCostCentre = secondaryCostCentres.find((scc) => scc.name === value);
			const filter =
				secondaryCostCentre?.id != null
					? { secondary_cost_centre: secondaryCostCentre.id }
					: undefined;
			budgetLines = await api.budget.listBudgetLines(1, 100, filter).then((res) => res.data);
			url.searchParams.delete('budget_line');
		}

		goto(url, { keepFocus: true, noScroll: true, replaceState: true });
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

<div
	class="mb-4 flex flex-row items-center space-x-2 border-b border-base-500 pb-4 dark:border-dark-base-200"
>
	{#key resetKey}
		<!--        <button-->
		<!--                class="group flex min-w-fit cursor-pointer flex-row items-center gap-1.5 text-base-subtle transition-colors hover:text-base-text dark:text-dark-base-subtle dark:hover:text-dark-base-text"-->
		<!--                onclick={() => showAllFilters = !showAllFilters}-->
		<!--        >-->
		<!--            <SlidersHorizontal class="size-4 shrink-0 transition-transform group-hover:scale-125"/>-->
		<!--            <span class="text-xs">{$_('show_all_filters')}</span>-->
		<!--        </button>-->

		<ComboBox
			class="text-sm"
			value={filterValue('cost_centre')}
			onchange={(v) => setFilter('cost_centre', v)}
			placeholder={$_('cost_centre')}
			items={costCentres.map((it) => it.name)}
		/>
		<ComboBox
			class="text-sm"
			value={filterValue('secondary_cost_centre')}
			onchange={(v) => setFilter('secondary_cost_centre', v)}
			placeholder={$_('secondary_cost_centre')}
			items={secondaryCostCentres.map((it) => it.name)}
		/>
		<ComboBox
			class="text-sm"
			value={filterValue('budget_line')}
			onchange={(v) => setFilter('budget_line', v)}
			placeholder={$_('budget_line')}
			items={budgetLines.map((it) => it.name)}
		/>

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
	{/key}
	{#if includeReset}
		<button
			onclick={resetFilter}
			class="ml-auto flex cursor-pointer flex-row items-center gap-1.5 text-base-subtle transition-colors hover:text-base-text dark:text-dark-base-subtle dark:hover:text-dark-base-text"
		>
			<ListRestart class="size-4" />
			<span class="text-xs uppercase">{$_('reset')}</span>
		</button>
	{/if}
</div>
{#if includeChecks}
	<div
		class="mb-4 flex flex-row items-center space-x-2 border-b border-base-500 pb-4 dark:border-dark-base-200"
	>
		<div
			class="flex flex-1 flex-wrap items-center divide-x divide-base-400 dark:divide-dark-base-150"
		>
			{#if !exclude.includes('attested')}
				<div class="flex items-center gap-1.5 py-1 pr-4">
					<Stamp
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('attested')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
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
			{/if}
			{#if !exclude.includes('confirmed')}
				<div class="flex items-center gap-1.5 py-1 pr-4">
					<CircleCheck
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('confirmed')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
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
			{/if}
			{#if !exclude.includes('paid')}
				<div class="flex items-center gap-1.5 px-4 py-1">
					<Banknote
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('paid')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
					<Checkbox
						checked={tristateChecked('paid', 'true')}
						onCheckedChange={(v) => setTristateFilter('paid', v, tristateChecked('paid', 'false'))}
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
			{/if}
			{#if !exclude.includes('accounted')}
				<div class="flex items-center gap-1.5 px-4 py-1">
					<Receipt
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('accounted')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
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
			{/if}
			{#if !exclude.includes('flagged')}
				<div class="flex items-center gap-1.5 py-1 pl-4">
					<Flag
						class={[
							'size-4 shrink-0 transition-colors',
							tristateActive('flagged')
								? 'text-money-green-600 dark:text-money-green-500'
								: 'text-base-subtle dark:text-dark-base-subtle'
						]}
					/>
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
			{/if}
		</div>
		<button
			onclick={clearTristateFilters}
			class="ml-auto flex shrink-0 cursor-pointer flex-row items-center gap-1.5 text-base-subtle transition-colors hover:text-base-text dark:text-dark-base-subtle dark:hover:text-dark-base-text"
		>
			<Eraser class="size-4" />
			<span class="text-xs uppercase">{$_('clear_all')}</span>
		</button>
	</div>
{/if}
