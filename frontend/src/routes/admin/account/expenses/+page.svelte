<script lang="ts">
	import { _ } from 'svelte-i18n';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';
	import { setRedirect } from '#lib/stores/state.svelte.js';
	import { page } from '$app/state';

	let { data } = $props();

	let redirectId = $state(crypto.randomUUID().slice(0, 8));

	$effect(() => {
		const url = new URL(page.url.href);
		url.searchParams.set('redirect', redirectId);
		setRedirect({ id: redirectId, url });
	});
</script>

<ClaimTable
	claims={data.expenses}
	user={data.user!}
	filters={['description', 'reimbursement']}
	excludeColumns={['verification', 'type', 'status']}
	rowHref={(c) => `/admin/account/expenses/${c.id}?redirect=${redirectId}`}
/>
