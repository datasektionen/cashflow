<script lang="ts">
	import type { Expense } from '$lib/api/types.ts';
	import ExpenseTable from "$lib/components/ExpenseTable.svelte";

	let { data } = $props();
	const expenses: Expense[] = data.expenses;
</script>

<ExpenseTable {expenses} />

