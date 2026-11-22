<script lang="ts">
	import type { PageProps } from './$types';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data }: PageProps = $props();
</script>

<ClaimTable
	claims={data.invoices}
	user={data.user}
	filters={['description', 'invoice_number', 'attested', 'paid', 'accounted', 'verification']}
	includeColumns={['__all__', 'due_date']}
	excludeColumns={['verification']}
	layout={{
		xs: ['description', 'amount'],
		sm: ['description', 'owner', 'status'],
		md: ['description', 'owner', 'date', 'status']
	}}
/>
