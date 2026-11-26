<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { fade } from 'svelte/transition';
	import type { PageProps } from './$types';
	import ExpenseDetail from './ExpenseDetail.svelte';
	import ClaimDetailSkeleton from '#lib/components/claim/ClaimDetailSkeleton.svelte';

	let { data }: PageProps = $props();
</script>

{#await data.expense}
	<ClaimDetailSkeleton />
{:then expense}
	<div in:fade={{ duration: 50 }}>
		<ExpenseDetail {expense} user={data.user} />
	</div>
{:catch}
	<div class="py-24 text-center text-sm text-danger-text">{$_('action_failed')}</div>
{/await}
