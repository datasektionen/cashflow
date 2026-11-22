<script lang="ts">
	import type { PageProps } from './$types';
	import AccountingDetail from '../../AccountingDetail.svelte';

	let { data }: PageProps = $props();
</script>

<AccountingDetail
	kind="invoice"
	claim={data.claim}
	accounts={data.accounts}
	costCentres={data.costCentres}
	user={data.user}
/>
