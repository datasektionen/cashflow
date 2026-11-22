<script lang="ts">
	import type { PageProps } from './$types';
	import ClaimEditForm from '../../../ClaimEditForm.svelte';

	let { data }: PageProps = $props();
</script>

<ClaimEditForm kind="invoice" claim={data.invoice} />
