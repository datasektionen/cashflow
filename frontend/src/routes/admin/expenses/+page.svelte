<script lang="ts">
	import type { PageProps } from './$types';
	import { api } from '$lib/api';
	import ExpenseTable from '$lib/components/ExpenseTable.svelte';

	let { data }: PageProps = $props();

	// svelte-ignore state_referenced_locally
	let expenses = $state(data.expenses);

	async function handlePageChange(page: number) {
		expenses = await api.expenses.list(page, expenses.pagination.perPage);
	}

	async function handlePerPageChange(perPage: number) {
		expenses = await api.expenses.list(1, perPage);
	}
</script>

<ExpenseTable {expenses} onPageChange={handlePageChange} onPerPageChange={handlePerPageChange} />
