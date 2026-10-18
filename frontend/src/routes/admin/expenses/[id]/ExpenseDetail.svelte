<script lang="ts">
	import { _, locale } from 'svelte-i18n';
	import { Check, Flag, MessageSquarePlus, Trash } from '@lucide/svelte';
	import CopyableValue from '$lib/components/ui/CopyableValue.svelte';
	import { formatDineroAmount, sumDinero } from '$lib/money';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import type { Expense, Comment, User } from '$lib/api/types';
	import ReceiptViewer from '$lib/components/ReceiptViewer.svelte';
	import CommentDisplay from '$lib/components/CommentDisplay.svelte';
	import PartsTable from '$lib/components/PartsTable.svelte';
	import { api } from '$lib/api';
	import { logger } from '$lib/logger';
	import { alerts, error, success } from '$lib/stores/alerts';
	import { isErrorResponse } from '$lib/api/errors';
	import UserLink from '$lib/components/UserLink.svelte';
	import Dialog from '$lib/components/Dialog.svelte';
	import { Dialog as DialogPrimitive } from 'bits-ui';
	import { goto } from '$app/navigation';
	import { tick } from 'svelte';

	let { expense: initialExpense, user }: { expense: Expense; user: User | null } = $props();
	let expense: Expense = $derived(initialExpense);

	const totalAmount = $derived(sumDinero(expense.parts.map((part) => part.amount)));

	const expenseStatus: {
		attested: boolean;
		confirmedDisabled: boolean;
	} = $derived({
		attested: expense.parts.length > 0 && expense.parts.every((p) => p.attested_by != null),
		confirmedDisabled: !!expense.is_flagged
	});

	const availableActions: {
		confirm: boolean;
		unconfirm: boolean;
		flag: boolean;
		unflag: boolean;
		delete: boolean;
	} = $derived({
		confirm: !!user?.permissions.confirm && !expense.confirmed_at,
		unconfirm: !!user?.permissions.unconfirm && !!expense.confirmed_at,
		flag:
			((user?.permissions.attest.length ?? 0) > 0 || !!user?.permissions.pay) &&
			!expense.is_flagged,
		unflag:
			((user?.permissions.attest.length ?? 0) > 0 || !!user?.permissions.pay) &&
			!!expense.is_flagged,
		delete:
			(!!user?.permissions.delete || expense.owner.username === user?.username) &&
			!expense.reimbursement
	});

	let pending = $state({ confirm: false, flag: false, delete: false, comment: false });

	async function handleConfirm() {
		pending.confirm = true;
		await api.expenses
			.confirm(expense.id)
			.then(() => {
				expense = { ...expense, confirmed_at: new Date().toISOString(), confirmed_by: user };
				alerts.update((a) => [...a, success($_('alerts.expense_confirmed'))]);
			})
			.catch((e) => {
				logger.error(e);
				const msg = isErrorResponse(e) ? e.detail : $_('action_failed');
				alerts.update((a) => [...a, error(msg)]);
			})
			.finally(() => (pending.confirm = false));
	}

	async function handleUnconfirm() {
		pending.confirm = true;
		await api.expenses
			.unconfirm(expense.id)
			.then(() => {
				expense = { ...expense, confirmed_at: null, confirmed_by: null };
				alerts.update((a) => [...a, success($_('alerts.expense_unconfirmed'))]);
			})
			.catch((e) => {
				logger.error(e);
				const msg = isErrorResponse(e) ? e.detail : $_('action_failed');
				alerts.update((a) => [...a, error(msg)]);
			})
			.finally(() => (pending.confirm = false));
	}

	async function handleFlag() {
		pending.flag = true;
		await api.expenses
			.flag(expense.id)
			.then(() => {
				expense = { ...expense, is_flagged: true };
			})
			.catch((e) => {
				logger.error(e);
				const msg = isErrorResponse(e) ? e.detail : $_('action_failed');
				alerts.update((a) => [...a, error(msg)]);
			})
			.finally(() => (pending.flag = false));
	}

	async function handleUnflag() {
		pending.flag = true;
		await api.expenses
			.unflag(expense.id)
			.then(() => {
				expense = { ...expense, is_flagged: false };
				alerts.update((a) => [...a, success($_('alerts.expense_unflagged'))]);
			})
			.catch((e) => {
				logger.error(e);
				const msg = isErrorResponse(e) ? e.detail : $_('action_failed');
				alerts.update((a) => [...a, error(msg)]);
			})
			.finally(() => (pending.flag = false));
	}

	async function handleDelete() {
		pending.delete = true;
		await api.expenses
			.delete(expense.id)
			.then(() => {
				alerts.update((a) => [
					...a,
					success($_('alerts.expense_delete', { values: { description: expense.description } }))
				]);
				goto('/admin/expenses/');
			})
			.catch((e) => {
				logger.error(e);
				const msg = isErrorResponse(e) ? e.detail : $_('action_failed');
				alerts.update((a) => [...a, error(msg)]);
			})
			.finally(() => (pending.delete = false));
	}

	// svelte-ignore state_referenced_locally
	let comments = $state<Comment[]>(expense.comments);
	let showCommentForm = $state(false);
	let commentContent: string = $state('');

	const commentSubmit = async () => {
		pending.comment = true;
		await api.expenses
			.comment(expense.id, commentContent)
			.then(async (comment) => {
				comments.push(comment);
				showCommentForm = false;
				commentContent = '';
				alerts.update((a) => [...a, success($_('comment_submitted'))]);
				pending.comment = false;
				await tick();

				// Scroll to new comment
				const element = document.getElementById(`comment-${comments.length - 1}`);
				if (element) {
					logger.debug(element, 'Scrolling to new comment');
					element.scrollIntoView({ behavior: 'smooth' });
				} else {
					logger.warn('New comment element not found');
				}
			})
			.catch((e) => {
				logger.error(e);
				const msg = isErrorResponse(e) ? e.detail : $_('comment_submission_failed');
				alerts.update((a) => [...a, error(msg)]);
				pending.comment = false;
			});
	};
