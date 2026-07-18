<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { ExternalLink } from '@lucide/svelte';
	import type { Expense, User } from '$lib/api/types.ts';
	import ReceiptViewer from '$lib/components/ReceiptViewer.svelte';
	import CommentDisplay from '$lib/components/CommentDisplay.svelte';
	import PartsTable from '$lib/components/PartsTable.svelte';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import { api } from '$lib/api';
	import { invalidateAll } from '$app/navigation';
	import { logger } from '$lib/logger';
	import { alerts, error, success } from '$lib/stores/alerts.ts';
	import { isErrorResponse } from '$lib/api/errors.ts';
	import UserLink from '$lib/components/UserLink.svelte';

	let { expenseId, currentUser }: { expenseId: number; currentUser?: User } = $props();

	let expensePromise = $derived(api.expenses.get(expenseId));

	let confirming = $state(false);

	async function handleConfirm(expense: Expense) {
		confirming = true;
		try {
			await api.expenses.confirm(expense.id);
			alerts.update((a) => [...a, success($_('alerts.expense_confirmed'))]);
			await invalidateAll();
		} catch (e) {
			logger.error(e);
			const msg = isErrorResponse(e) ? e.detail : $_('action_failed');
			alerts.update((a) => [...a, error(msg)]);
		} finally {
			confirming = false;
		}
	}
</script>

{#await expensePromise}
	<div class="flex justify-center py-24"><CashSpinner /></div>
{:then expense}
	{@const canConfirm =
		!!currentUser?.permissions.confirm && !expense.confirmed_at && !expense.is_flagged}
	<div class="flex flex-col gap-6">
		<div class="flex flex-wrap items-center justify-between gap-3">
			<div class="flex items-center gap-2 text-sm text-base-subtle dark:text-dark-base-subtle">
				<span>{$_('expense')} #{expense.id}</span>
				<span>·</span>
				<span><UserLink user={expense.owner} /></span>
			</div>
			<div class="flex items-center gap-2">
				<a
					href="/admin/expenses/{expense.id}"
					class="flex cursor-pointer items-center gap-2 border border-base-500 px-3 py-1.5 text-xs font-medium text-base-subtle transition-colors hover:text-base-text dark:border-dark-base-300 dark:text-dark-base-subtle dark:hover:text-dark-base-text"
				>
					{$_('admin_confirmable.preview.open_detail')}
					<ExternalLink class="size-3.5" />
				</a>
				{#if canConfirm}
					<button
						onclick={() => handleConfirm(expense)}
						disabled={confirming}
						class="flex cursor-pointer items-center gap-1.5 bg-money-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-money-green-500 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-money-green-700 dark:hover:bg-money-green-600"
					>
						{#if confirming}
							<CashSpinner />
						{:else}
							{$_('expense_confirm')}
						{/if}
					</button>
				{/if}
			</div>
		</div>

		<div class="flex max-h-128 flex-col border">
			{#if expense.files.length > 0}
				<ReceiptViewer source={expense.files.map((f) => f.file)} />
			{:else}
				<div
					class="flex flex-1 items-center justify-center p-8 text-sm text-base-subtle dark:text-dark-base-subtle"
				>
					{$_('expense_no_files')}
				</div>
			{/if}
		</div>

		<div>
			<h2 class="text-base font-semibold">{$_('expense_parts')}</h2>
			<PartsTable parts={expense.parts} owner={expense.owner} {currentUser} />
		</div>

		<div>
			<h2 class="text-base font-semibold">{$_('expense_comments')}</h2>
			<CommentDisplay comments={expense.comments} {currentUser} />
		</div>
	</div>
{:catch e}
	<div class="py-24 text-center text-sm text-red-500">{$_('action_failed')}</div>
{/await}
