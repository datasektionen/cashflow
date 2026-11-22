<script lang="ts">
	import type { PageProps } from './$types';
	import { _ } from 'svelte-i18n';
	import { CircleCheck } from '@lucide/svelte';
	import { page } from '$app/state';
	import { latest } from '#lib/latest.svelte.ts';
	import { EmptyState } from '#lib/components/ui/index.ts';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data }: PageProps = $props();

	const filtered = $derived(
		[...page.url.searchParams.keys()].some((k) => !['page', 'per_page', 'sorting'].includes(k))
	);
	const list = latest(() => data.claims);
</script>

{#if list.value?.pagination.total === 0 && !filtered}
	<EmptyState icon={CircleCheck} title={$_('tasks.empty')} />
{:else}
	<ClaimTable
		claims={data.claims}
		user={data.user}
		filters={['confirmed', 'flagged', 'description', 'invoice_number']}
		excludeColumns={['verification']}
		layout={{ xs: ['description', 'amount'], sm: ['type', 'description', 'owner', 'cost_centres'] }}
	/>
{/if}
