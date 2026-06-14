<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ListRestart } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';
	import ComboBox from '$lib/components/ComboBox.svelte';

	let {
		costCentreItems = [],
		secondaryCostCentreItems = [],
		budgetLineItems = [],
		includeReset = true
	}: {
		costCentreItems?: string[];
		secondaryCostCentreItems?: string[];
		budgetLineItems?: string[];
		includeReset?: boolean;
	} = $props();

	const filterKeys = ['cost_centre', 'secondary_cost_centre', 'budget_line'] as const;

	let resetKey = $state(0);
	let resetting = $state(false);

	function resetFilter() {
		resetting = true;
		resetKey++;
		const url = new URL(page.url);
		for (const key of filterKeys) {
			url.searchParams.delete(key);
		}
		goto(url, { keepFocus: true, noScroll: true, replaceState: true }).then(
			() => (resetting = false)
		);
	}

	function filterValue(key: (typeof filterKeys)[number]) {
		return resetting ? '' : (page.url.searchParams.get(key) ?? '');
	}

	function setFilter(key: (typeof filterKeys)[number], value: string) {
		console.log(`Setting filter ${key} to ${value}`);
		const url = new URL(page.url);
		if (value) {
			url.searchParams.set(key, value);
		} else {
			url.searchParams.delete(key);
		}
		goto(url, { keepFocus: true, noScroll: true, replaceState: true });
	}
</script>

<div
	class="mb-4 flex flex-row items-center space-x-2 border-b border-base-500 pb-4 dark:border-dark-base-200"
>
	{#key resetKey}
		<ComboBox
			class="text-sm"
			value={filterValue('cost_centre')}
			onchange={(v) => setFilter('cost_centre', v)}
			placeholder={$_('cost_centre')}
			items={costCentreItems}
		/>
		<ComboBox
			class="text-sm"
			value={filterValue('secondary_cost_centre')}
			onchange={(v) => setFilter('secondary_cost_centre', v)}
			placeholder={$_('secondary_cost_centre')}
			items={secondaryCostCentreItems}
		/>
		<ComboBox
			class="text-sm"
			value={filterValue('budget_line')}
			onchange={(v) => setFilter('budget_line', v)}
			placeholder={$_('budget_line')}
			items={budgetLineItems}
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
