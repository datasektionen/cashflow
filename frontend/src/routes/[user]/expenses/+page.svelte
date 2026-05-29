<script lang="ts">
	import type { PageProps } from './$types';
	import ExpenseTable from '$lib/components/ExpenseTable.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { alerts, success } from '$lib/stores/alerts';
	import { _ } from 'svelte-i18n';

	let { data }: PageProps = $props();

	if (page.url.searchParams.get('createSuccess') === 'true') {
		alerts.update((a) => [...a, success($_('expense_created'))]);
	}

	let expenses = $derived(data.expenses);

	function handlePageChange(p: number) {
		const url = new URL(page.url);
		url.searchParams.set('page', p.toString());
		goto(url, { keepFocus: true, noScroll: true });
	}

	function handlePerPageChange(perPage: number) {
		const url = new URL(page.url);
		url.searchParams.set('per_page', perPage.toString());
		url.searchParams.set('page', '1');
		goto(url, { keepFocus: true, noScroll: true });
	}
</script>

<ExpenseTable {expenses} onPageChange={handlePageChange} onPerPageChange={handlePerPageChange} />
