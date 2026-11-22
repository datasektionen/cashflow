<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Calendar, CalendarClock, Hash } from '@lucide/svelte';
	import { CopyableValue } from '#lib/components/ui/index.ts';
	import { claimTotal, formatDineroAmount } from '#lib/money.ts';
	import type { Expense, Invoice } from '#lib/api/types.ts';
	import UserLink from '#lib/components/UserLink.svelte';
	import ClaimStatus from './ClaimStatus.svelte';
	import { claimIdLabel } from '#lib/claimId.ts';

	// A claim's id, owner, number, total, dates and status; linkOwner links the owner to their admin page
	let { claim, linkOwner = false }: { claim: Expense | Invoice; linkOwner?: boolean } = $props();

	const total = $derived(formatDineroAmount(claimTotal(claim)));
</script>

<div class="flex flex-wrap items-center gap-1.5">
	<CopyableValue display={claimIdLabel(claim, $_)} value={claim.id} />
	{#if linkOwner}
		<UserLink
			user={claim.owner}
			class="flex h-7 items-center border border-border bg-card px-2 text-xs text-muted-foreground hover:text-foreground"
		/>
	{:else}
		<CopyableValue display="{claim.owner.first_name} {claim.owner.last_name}" />
	{/if}
	{#if 'invoice_number' in claim && claim.invoice_number}
		<CopyableValue
			icon={Hash}
			label={$_('new_invoice.form.invoice_number.label')}
			display={claim.invoice_number}
		/>
	{/if}
	<CopyableValue display="{total} kr" value={total} />
	{#if 'expense_date' in claim}
		<CopyableValue icon={Calendar} label={$_('expense_date')} display={claim.expense_date} />
	{:else}
		{#if claim.invoice_date}
			<CopyableValue
				icon={Calendar}
				label={$_('admin_invoices.columns.invoice_date')}
				display={claim.invoice_date}
			/>
		{/if}
		{#if claim.due_date}
			<CopyableValue
				icon={CalendarClock}
				label={$_('admin_invoices.columns.due_date')}
				display={claim.due_date}
			/>
		{/if}
	{/if}
	<ClaimStatus {claim} size="lg" />
</div>
