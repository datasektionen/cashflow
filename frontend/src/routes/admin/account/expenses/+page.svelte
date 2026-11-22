<script lang="ts">
	import { _ } from 'svelte-i18n';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';
	import { goto } from '$app/navigation';

	let { data } = $props();
</script>

<ClaimTable
	claims={data.expenses}
	user={data.user!}
	filters={['description', 'reimbursement']}
	excludeColumns={['verification', 'type', 'status']}
	onRowClick={(c) => {
		goto(`/admin/account/expenses/${c.id}`);
	}}
/>
