<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { fade } from 'svelte/transition';
	import type { PageProps } from './$types';
	import InvoiceDetail from './InvoiceDetail.svelte';
	import ClaimDetailSkeleton from '#lib/components/claim/ClaimDetailSkeleton.svelte';

	let { data }: PageProps = $props();
</script>

{#await data.invoice}
	<ClaimDetailSkeleton />
{:then invoice}
	<div in:fade={{ duration: 50 }}>
		<InvoiceDetail {invoice} user={data.user} />
	</div>
{:catch}
	<div class="py-24 text-center text-sm text-danger">{$_('action_failed')}</div>
{/await}
