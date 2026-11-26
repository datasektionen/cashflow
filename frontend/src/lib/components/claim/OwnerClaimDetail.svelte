<!--
@component
A claim's detail page for its owner.
-->
<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Pencil } from '@lucide/svelte';
	import type { Comment, Expense, Invoice, User } from '#lib/api/types.ts';
	import PartsTable from '#lib/components/PartsTable.svelte';
	import { Button, Card } from '#lib/components/ui/index.ts';
	import ClaimDetailLayout from './ClaimDetailLayout.svelte';
	import CommentsCard from './CommentsCard.svelte';
	import ClaimInfo from './ClaimInfo.svelte';
	import DeleteClaimButton from './DeleteClaimButton.svelte';
	import { api } from '#lib/api/index.ts';

	let {
		kind,
		claim,
		user
	}: { kind: 'expense' | 'invoice'; claim: Expense | Invoice; user: User | null } = $props();

	const settled = $derived('expense_date' in claim ? !!claim.reimbursement : !!claim.paid_at);
	const own = $derived(claim.owner.username === user?.username);
	const canEdit = $derived(own && !settled);
	const canDelete = $derived((own || !!user?.permissions.delete) && !settled);

	// svelte-ignore state_referenced_locally
	let comments = $state<Comment[]>(claim.comments);
</script>

{#snippet actions()}
	{#if canEdit}
		<Button
			variant="secondary"
			class="max-lg:flex-1"
			href="/{claim.owner.username}/{kind}s/{claim.id}/update"
		>
			<Pencil />
			{$_('edit')}
		</Button>
	{/if}
	{#if canDelete}
		<DeleteClaimButton {kind} {claim} redirect="/claims" />
	{/if}
{/snippet}

<ClaimDetailLayout {claim} actions={canEdit || canDelete ? actions : undefined}>
	<Card
		title={$_(kind === 'invoice' ? 'new_invoice.form.invoice_parts.label' : 'expense_parts')}
		padded={false}
	>
		<PartsTable parts={claim.parts} owner={claim.owner} partType={kind} />
	</Card>

	<ClaimInfo {claim} />

	<CommentsCard
		bind:comments
		currentUser={user ?? undefined}
		onSubmit={(content) => api[`${kind}s`].comment(claim.id, content)}
	/>
</ClaimDetailLayout>
