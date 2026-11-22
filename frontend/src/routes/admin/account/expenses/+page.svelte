<script lang="ts">
	import { _ } from 'svelte-i18n';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data } = $props();
</script>

<ClaimTable
	claims={data.expenses}
	user={data.user!}
	filters={['description', 'reimbursement']}
	excludeColumns={['verification', 'type', 'status']}
	rowHref={(c) => `/admin/account/expenses/${c.id}`}
/>
