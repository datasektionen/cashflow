<script lang="ts">
	import { _ } from 'svelte-i18n';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data } = $props();
</script>

<ClaimTable
	claims={data.invoices}
	user={data.user!}
	filters={['description', 'invoice_number']}
	excludeColumns={['verification', 'type', 'status']}
	rowHref={(c) => `/admin/account/invoices/${c.id}`}
/>
