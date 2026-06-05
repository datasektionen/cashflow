<script lang="ts">
	import { _, locale } from 'svelte-i18n';
	import { PDFViewer } from '@embedpdf/svelte-pdf-viewer';
	import { ScrollArea } from 'bits-ui';
	import { ZoomMode, ScrollStrategy } from '@embedpdf/snippet';
	import { Copy, Check, MessageSquarePlus } from '@lucide/svelte';
	import type { PageData } from './$types';
	import type { Expense } from '$lib/api/types.ts';

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

	let showCommentForm = $state(false);

	function formatComment(text: string): string {
		return text
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(
				/```([^`]+)```/g,
				'<span class="uppercase text-xs tracking-wide opacity-60 font-medium">$1</span>'
			);
	}
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
	<div class="flex flex-col border lg:w-2/5">
		{#if expense.files.length > 0}
			<PDFViewer
				config={{
					documentManager: {
						initialDocuments: expense.files.map((f, i) => ({
							url: f.file,
							name: `${$_('file')} ${i + 1}`
						}))
					},
					tabBar: expense.files.length > 1 ? 'multiple' : 'never',
					theme: { preference: 'system' },
					disabledCategories: ['annotation', 'redaction', 'search'],
					zoom: { defaultZoomLevel: ZoomMode.FitWidth },
					scroll: { defaultStrategy: ScrollStrategy.Vertical },
					i18n: { defaultLocale: $locale ?? 'sv', fallbackLocale: 'en' }
				}}
				style="width: 100%; height: 100%"
			/>
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
			<table class="w-full text-sm">
				<thead
					class="text-xxs text-left font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
				>
					<tr class="text-xs">
						<td class="py-3 pr-4">{$_('cost_centre')}</td>
						<td class="px-4 py-3">{$_('secondary_cost_centre')}</td>
						<td class="px-4 py-3">{$_('budget_line')}</td>
						<td class="py-3 pl-4 text-right">{$_('amount')}</td>
						<td class="w-8 py-3 pl-4"></td>
					</tr>
				</thead>
				<tbody>
					{#each expense.parts as part}
						<tr class="border-t border-base-500 dark:border-dark-base-200">
							<td class="py-3 pr-4 text-left">{part.cost_centre}</td>
							<td class="px-4 py-3 text-left">{part.secondary_cost_centre}</td>
							<td class="px-4 py-3 text-left">{part.budget_line}</td>
							<td class="py-3 pl-4 text-right"
								>{part.amount.toLocaleString()}
								<span class="text-xs text-base-subtle dark:text-dark-base-subtle">SEK</span></td
							>
							<td class="w-8 py-3 pl-4">
								{#if part.attested_by}
									<Check class="size-4 text-money-green-600" />
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
				<tfoot>
					<tr class="border-t border-base-500 font-medium dark:border-dark-base-200">
						<td class="py-3 pr-4 text-right" colspan="3">{$_('total')}</td>
						<td class="py-3 pl-4 text-right"
							>{totalAmount}
							<span class="text-xs text-base-subtle dark:text-dark-base-subtle">SEK</span></td
						>
					</tr>
				</tfoot>
			</table>
		</div>

		<div>
			<h2 class="text-base font-semibold">{$_('expense_comments')}</h2>

			<div class="flex flex-col gap-4 lg:hidden">
				{#each expense.comments as comment}
					{@const isOwn = comment.author.email === data.user?.email}
					<div
						class={[
							'min-h-12 w-1/2 p-2',
							isOwn ? 'self-end bg-money-green-500' : 'self-start bg-base-300 dark:bg-dark-base-300'
						]}
					>
						<div class="flex items-baseline gap-2">
							<span
								class={[
									'text-xs font-medium uppercase',
									isOwn ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
								]}>{comment.author.first_name} {comment.author.last_name}</span
							>
							<span
								class={[
									'text-xs opacity-60',
									isOwn ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
								]}>{new Date(comment.date).toLocaleDateString($locale ?? 'sv-SE')}</span
							>
						</div>
						<div class={['text-sm', isOwn && 'text-white']}>
							{@html formatComment(comment.content)}
						</div>
					</div>
				{/each}
			</div>

			<ScrollArea.Root class="relative hidden w-full overflow-hidden lg:block">
				<ScrollArea.Viewport class="h-full max-h-50 w-full">
					<div class="flex flex-col gap-4 p-4">
						{#each expense.comments as comment}
							{@const isOwn = comment.author.email === data.user?.email}
							<div
								class={[
									'min-h-12 w-1/2 p-2',
									isOwn
										? 'self-end bg-money-green-500'
										: 'self-start bg-base-300 dark:bg-dark-base-300'
								]}
							>
								<div class="flex items-baseline gap-2">
									<span
										class={[
											'text-xs font-medium uppercase',
											isOwn ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
										]}>{comment.author.first_name} {comment.author.last_name}</span
									>
									<span
										class={[
											'text-xs opacity-60',
											isOwn ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
										]}>{new Date(comment.date).toLocaleDateString($locale ?? 'sv-SE')}</span
									>
								</div>
								<div class={['text-sm', isOwn && 'text-white']}>
									{@html formatComment(comment.content)}
								</div>
							</div>
						{/each}
					</div>
				</ScrollArea.Viewport>

				<ScrollArea.Scrollbar
					orientation="vertical"
					class="hover:bg-dark-10 data-[state=visible]:animate-in data-[state=hidden]:animate-out data-[state=hidden]:fade-out-0 data-[state=visible]:fade-in-0 flex w-2.5 touch-none rounded-none border-l border-l-transparent bg-base-subtle p-px transition-all duration-200 select-none hover:w-3 dark:bg-dark-base-subtle"
				>
					<ScrollArea.Thumb class="flex-1 rounded-none bg-base-400 dark:bg-dark-base-400" />
				</ScrollArea.Scrollbar>
				<ScrollArea.Scrollbar
					orientation="horizontal"
					class="flex h-2.5 touch-none rounded-none border-t border-t-transparent bg-base-300 p-px transition-all duration-200 select-none hover:h-3 dark:bg-dark-base-300"
				>
					<ScrollArea.Thumb class="rounded-none bg-base-400 dark:bg-dark-base-400" />
				</ScrollArea.Scrollbar>
				<ScrollArea.Corner />
			</ScrollArea.Root>
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
			{/if}
		</div>
	</div>
</div>
