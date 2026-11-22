<script lang="ts">
	import type { PageProps } from './$types';
	import OwnerClaimDetail from '#lib/components/claim/OwnerClaimDetail.svelte';

	let { data }: PageProps = $props();
</script>

<OwnerClaimDetail kind="invoice" claim={data.invoice} user={data.user} />
