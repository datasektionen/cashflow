<script lang="ts">
	import { _ } from 'svelte-i18n';
	import type { User } from '#lib/api/types.ts';
	import { Button, Spinner } from '#lib/components/ui/index.ts';
	import ClaimPreview from '#lib/components/claim/ClaimPreview.svelte';
	import { api } from '#lib/api/index.ts';
	import { mayConfirm } from '#lib/auth.ts';
	import { refreshAll } from '$app/navigation';
	import { failed, success } from '#lib/stores/alerts.ts';

	let {
		expenseId,
		currentUser,
		afterConfirm
	}: { expenseId: number; currentUser?: User; afterConfirm: () => void | Promise<void> } = $props();

	let expense = $derived(api.expenses.get(expenseId));
	let confirming = $state(false);

	async function handleConfirm() {
		confirming = true;
		try {
			await api.expenses.confirm(expenseId);
			success($_('alerts.expense_confirmed'));
			await refreshAll();
			await afterConfirm();
		} catch (e) {
			failed(e, $_('action_failed'));
		} finally {
			confirming = false;
		}
	}
</script>

<ClaimPreview claim={expense} href="/admin/expenses/{expenseId}" {currentUser}>
	{#snippet actions(expense)}
		{#if mayConfirm(currentUser) && !expense.confirmed_at && !expense.is_flagged}
			<Button onclick={handleConfirm} disabled={confirming}>
				{#if confirming}<Spinner />{/if}
				{$_('expense_confirm')}
			</Button>
		{/if}
	{/snippet}
</ClaimPreview>
