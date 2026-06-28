<script lang="ts">
	import { _, locale } from 'svelte-i18n';
	import { Check, Copy, MessageSquarePlus } from '@lucide/svelte';
	import type { PageData } from './$types';
	import type { Expense } from '$lib/api/types.ts';
	import ReceiptViewer from '$lib/components/ReceiptViewer.svelte';
	import CommentDisplay from '$lib/components/CommentDisplay.svelte';
	import PartsTable from '$lib/components/PartsTable.svelte';
	import { api } from '$lib/api';
	import { logger } from '$lib/logger.ts';
	import { alerts, error, success } from '$lib/stores/alerts.ts';
	import { isErrorResponse } from '$lib/api/errors.ts';

	let { data }: { data: PageData } = $props();
	let { expense }: { expense: Expense } = data;

	const isAttested = $derived(
		expense.parts.length > 0 && expense.parts.every((p) => p.attested_by != null)
	);

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});
	const totalAmount = $derived(
		fmt.format(
			expense.parts.reduce(
				(sum: number, part: { amount: string }) => sum + parseFloat(part.amount),
				0
			)
		)
	);

	let copied = $state(false);

	function copyId() {
		navigator.clipboard.writeText(String(expense.id));
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	let comments = $state(expense.comments);
	let showCommentForm = $state(false);
	let commentContent: string = $state('');
	const commentSubmit = async () => {
		await api.expenses
			.comment(expense.id, commentContent)
			.then((comment) => {
				comments.push(comment);
				showCommentForm = false;
				alerts.update((a) => [...a, success($_('comment_submitted'))]);
			})
			.catch((e) => {
				logger.error(e);
				const msg = isErrorResponse(e) ? e.detail : $_('comment_submission_failed');
				alerts.update((a) => [...a, error(msg)]);
			});
	};
</script>

<div class="mb-6 flex flex-wrap items-center gap-3">
	<div class="flex items-center gap-2 text-sm text-base-subtle dark:text-dark-base-subtle">
		<button
			onclick={copyId}
			class="flex cursor-pointer items-center gap-1 transition-colors hover:text-base-text dark:hover:text-dark-base-text"
		>
			<span>{$_('expense')} #{expense.id}</span>
			{#if copied}
				<Check class="size-3" />
			{:else}
				<Copy class="size-3" />
			{/if}
		</button>
		<span>·</span>
		<span>{expense.owner.first_name} {expense.owner.last_name}</span>
	</div>
	<div class="flex items-center gap-2">
		{#if isAttested}
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
		{#if expense.payment}
			<span
				class="dark:text-money-green-950 bg-money-green-700 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-300"
				>{$_('expense_paid')}</span
			>
		{/if}
		{#if expense.verification}
			<span
				class="bg-money-green-900 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-200 dark:text-money-green-900"
				>{expense.verification}</span
			>
		{/if}
		{#if !isAttested && !expense.confirmed_at && !expense.payment && !expense.verification}
			<span
				class="bg-base-300 px-2.5 py-0.5 text-xs font-semibold text-base-subtle dark:bg-dark-base-300 dark:text-dark-base-subtle"
				>{$_('expense_status.unconfirmed')}</span
			>
		{/if}
	</div>
</div>

<div class="flex flex-col gap-4 lg:flex-row">
	<div class="flex max-h-256 flex-col border lg:w-2/5">
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

	<div class="flex flex-col gap-12 lg:w-3/5 lg:pt-1 xl:pr-16">
		<div>
			<h2 class="text-base font-semibold">{$_('expense_parts')}</h2>
			<PartsTable parts={expense.parts} owner={expense.owner} {totalAmount} />
		</div>

		<div>
			<h2 class="border-t border-base-500 pt-4 text-base font-semibold dark:border-dark-base-200">
				Information
			</h2>
			<dl class="mt-3 grid grid-cols-[auto_1fr] gap-x-12 gap-y-3 text-sm">
				<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_owner')}</dt>
				<dd>
					{expense.owner.first_name}
					{expense.owner.last_name}
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
							>{$_('expense_status.unconfirmed')}</span
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
					{:else}
						<span class="text-base-subtle dark:text-dark-base-subtle"
							>{$_('expense_status.unpaid')}</span
						>
					{/if}
				</dd>

				<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_verification')}</dt>
				<dd class="flex items-center gap-2">
					{#if expense.verification}
						<Check class="size-5 shrink-0 text-money-green-600" />
						<span class="font-mono text-xs text-base-subtle dark:text-dark-base-subtle"
							>{expense.verification}</span
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
							class="bg-money-green-600 px-3 py-1 text-xs font-semibold text-white transition-colors hover:bg-money-green-500"
						>
							{$_('submit')}
						</button>
					</div>
				</div>
			{/if}
			<CommentDisplay {comments} currentUser={data.user} />
		</div>
	</div>
</div>
