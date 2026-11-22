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
	claims={data.invoices}
	user={data.user!}
	filters={['description', 'invoice_number']}
	excludeColumns={['verification', 'type', 'status']}
	rowHref={(c) => `/admin/account/invoices/${c.id}?redirect=${redirectId}`}
/>
