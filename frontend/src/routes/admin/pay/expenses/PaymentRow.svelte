<script lang="ts">
	import type { BankInfo, Profile } from '$lib/api/types';
	import { api } from '$lib/api';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import { Check, Copy, ExternalLink } from '@lucide/svelte';
	import Checkbox from '$lib/components/Checkbox.svelte';
	import { invalidateAll } from '$app/navigation';
	import { alerts, error, success } from '$lib/stores/alerts';
	import { isErrorResponse } from '$lib/api/errors';
	import { logger } from '$lib/logger';
	import { formatBankAccount } from '$lib/bankAccount';
	import Dialog from '$lib/components/Dialog.svelte';
	import { Dialog as DialogPrimitive } from 'bits-ui';
	import { _ } from 'svelte-i18n';
	import { completedPayments } from './completedPayments.svelte';

	let {
		owner,
		bankInfo,
		canPay = false,
		onPaid
	}: { owner: Profile; bankInfo: BankInfo; canPay?: boolean; onPaid?: () => void } = $props();

	let copied = $state(false);

	let formattedAccount = $derived(
		formatBankAccount(bankInfo.sorting_number, bankInfo.bank_account)
	);

	function copy(value: string) {
		navigator.clipboard.writeText(value);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	let refreshKey = $state(0);

	let expenses = $derived.by(() => {
		refreshKey;
		return api.expenses.list(1, 100, { user: owner.username, payable: true });
	});

	let selected = new SvelteSet<number>();

	let paying = $state(false);
	let payDialogOpen = $state(false);

	async function handlePay() {
		if (selected.size === 0) return;
		paying = true;
		try {
			const resolved = await expenses;
			const amount = resolved.data
				.filter((e) => selected.has(e.id))
				.reduce((sum, e) => sum + e.parts.reduce((s, p) => s + parseFloat(p.amount), 0), 0);
			const payment = await api.payments.create([...selected]);
			completedPayments.push({ ...payment, amount: amount.toFixed(2), bankInfo });
			alerts.update((a) => [
				...a,
				success($_('admin_pay.payment_created', { values: { tag: payment.tag } }))
			]);
			selected.clear();
			payDialogOpen = false;
			onPaid?.();
			refreshKey++;
			await invalidateAll();
		} catch (e) {
			logger.error(e);
			const msg = isErrorResponse(e) ? e.detail : $_('admin_pay.error');
			alerts.update((a) => [...a, error(msg)]);
		} finally {
			paying = false;
		}
	}
</script>

{#snippet payTitle()}
	<h1 class="text-xl font-medium text-base-text dark:text-dark-base-text">
		{$_('pay_confirm.title')}
	</h1>
{/snippet}
{#snippet payDescription()}
	<p class="text-base-subtle dark:text-dark-base-subtle">
		{$_('pay_confirm.description')}
	</p>
{/snippet}
{#snippet payTrigger()}
	<button
		disabled={selected.size === 0 || paying || !canPay}
		class="cursor-pointer bg-money-green-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-money-green-700 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-money-green-600"
	>
		{paying ? $_('pay_confirm.action_loading') : $_('pay_confirm.action')}
	</button>
{/snippet}
{#snippet payButtons()}
	<div class="mt-6 flex justify-end gap-2">
		<DialogPrimitive.Close
			class="cursor-pointer border border-base-500 px-3 py-1.5 text-xs font-medium text-base-subtle dark:border-dark-base-500 dark:text-dark-base-subtle"
		>
			{$_('cancel')}
		</DialogPrimitive.Close>
		<button
			onclick={handlePay}
			disabled={selected.size === 0 || paying || !canPay}
			class="flex cursor-pointer items-center gap-1.5 bg-money-green-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-money-green-700 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-money-green-600"
		>
			{paying ? $_('pay_confirm.action_loading') : $_('pay_confirm.action')}
		</button>
	</div>
{/snippet}

<div class="flex flex-col pb-2 pl-8">
	{#if owner.has_bank_info}
		<div
			class="flex flex-wrap items-center gap-x-4 gap-y-1 pt-2 pr-4 text-sm text-base-subtle dark:text-dark-base-subtle"
		>
			{#if bankInfo.bank_name}
				<span>{bankInfo.bank_name}</span>
			{/if}
			<button
				onclick={() => copy(formattedAccount)}
				class="flex cursor-pointer items-center gap-1 tabular-nums transition-colors hover:text-base-text dark:hover:text-dark-base-text"
			>
				<span>{formattedAccount}</span>
				{#if copied}
					<Check class="size-3" />
				{:else}
					<Copy class="size-3" />
				{/if}
			</button>
		</div>
	{/if}
	{#await expenses}
		<div class="p-4">
			<CashSpinner />
		</div>
	{:then resolved}
		{#each resolved.data as expense}
			{@const total = expense.parts.reduce((sum, part) => sum + parseFloat(part.amount), 0)}
			{@const costCentres = [...new Set(expense.parts.map((p) => p.cost_centre))]}
			<div class="flex flex-row items-stretch">
				<div
					class={[
						'w-0.5 shrink-0 transition-colors',
						selected.has(expense.id) ? 'bg-money-green-600' : 'bg-transparent'
					]}
				></div>
				<div class="flex min-w-0 flex-1 flex-col gap-y-1 py-2 pl-3">
					<a
						href="/admin/expenses/{expense.id}"
						target="_blank"
						rel="noopener noreferrer"
						class="group dark:hover:text-dark-base flex min-w-0 items-center gap-x-1.5 text-sm text-base-subtle dark:text-dark-base-subtle"
					>
						<span class="my-auto min-w-0 text-xs">#{expense.id}</span>
						<span class="min-w-0 truncate">{expense.description}</span>
						<ExternalLink
							class="size-3.5 shrink-0 opacity-50 transition-opacity group-hover:opacity-100"
						/>
					</a>
					{#if costCentres.length > 0}
						<div class="flex flex-wrap gap-1">
							{#each costCentres as cc}
								<span class="bg-base-400 px-1.5 py-0.5 text-xs dark:bg-dark-base-200">{cc}</span>
							{/each}
						</div>
					{/if}
				</div>
				<div
					class="flex w-36 shrink-0 items-start justify-end px-4 py-2 text-sm font-medium tabular-nums"
				>
					{total.toLocaleString('sv-SE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} kr
				</div>
				<div class="flex w-20 shrink-0 items-start justify-center py-2 pr-4">
					<Checkbox
						class="mt-0.5"
						checked={selected.has(expense.id)}
						onCheckedChange={(v) => {
							if (v) selected.add(expense.id);
							else selected.delete(expense.id);
						}}
					/>
				</div>
			</div>
		{/each}

		{@const selectedTotal = resolved.data
			.filter((e) => selected.has(e.id))
			.reduce((sum, e) => sum + e.parts.reduce((s, p) => s + parseFloat(p.amount), 0), 0)}
		{@const allSelected =
			resolved.data.length > 0 && resolved.data.every((e) => selected.has(e.id))}
		<div
			class="mt-2 flex items-center justify-end gap-x-4 border-t border-base-400 pt-3 pr-4 dark:border-dark-base-150"
		>
			<Checkbox
				checked={allSelected}
				indeterminate={selected.size > 0 && !allSelected}
				onCheckedChange={(v) => {
					if (v) for (const e of resolved.data) selected.add(e.id);
					else selected.clear();
				}}
			>
				{$_('admin_pay.select_all')}
			</Checkbox>
			<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
				{selectedTotal.toLocaleString('sv-SE', {
					minimumFractionDigits: 2,
					maximumFractionDigits: 2
				})} kr
			</span>
			<Dialog
				bind:open={payDialogOpen}
				title={payTitle}
				description={payDescription}
				triggerContent={payTrigger}
			>
				{@render payButtons()}
			</Dialog>
		</div>
	{:catch err}
		<div class="p-4">
			<span class="text-sm text-red-500">{$_('admin_pay.load_error')}</span>
		</div>
	{/await}
</div>
