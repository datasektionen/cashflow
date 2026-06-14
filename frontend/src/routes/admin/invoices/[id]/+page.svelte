<script lang="ts">
	import { _, locale } from 'svelte-i18n';
	import { Check, Copy, MessageSquarePlus } from '@lucide/svelte';
	import type { PageData } from './$types';
	import type { Invoice } from '$lib/api/types.ts';
	import ReceiptViewer from '$lib/components/ReceiptViewer.svelte';
	import CommentDisplay from '$lib/components/CommentDisplay.svelte';
	import PartsTable from '$lib/components/PartsTable.svelte';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import { api } from '$lib/api';
	import { logger } from '$lib/logger.ts';
	import { alerts, error, success } from '$lib/stores/alerts.ts';
	import { isErrorResponse } from '$lib/api/errors.ts';

	let { data }: { data: PageData } = $props();
	let invoice: Invoice = $state(data.invoice);

	const isAttested = $derived(
		invoice.parts.length > 0 && invoice.parts.every((p) => p.attested_by != null)
	);

	const fmt = new Intl.NumberFormat('sv-SE', {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});
	const totalAmount = $derived(
		fmt.format(
			invoice.parts.reduce(
				(sum: number, part: { amount: string }) => sum + parseFloat(part.amount),
				0
			)
		)
	);

	const canConfirm = $derived(!!data.user?.permissions.confirm && !invoice.confirmed_at);
	const canUnconfirm = $derived(!!data.user?.permissions.unconfirm && !!invoice.confirmed_at);

	let confirming = $state(false);

	async function handleConfirm() {
		confirming = true;
		await api.invoices
			.confirm(invoice.id)
			.then(() => {
				invoice = { ...invoice, confirmed_at: new Date().toISOString(), confirmed_by: data.user };
				alerts.update((a) => [...a, success($_('alerts.invoice_confirmed'))]);
			})
			.catch((e) => {
				logger.error(e);
				const msg = isErrorResponse(e) ? e.detail : $_('action_failed');
				alerts.update((a) => [...a, error(msg)]);
			})
			.finally(() => (confirming = false));
	}

	async function handleUnconfirm() {
		confirming = true;
		await api.invoices
			.unconfirm(invoice.id)
			.then(() => {
				invoice = { ...invoice, confirmed_at: null, confirmed_by: null };
				alerts.update((a) => [...a, success($_('alerts.invoice_unconfirmed'))]);
			})
			.catch((e) => {
				logger.error(e);
				const msg = isErrorResponse(e) ? e.detail : $_('action_failed');
				alerts.update((a) => [...a, error(msg)]);
			})
			.finally(() => (confirming = false));
	}

	let copied = $state(false);
	function copyId() {
		navigator.clipboard.writeText(String(invoice.id));
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	let comments = $state(invoice.comments);
	let showCommentForm = $state(false);
	let commentContent: string = $state('');
	const commentSubmit = async () => {
		await api.invoices
			.comment(invoice.id, commentContent)
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

<div class="mb-6 flex flex-wrap items-center justify-between gap-3">
	<div class="flex flex-wrap items-center gap-3">
		<div class="flex items-center gap-2 text-sm text-base-subtle dark:text-dark-base-subtle">
			<button
				onclick={copyId}
				class="flex cursor-pointer items-center gap-1 transition-colors hover:text-base-text dark:hover:text-dark-base-text"
			>
				<span>{$_('invoice')} #{invoice.id}</span>
				{#if copied}
					<Check class="size-3" />
				{:else}
					<Copy class="size-3" />
				{/if}
			</button>
			<span>·</span>
			<span>{invoice.owner.first_name} {invoice.owner.last_name}</span>
		</div>
		<div class="flex items-center gap-2">
			{#if isAttested}
				<span
					class="bg-money-green-200 px-2.5 py-0.5 text-xs font-semibold text-money-green-900 dark:bg-money-green-600 dark:text-white"
					>{$_('expense_attested')}</span
				>
			{/if}
			{#if invoice.confirmed_at}
				<span
					class="dark:text-money-green-950 bg-money-green-500 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-400"
					>{$_('expense_confirmed')}</span
				>
			{/if}
			{#if invoice.paid_at}
				<span
					class="dark:text-money-green-950 bg-money-green-700 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-300"
					>{$_('expense_paid')}</span
				>
			{/if}
			{#if invoice.verification}
				<span
					class="bg-money-green-900 px-2.5 py-0.5 text-xs font-semibold text-white dark:bg-money-green-200 dark:text-money-green-900"
					>{invoice.verification}</span
				>
			{/if}
			{#if !isAttested && !invoice.confirmed_at && !invoice.paid_at && !invoice.verification}
				<span
					class="bg-base-300 px-2.5 py-0.5 text-xs font-semibold text-base-subtle dark:bg-dark-base-300 dark:text-dark-base-subtle"
					>{$_('expense_status.unconfirmed')}</span
				>
			{/if}
		</div>
	</div>

	<div class="flex items-center gap-2">
		{#if canConfirm}
			<button
				onclick={handleConfirm}
				disabled={confirming}
				class="flex cursor-pointer items-center gap-1.5 bg-money-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-money-green-500 disabled:opacity-50 dark:bg-money-green-700 dark:hover:bg-money-green-600"
			>
				{#if confirming}
					<CashSpinner />
				{:else}
					{$_('expense_confirm')}
				{/if}
			</button>
		{:else if canUnconfirm}
			<button
				onclick={handleUnconfirm}
				disabled={confirming}
				class="flex cursor-pointer items-center gap-1.5 border border-base-500 px-3 py-1.5 text-xs font-medium text-base-subtle hover:border-red-400 hover:text-red-600 disabled:opacity-50 dark:border-dark-base-300 dark:text-dark-base-subtle dark:hover:border-red-500 dark:hover:text-red-400"
			>
				{#if confirming}
					<CashSpinner />
				{:else}
					{$_('expense_unconfirm')}
				{/if}
			</button>
		{/if}
	</div>
</div>

<div class="flex flex-col gap-4 lg:flex-row">
	<div class="flex max-h-256 flex-col border lg:w-2/5">
		{#if invoice.files.length > 0}
			<ReceiptViewer source={invoice.files.map((f) => f.file)} />
		{:else}
			<div
				class="flex flex-1 items-center justify-center p-8 text-sm text-base-subtle dark:text-dark-base-subtle"
			>
				{$_('expense_no_files')}
			</div>
		{/if}
	</div>

	<div class="flex flex-col gap-12 lg:w-3/5 lg:pt-1">
		<div>
			<h2 class="text-base font-semibold">{$_('expense_parts')}</h2>
			<PartsTable
				parts={invoice.parts}
				owner={invoice.owner}
				{totalAmount}
				includeAttest={true}
				partType="invoice"
				currentUser={data.user ?? undefined}
			/>
		</div>

		<div>
			<h2 class="text-base font-semibold">{$_('expense_comments')}</h2>
			<CommentDisplay {comments} currentUser={data.user} />
		</div>

		<div>
			<div
				class="flex items-center justify-between border-t border-base-500 pt-4 dark:border-dark-base-200"
			>
				<h2 class={['text-base font-semibold', showCommentForm && 'opacity-0']}>Information</h2>
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
			{:else}
				<dl class="grid grid-cols-[auto_1fr] gap-x-12 gap-y-3 text-sm">
					<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_owner')}</dt>
					<dd>
						{invoice.owner.first_name}
						{invoice.owner.last_name}
						<span class="text-base-subtle dark:text-dark-base-subtle">({invoice.owner.email})</span>
					</dd>

					<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_date')}</dt>
					<dd>
						{invoice.invoice_date
							? new Date(invoice.invoice_date).toLocaleDateString($locale ?? 'sv-SE')
							: '–'}
					</dd>

					<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_created_at')}</dt>
					<dd>{new Date(invoice.created_date).toLocaleDateString($locale ?? 'sv-SE')}</dd>

					<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_confirmed')}</dt>
					<dd class="flex items-center gap-2">
						{#if invoice.confirmed_at}
							<Check class="size-5 shrink-0 text-money-green-600" />
							<span class="text-xs text-base-subtle dark:text-dark-base-subtle">
								{#if invoice.confirmed_by}{invoice.confirmed_by.first_name}
									{invoice.confirmed_by.last_name} ·
								{/if}
								{new Date(invoice.confirmed_at).toLocaleDateString($locale ?? 'sv-SE')}
							</span>
						{:else}
							<span class="text-base-subtle dark:text-dark-base-subtle"
								>{$_('expense_status.unconfirmed')}</span
							>
						{/if}
					</dd>

					<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_paid')}</dt>
					<dd class="flex items-center gap-2">
						{#if invoice.paid_at}
							<Check class="size-5 shrink-0 text-money-green-600" />
							<span class="text-xs text-base-subtle dark:text-dark-base-subtle">
								{#if invoice.paid_by}{invoice.paid_by.first_name} {invoice.paid_by.last_name} ·
								{/if}{new Date(invoice.paid_at).toLocaleDateString($locale ?? 'sv-SE')}
							</span>
						{:else}
							<span class="text-base-subtle dark:text-dark-base-subtle"
								>{$_('expense_status.unpaid')}</span
							>
						{/if}
					</dd>

					<dt class="text-base-subtle dark:text-dark-base-subtle">{$_('expense_verification')}</dt>
					<dd class="flex items-center gap-2">
						{#if invoice.verification}
							<Check class="size-5 shrink-0 text-money-green-600" />
							<span class="font-mono text-xs text-base-subtle dark:text-dark-base-subtle"
								>{invoice.verification}</span
							>
						{:else}
							<span class="text-base-subtle dark:text-dark-base-subtle"
								>{$_('expense_status.not_booked')}</span
							>
						{/if}
					</dd>
				</dl>
			{/if}
		</div>
	</div>
</div>
