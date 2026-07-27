<script lang="ts">
	import { _ } from 'svelte-i18n';
	import type { Claim } from '$lib/api/types';
	import StatusPill from '$lib/components/StatusPill.svelte';

	// A claim shows a single pill for its furthest-reached state.
	let { claim }: { claim: Claim } = $props();
</script>

<div class="flex gap-3">
	{#if claim.voucher}
		<StatusPill tone="voucher" label={claim.voucher} mono />
	{:else if claim.is_paid}
		<StatusPill tone="paid" label={$_('expense_paid')} />
	{:else if claim.is_confirmed}
		<StatusPill tone="confirmed" label={$_('expense_confirmed')} />
	{:else if claim.is_attested}
		<StatusPill tone="attested" label={$_('expense_attested')} />
	{:else}
		<StatusPill tone="neutral" label={$_('expense_status.unconfirmed')} />
	{/if}
</div>
