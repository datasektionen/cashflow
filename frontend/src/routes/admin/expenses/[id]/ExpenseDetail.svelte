<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Flag } from '@lucide/svelte';
	import { Button, Card, Spinner } from '#lib/components/ui/index.ts';
	import type { Expense, Comment, User } from '#lib/api/types.ts';
	import PartsTable from '#lib/components/PartsTable.svelte';
	import { api } from '#lib/api/index.ts';
	import { failed, success } from '#lib/stores/alerts.ts';
	import ClaimDetailLayout from '#lib/components/claim/ClaimDetailLayout.svelte';
	import CommentsCard from '#lib/components/claim/CommentsCard.svelte';
	import ClaimInfo from '#lib/components/claim/ClaimInfo.svelte';
	import DeleteClaimButton from '#lib/components/claim/DeleteClaimButton.svelte';

	let { expense: initialExpense, user }: { expense: Expense; user: User | null } = $props();
	let expense: Expense = $derived(initialExpense);

	const mayFlag = $derived((user?.permissions.attest.length ?? 0) > 0 || !!user?.permissions.pay);
	const availableActions = $derived({
		confirm: !!user?.permissions.confirm && !expense.confirmed_at,
		unconfirm: !!user?.permissions.unconfirm && !!expense.confirmed_at,
		flag: mayFlag,
		delete:
			(!!user?.permissions.delete || expense.owner.username === user?.username) &&
			!expense.reimbursement
	});

	const hasActions = $derived(Object.values(availableActions).some(Boolean));

	let pending = $state({ confirm: false, flag: false });

	async function act(key: 'confirm' | 'flag', call: () => Promise<void>, message?: string) {
		pending[key] = true;
		try {
			await call();
			if (message) success(message);
			await refresh();
		} catch (e) {
			failed(e, $_('action_failed'));
		} finally {
			pending[key] = false;
		}
	}

	const handleConfirm = () =>
		act('confirm', () => api.expenses.confirm(expense.id), $_('alerts.expense_confirmed'));
	const handleUnconfirm = () =>
		act('confirm', () => api.expenses.unconfirm(expense.id), $_('alerts.expense_unconfirmed'));
	const handleFlag = () => act('flag', () => api.expenses.flag(expense.id));
	const handleUnflag = () =>
		act('flag', () => api.expenses.unflag(expense.id), $_('alerts.expense_unflagged'));

	// svelte-ignore state_referenced_locally
	let comments = $state<Comment[]>(expense.comments);

	// Actions add activity comments server-side; reload so they show up directly
	let latestRefresh = 0;
	async function refresh() {
		const id = ++latestRefresh;
		try {
			const fresh = await api.expenses.get(expense.id);
			if (id !== latestRefresh) return;
			expense = fresh;
			comments = fresh.comments;
		} catch (e) {
			failed(e, $_('action_failed'));
		}
	}
</script>

{#snippet actions()}
	{#if mayFlag}
		<Button
			variant="secondary"
			class="max-lg:flex-1"
			onclick={expense.is_flagged ? handleUnflag : handleFlag}
			disabled={pending.flag}
		>
			{#if pending.flag}<Spinner />{:else}<Flag />{/if}
			{$_(expense.is_flagged ? 'expense_unflag' : 'expense_flag')}
		</Button>
	{/if}

	{#if availableActions.confirm}
		<span
			class="flex max-lg:flex-1"
			title={expense.is_flagged ? $_('confirm_disabled_flagged') : undefined}
		>
			<Button
				class="max-lg:flex-1"
				onclick={handleConfirm}
				disabled={pending.confirm || !!expense.is_flagged}
			>
				{#if pending.confirm}<Spinner />{/if}
				{$_('expense_confirm')}
			</Button>
		</span>
	{:else if availableActions.unconfirm}
		<Button
			variant="secondary"
			class="max-lg:flex-1"
			onclick={handleUnconfirm}
			disabled={pending.confirm}
		>
			{#if pending.confirm}<Spinner />{/if}
			{$_('expense_unconfirm')}
		</Button>
	{/if}

	{#if availableActions.delete}
		<DeleteClaimButton kind="expense" claim={expense} redirect="/admin/expenses/" />
	{/if}
{/snippet}

<ClaimDetailLayout claim={expense} actions={hasActions ? actions : undefined}>
	<Card title={$_('expense_parts')} padded={false}>
		<PartsTable
			parts={expense.parts}
			owner={expense.owner}
			includeAttest={true}
			attestDisabled={!!expense.is_flagged}
			currentUser={user ?? undefined}
			onchange={refresh}
		/>
	</Card>

	<ClaimInfo claim={expense} linkOwner />

	<CommentsCard
		bind:comments
		currentUser={user ?? undefined}
		onSubmit={(content) => api.expenses.comment(expense.id, content)}
	/>
</ClaimDetailLayout>
