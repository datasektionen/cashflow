<script lang="ts">
	import type { PageProps } from './$types';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data }: PageProps = $props();
</script>

<ClaimTable
	claims={data.claims}
	user={data.user}
	filters={['description', 'invoice_number']}
	layout={{
		xs: ['verification', 'description'],
		sm: ['verification', 'description', 'cost_centres']
	}}
/>
