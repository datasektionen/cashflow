<script lang="ts">
	import type { PageProps } from './$types';
	import { _ } from 'svelte-i18n';
	import ClaimTable from '#lib/components/tables/ClaimTable.svelte';

	let { data }: PageProps = $props();
</script>

<ClaimTable
	claims={data.claims}
	user={data.user!}
	filters={['confirmed', 'flagged', 'description', 'invoice_number']}
	excludeColumns={['verification']}
/>
