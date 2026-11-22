<script lang="ts">
	import type { PageProps } from './$types';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data }: PageProps = $props();
</script>

<ClaimTable
	claims={data.expenses}
	user={data.user}
	filters={[
		'description',
		'attested',
		'confirmed',
		'paid',
		'flagged',
		'accounted',
		'reimbursement'
	]}
	excludeColumns={['verification']}
	layout={{ xs: ['description', 'amount'], sm: ['description', 'owner', 'cost_centres'] }}
/>
