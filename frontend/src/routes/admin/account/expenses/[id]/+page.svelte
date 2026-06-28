<script lang="ts">
	import { _, locale } from 'svelte-i18n';
	import type { PageData } from './$types';
	import CommentDisplay from '$lib/components/CommentDisplay.svelte';
	import PartsTable from '$lib/components/PartsTable.svelte';
	import VoucherRowFields, { newVoucherRow } from '../../VoucherRowFields.svelte';
	import type { VoucherRowDraft } from '../../VoucherRowFields.svelte';

	let { data }: { data: PageData } = $props();
	const expense = $derived(data.expense);

	let voucherRows = $state<VoucherRowDraft[]>([newVoucherRow()]);

	const isAttested = $derived(
		expense.parts.length > 0 && expense.parts.every((p) => p.attested_by != null)
	);
</script>

<div class="mb-6 flex flex-wrap items-center gap-3">
	<div class="flex items-center gap-2 text-sm text-base-subtle dark:text-dark-base-subtle">
		<span>{$_('expense')} #{expense.id}</span>
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
	</div>
</div>

<div class="flex flex-col gap-10">
	<div class="flex flex-col gap-8 lg:flex-row">
		<div class="flex flex-col gap-8 lg:w-3/5 lg:pt-1">
			<div>
				<h2 class="mb-2 text-base font-semibold">{$_('admin_account.create_voucher')}</h2>
				<VoucherRowFields bind:voucherRows />
				<div class="mt-4 flex justify-end">
					<button
						type="button"
						class="cursor-pointer bg-money-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-money-green-500"
					>
						{$_('submit')}
					</button>
				</div>
			</div>

			<div class="border-t border-base-400 pt-6 dark:border-dark-base-200">
				<h2 class="mb-2 text-base font-semibold">{$_('admin_account.existing_voucher')}</h2>
				<div class="flex gap-2">
					<input
						type="text"
						placeholder={$_('admin_account.voucher_number_placeholder')}
						class="border border-base-500 bg-base-200 p-2 text-sm placeholder:text-base-subtle dark:border-dark-base-200 dark:bg-dark-base-200 dark:placeholder:text-dark-base-subtle"
					/>
					<button
						type="button"
						class="cursor-pointer bg-money-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-money-green-500"
					>
						{$_('submit')}
					</button>
				</div>
			</div>
		</div>

		<div class="flex flex-col gap-8 lg:w-2/5 lg:pt-1">
			<div>
				<h2 class="text-base font-semibold">Information</h2>
				<dl class="mt-3 grid grid-cols-[auto_1fr] gap-x-8 gap-y-2 text-sm">
					<dt class="text-base-subtle dark:text-dark-base-subtle">
						{$_('new_expense.form.description.label')}
					</dt>
					<dd>{expense.description}</dd>

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
				</dl>
			</div>

			<div>
				<h2 class="text-base font-semibold">{$_('expense_parts')}</h2>
				<PartsTable parts={expense.parts} owner={expense.owner} dense />
			</div>
		</div>
	</div>

	<div class="border-t border-base-400 pt-6 dark:border-dark-base-200">
		<h2 class="mb-3 text-base font-semibold">{$_('expense_comments')}</h2>
		<CommentDisplay
			variant="compact"
			comments={expense.comments}
			currentUser={data.user ?? undefined}
		/>
	</div>
</div>
