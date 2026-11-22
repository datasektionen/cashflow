<script lang="ts">
	import CostCentreCell from '#lib/components/CostCentreCell.svelte';
	import UserLink from '#lib/components/UserLink.svelte';
	import type { BankInfo, Expense, Profile } from '#lib/api/types.ts';
	import { api } from '#lib/api/index.ts';
	import { SvelteSet } from 'svelte/reactivity';
	import { ExternalLink } from '@lucide/svelte';
	import {
		Button,
		Checkbox,
		CopyableValue,
		Dialog,
		Skeleton,
		Spinner
	} from '#lib/components/ui/index.ts';
	import { refreshAll } from '$app/navigation';
	import { failed, success } from '#lib/stores/alerts.ts';
	import { formatDineroAmount, sumDinero, claimTotal } from '#lib/money.ts';
	import { formatBankAccount } from '#lib/bankAccount.ts';
	import { _ } from 'svelte-i18n';
	import { completedPayments } from './completedPayments.svelte';

	let {
		owner,
		bankInfo,
		count,
		canPay = false,
		onPaid
	}: {
		owner: Profile;
		bankInfo: BankInfo;
		count: number;
		canPay?: boolean;
		onPaid?: () => void;
	} = $props();

	const formattedAccount = $derived(
		formatBankAccount(bankInfo.sorting_number, bankInfo.bank_account)
	);

	const expenses = $derived(api.expenses.list(1, 100, { user: owner.username, payable: true }));

	let selected = new SvelteSet<number>();
	const totalOf = (list: Expense[]) =>
		sumDinero(list.filter((e) => selected.has(e.id)).map(claimTotal));

	let paying = $state(false);
	let payDialogOpen = $state(false);

	async function handlePay() {
		if (selected.size === 0) return;
		paying = true;
		try {
			const amount = totalOf((await expenses).data);
			const payment = await api.payments.create([...selected]);
			completedPayments.unshift({ ...payment, amount, bankInfo });
			success($_('admin_pay.payment_created', { values: { tag: payment.tag } }));
			selected.clear();
			payDialogOpen = false;
			onPaid?.();
			await refreshAll();
		} catch (e) {
			failed(e, $_('admin_pay.error'));
		} finally {
			paying = false;
		}
	}
</script>

<div class="border-t border-border bg-muted/30">
	<div class="flex flex-wrap items-center gap-3 px-4 py-3 text-sm text-muted-foreground">
		<UserLink user={owner} class="font-medium text-foreground" />
		{#if owner.has_bank_info}
			<CopyableValue display={formattedAccount} class="font-mono" />
			{#if bankInfo.bank_name}<span>{bankInfo.bank_name}</span>{/if}
		{/if}
	</div>
	{#await expenses}
		<ul class="divide-y divide-border border-y border-border bg-card">
			{#each { length: count }, i (i)}
				<li class="flex items-center gap-4 px-4 py-3">
					<Skeleton class="size-4" />
					<div class="flex flex-1 flex-col gap-1.5">
						<Skeleton class="h-5 w-48" />
						<Skeleton class="h-6 w-24" />
					</div>
					<Skeleton class="h-5 w-20" />
				</li>
			{/each}
		</ul>
		<div class="flex items-center gap-x-4 px-4 py-3">
			<Skeleton class="size-4" />
			<Skeleton class="h-4 w-24" />
			<Skeleton class="ml-auto h-5 w-16" />
			<Skeleton class="h-9 w-20" />
		</div>
	{:then resolved}
		{@const allSelected =
			resolved.data.length > 0 && resolved.data.every((e) => selected.has(e.id))}
		<ul class="divide-y divide-border border-y border-border bg-card">
			{#each resolved.data as expense (expense.id)}
				{@const checked = selected.has(expense.id)}
				<li
					class={['flex items-center gap-4 px-4 py-3 transition-colors', checked && 'bg-accent/60']}
				>
					<Checkbox
						aria-label="#{expense.id}"
						{checked}
						onCheckedChange={(v) => {
							if (v) selected.add(expense.id);
							else selected.delete(expense.id);
						}}
					/>
					<div class="flex min-w-0 flex-1 flex-col gap-1.5">
						<a
							href="/admin/expenses/{expense.id}"
							target="_blank"
							rel="noopener noreferrer"
							class="group flex min-w-0 items-center gap-2 text-sm hover:text-primary-text"
						>
							<span class="shrink-0 font-mono text-xs text-muted-foreground">#{expense.id}</span>
							<span class="min-w-0 truncate font-medium">{expense.description}</span>
							<ExternalLink
								class="size-3.5 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100"
							/>
						</a>
						<CostCentreCell parts={expense.parts} />
					</div>
					<span class="shrink-0 text-sm font-medium tabular-nums">
						{formatDineroAmount(claimTotal(expense))} kr
					</span>
				</li>
			{/each}
		</ul>

		<div class="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
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
			<span class="ml-auto text-sm font-semibold tabular-nums">
				{formatDineroAmount(totalOf(resolved.data))} kr
			</span>
			<Dialog
				bind:open={payDialogOpen}
				title={$_('pay_confirm.title')}
				description={$_('pay_confirm.description')}
			>
				{#snippet trigger({ props })}
					<Button {...props} disabled={selected.size === 0 || paying || !canPay}>
						{$_('pay_confirm.action')}
					</Button>
				{/snippet}
				{#snippet footer()}
					<Button variant="secondary" onclick={() => (payDialogOpen = false)}>
						{$_('cancel')}
					</Button>
					<Button onclick={handlePay} disabled={selected.size === 0 || paying || !canPay}>
						{#if paying}<Spinner />{/if}
						{paying ? $_('pay_confirm.action_loading') : $_('pay_confirm.action')}
					</Button>
				{/snippet}
			</Dialog>
		</div>
	{:catch}
		<p class="px-4 py-4 text-sm text-danger">{$_('admin_pay.load_error')}</p>
	{/await}
</div>
