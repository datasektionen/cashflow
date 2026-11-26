<script lang="ts">
	import type { PageProps } from './$types';
	import { page } from '$app/state';
	import { setRedirect } from '#lib/stores/state.svelte.ts';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data }: PageProps = $props();

	// Accounting a claim returns here with the same filters
	const redirectId = crypto.randomUUID().slice(0, 8);
	$effect(() => {
		const url = new URL(page.url.href);
		url.searchParams.set('redirect', redirectId);
		setRedirect({ id: redirectId, url });
	});
</script>

<ClaimTable
	claims={data.expenses}
	user={data.user}
	filters={['description', 'reimbursement']}
	excludeColumns={['verification', 'type', 'status']}
	rowHref={(c) => `/admin/account/expenses/${c.id}?redirect=${redirectId}`}
	layout={{ xs: ['description', 'owner'], sm: ['description', 'owner', 'cost_centres'] }}
/>
