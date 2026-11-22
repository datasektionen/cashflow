<script lang="ts">
	import type { PageProps } from './$types';
	import { _ } from 'svelte-i18n';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data }: PageProps = $props();
</script>

<ClaimTable
	claims={data.expenses!}
	user={data.user!}
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
/>
