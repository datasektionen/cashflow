<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { fade } from 'svelte/transition';
	import type { PageProps } from './$types';
	import ExpenseDetail from './ExpenseDetail.svelte';
	import ExpenseSkeleton from './ExpenseSkeleton.svelte';

	let { data }: PageProps = $props();
</script>

{#await data.expense}
	<ExpenseSkeleton />
{:then expense}
	<div in:fade={{ duration: 50 }}>
		<ExpenseDetail {expense} user={data.user} />
	</div>
{:catch}
	<div class="py-24 text-center text-sm text-red-500">{$_('action_failed')}</div>
{/await}