</script>

<div class="mb-6 flex flex-wrap items-center justify-between gap-3">
	<div class="flex flex-col items-start gap-3">
		<div class="flex w-full flex-col items-stretch gap-2 sm:flex-row sm:flex-wrap sm:items-center">
			<CopyableValue display={`${$_('expense')} #${expense.id}`} value={expense.id} />
			<CopyableValue display={`${expense.owner.first_name} ${expense.owner.last_name}`} />
			<CopyableValue display={expense.description} />
			<CopyableValue
				display={formatDineroAmount(totalAmount)}
				value={formatDineroAmount(totalAmount)}
			/>
			<CopyableValue display={expense.expense_date} />
		</div>
		<div class="flex items-center gap-2">
			{#if expenseStatus.attested}
				<span
					class="bg-money-green-200 px-2.5 py-0.5 text-xs font-semibold text-money-green-900 dark:bg-money-green-600 dark:text-white"
					>{$_('expense_attested')}</span
				>
			{/if}
			{#if expense.confirmed_at}
				<span
					class="dark:text-money-green-950 bg-money-green-500 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-400"
					>{$_('expense_confirmed')}</span
				>
			{/if}
			{#if expense.is_flagged}
				<span
					class="bg-amber-200 px-2.5 py-0.5 text-xs font-semibold text-amber-900 dark:bg-amber-900 dark:text-amber-200"
					>{$_('expense_flagged')}</span
				>
			{/if}
			{#if expense.payment}
				<span
					class="dark:text-money-green-950 bg-money-green-700 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-300"
					>{$_('expense_paid')}</span
				>
			{/if}
			{#if expense.voucher}
				<span
					class="bg-money-green-900 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-200 dark:text-money-green-900"
					>{expense.voucher}</span
				>
			{/if}
			{#if !expenseStatus.attested && !expense.confirmed_at && !expense.payment && !expense.voucher}
				<span
					class="bg-base-300 px-2.5 py-0.5 text-xs font-semibold text-base-subtle dark:bg-dark-base-300 dark:text-dark-base-subtle"
					>{$_('expense_status.unprocessed')}</span
				>
			{/if}
		</div>
	</div>

	{#snippet deleteTitle()}
		<h1 class="text-xl font-medium text-base-text dark:text-dark-base-text">
			{$_('expense_delete_confirm_title')}
		</h1>
	{/snippet}
	{#snippet deleteDescription()}
		<p class="text-base-subtle dark:text-dark-base-subtle">
			{$_('expense_delete_confirm_description')}
		</p>
	{/snippet}
	{#snippet deleteTrigger()}
		<button
			disabled={!availableActions.delete}
			class="flex cursor-pointer items-center gap-1.5 border border-red-900 px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-red-900 dark:text-red-400 dark:hover:bg-red-950"
		>
			<Trash class="size-3.5" />
		</button>
	{/snippet}
	{#snippet deleteButtons()}
		<div class="mt-6 flex justify-end gap-2">
			<DialogPrimitive.Close
				class="cursor-pointer border border-base-500 px-3 py-1.5 text-xs font-medium text-base-subtle dark:border-dark-base-500 dark:text-dark-base-subtle"
			>
				{$_('cancel')}
			</DialogPrimitive.Close>
			<button
				onclick={handleDelete}
				disabled={pending.delete}
				class="flex cursor-pointer items-center gap-1.5 bg-red-500 px-3 py-1.5 text-xs font-medium text-white transition-all hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-50"
			>
				{#if pending.delete}
					<CashSpinner />
				{:else}
					{$_('expense_delete_confirm_action')}
				{/if}
			</button>
		</div>
	{/snippet}
	<div class="flex items-center gap-2">
		<Dialog title={deleteTitle} triggerContent={deleteTrigger} description={deleteDescription}>
			{@render deleteButtons()}
		</Dialog>

		{#if availableActions.unflag}
			<button
				onclick={handleUnflag}
				disabled={pending.flag}
				class="flex cursor-pointer items-center gap-1.5 border border-amber-600 px-3 py-1.5 text-xs font-medium text-amber-800 hover:bg-amber-50 disabled:opacity-50 dark:border-amber-600 dark:text-amber-400 dark:hover:bg-amber-950"
			>
				{#if pending.flag}
					<CashSpinner></CashSpinner>
				{:else}
					<Flag class="size-3.5" />
					{$_('expense_unflag')}
				{/if}
			</button>
		{:else if availableActions.flag}
			<button
				onclick={handleFlag}
				disabled={pending.flag}
				class="flex cursor-pointer items-center gap-1.5 border border-base-500 px-3 py-1.5 text-xs font-medium text-base-subtle hover:border-amber-500 hover:text-amber-700 disabled:opacity-50 dark:border-dark-base-300 dark:text-dark-base-subtle dark:hover:border-amber-600 dark:hover:text-amber-400"
			>
				{#if pending.flag}
					<CashSpinner />
				{:else}
					<Flag class="size-3.5" />
					{$_('expense_flag')}
				{/if}
			</button>
		{/if}
		{#if availableActions.confirm}
			<button
				onclick={handleConfirm}
				disabled={pending.confirm || expenseStatus.confirmedDisabled}
				title={expenseStatus.confirmedDisabled ? $_('confirm_disabled_flagged') : undefined}
				class="flex cursor-pointer items-center gap-1.5 bg-money-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-money-green-500 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-money-green-700 dark:hover:bg-money-green-600"
			>
				{#if pending.confirm}
					<CashSpinner />
				{:else}
					{$_('expense_confirm')}
				{/if}
			</button>
		{:else if availableActions.unconfirm}
			<button
				onclick={handleUnconfirm}
				disabled={pending.confirm}
				class="flex cursor-pointer items-center gap-1.5 border border-base-500 px-3 py-1.5 text-xs font-medium text-base-subtle hover:border-red-400 hover:text-red-600 disabled:opacity-50 dark:border-dark-base-300 dark:text-dark-base-subtle dark:hover:border-red-500 dark:hover:text-red-400"
			>
				{#if pending.confirm}
					<CashSpinner />
				{:else}
					{$_('expense_unconfirm')}
				{/if}
			</button>
		{/if}
	</div>
</div>

<div class="flex flex-col gap-4 lg:flex-row">
	<div class="flex max-h-256 flex-col lg:w-1/3">
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

	<div class="flex flex-col gap-12 lg:w-2/3 lg:pt-1 xl:pr-16">
		<div>
			<h2 class="text-base font-semibold">{$_('expense_parts')}</h2>
			<PartsTable
				parts={expense.parts}
				owner={expense.owner}
				includeAttest={true}
				attestDisabled={!!expense.is_flagged}
				currentUser={user ?? undefined}
			/>
		</div>

		<div>
			<h2 class="border-t border-base-500 pt-4 text-base font-semibold dark:border-dark-base-200">
				Information
			</h2>
			<dl class="mt-3 grid grid-cols-[auto_minmax(0,1fr)] gap-x-12 gap-y-3 text-sm wrap-break-word">
				<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_owner')}</dt>
				<dd>
					<UserLink user={expense.owner} />
					<span class="text-base-subtle dark:text-dark-base-subtle">({expense.owner.email})</span>
				</dd>

				<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_date')}</dt>
				<dd>{new Date(expense.expense_date).toLocaleDateString($locale ?? 'sv-SE')}</dd>

				<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_created_at')}</dt>
				<dd>{new Date(expense.created_date).toLocaleDateString($locale ?? 'sv-SE')}</dd>

				<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_confirmed')}</dt>
				<dd class="flex items-center gap-2">
					{#if expense.confirmed_at}
						<Check class="size-5 shrink-0 text-money-green-600" />
						<span class="text-xs text-base-subtle dark:text-dark-base-subtle">
							{#if expense.confirmed_by}{expense.confirmed_by.first_name}
								{expense.confirmed_by.last_name}
							{/if}
							{new Date(expense.confirmed_at).toLocaleDateString($locale ?? 'sv-SE')}
						</span>
					{:else}
						<span class="text-base-subtle dark:text-dark-base-subtle"
							>{$_('expense_status.unprocessed')}</span
						>
					{/if}
				</dd>

				<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_paid')}</dt>
				<dd class="flex items-center gap-2">
					{#if expense.payment}
						<Check class="size-5 shrink-0 text-money-green-600" />
						<span class="text-xs text-base-subtle dark:text-dark-base-subtle">
							{expense.payment.payer.first_name}
							{expense.payment.payer.last_name} · {new Date(
								expense.payment.date
							).toLocaleDateString($locale ?? 'sv-SE')}
						</span>
						<span class="font-mono text-xs text-base-subtle dark:text-dark-base-subtle"
							>{expense.payment.tag}</span
						>
					{:else}
						<span class="text-base-subtle dark:text-dark-base-subtle"
							>{$_('expense_status.unpaid')}</span
						>
					{/if}
				</dd>

				<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_verification')}</dt>
				<dd class="flex items-center gap-2">
					{#if expense.voucher}
						<Check class="size-5 shrink-0 text-money-green-600" />
						<span class="font-mono text-xs text-base-subtle dark:text-dark-base-subtle"
							>{expense.voucher}</span
						>
					{:else}
						<span class="text-base-subtle dark:text-dark-base-subtle"
							>{$_('expense_status.not_booked')}</span
						>
					{/if}
				</dd>
			</dl>
		</div>

		<div class="flex flex-col gap-3">
			<div class="flex items-center justify-between">
				<h2 class="text-base font-semibold">{$_('expense_comments')}</h2>
				{#if !showCommentForm}
					<button
						onclick={() => (showCommentForm = true)}
						class="flex cursor-pointer flex-row items-center gap-2 bg-money-green-600 p-2 text-sm font-medium text-white transition-all hover:bg-money-green-500"
					>
						{$_('add_comment')}
						<MessageSquarePlus class="size-4" />
					</button>
				{/if}
			</div>
			{#if showCommentForm}
				<div class="flex h-44 flex-col gap-2">
					<textarea
						bind:value={commentContent}
						class="w-full flex-1 resize-none border border-base-500 bg-transparent p-2 text-sm focus:outline-none dark:border-dark-base-200"
						placeholder={$_('add_comment_placeholder')}
					></textarea>
					<div class="flex justify-between">
						<button
							onclick={() => (showCommentForm = false)}
							class="text-xs font-medium text-base-subtle transition-colors hover:text-base-text dark:text-dark-base-subtle dark:hover:text-dark-base-text"
						>
							{$_('cancel')}
						</button>
						<button
							onclick={commentSubmit}
							class="bg-money-green-600 px-3 py-1 text-xs font-semibold text-white transition-colors hover:bg-money-green-500 disabled:cursor-not-allowed disabled:opacity-50"
							disabled={pending.comment}
						>
							{$_('submit')}
						</button>
					</div>
				</div>
			{/if}
			<CommentDisplay {comments} currentUser={user ?? undefined} />
		</div>
	</div>
</div>
