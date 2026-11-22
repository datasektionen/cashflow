<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Banknote, Check, CheckCheck, Flag } from '@lucide/svelte';
	import { claimProgress, type Claim, type Expense, type Invoice } from '#lib/api/types.ts';
	import { Badge, type BadgeSize } from '#lib/components/ui/index.ts';

	let { claim, size }: { claim: Claim | Expense | Invoice; size?: BadgeSize } = $props();

	const flagged = $derived('is_flagged' in claim && !!claim.is_flagged);
	const progress = $derived(claimProgress(claim));
</script>

<div class="flex flex-wrap gap-1.5">
	{#if flagged}
		<Badge {size} variant="warning"><Flag />{$_('expense_flagged')}</Badge>
	{/if}
	{#if claim.voucher}
		<Badge {size} variant="outline" class="font-mono">{claim.voucher}</Badge>
	{:else if progress.paid}
		<Badge {size} variant="success"><Banknote />{$_('expense_paid')}</Badge>
	{:else if progress.confirmed}
		<Badge {size} variant="success"><CheckCheck />{$_('expense_confirmed')}</Badge>
	{:else if progress.attested}
		<Badge {size} variant="success"><Check />{$_('expense_attested')}</Badge>
	{:else}
		<Badge {size}>{$_('expense_status.unprocessed')}</Badge>
	{/if}
</div>
