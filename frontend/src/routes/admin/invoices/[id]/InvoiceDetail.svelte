<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Card } from '#lib/components/ui/index.ts';
	import type { Invoice, Comment, User } from '#lib/api/types.ts';
	import PartsTable from '#lib/components/PartsTable.svelte';
	import { api } from '#lib/api/index.ts';
	import ClaimDetailLayout from '#lib/components/claim/ClaimDetailLayout.svelte';
	import CommentsCard from '#lib/components/claim/CommentsCard.svelte';
	import ClaimInfo from '#lib/components/claim/ClaimInfo.svelte';
	import DeleteClaimButton from '#lib/components/claim/DeleteClaimButton.svelte';

	let { invoice: initialInvoice, user }: { invoice: Invoice; user: User | null } = $props();
	// Writable so handlers can apply local updates; resets if the prop changes
	let invoice: Invoice = $derived(initialInvoice);

	const mayDelete = $derived(
		(!!user?.permissions.delete || invoice.owner.username === user?.username) && !invoice.paid_at
	);

	// svelte-ignore state_referenced_locally
	let comments = $state<Comment[]>(invoice.comments);

	// Attesting adds activity comments server-side; reload so they show up directly
	async function refresh() {
		const fresh = await api.invoices.get(invoice.id);
		invoice = fresh;
		comments = fresh.comments;
	}
</script>

{#snippet actions()}
	<DeleteClaimButton kind="invoice" claim={invoice} redirect="/admin/invoices/" />
{/snippet}

<ClaimDetailLayout claim={invoice} actions={mayDelete ? actions : undefined}>
	<Card title={$_('new_invoice.form.invoice_parts.label')} padded={false}>
		<PartsTable
			parts={invoice.parts}
			owner={invoice.owner}
			includeAttest={true}
			partType="invoice"
			currentUser={user ?? undefined}
			onchange={refresh}
		/>
	</Card>

	<ClaimInfo claim={invoice} linkOwner />

	<CommentsCard
		bind:comments
		currentUser={user ?? undefined}
		onSubmit={(content) => api.invoices.comment(invoice.id, content)}
	/>
</ClaimDetailLayout>
