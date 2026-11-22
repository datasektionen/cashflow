<script lang="ts">
	import type { PageProps } from './$types';
	import UserAvatar from '#lib/components/UserAvatar.svelte';
	import UserLink from '#lib/components/UserLink.svelte';
	import { ChevronDown, CircleCheck, TriangleAlert } from '@lucide/svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import PaymentRow from './PaymentRow.svelte';
	import { _ } from 'svelte-i18n';
	import { mayPay } from '#lib/auth.ts';
	import { Badge, Card, CopyableValue, EmptyState } from '#lib/components/ui/index.ts';
	import { formatBankAccount } from '#lib/bankAccount.ts';
	import { completedPayments } from './completedPayments.svelte';
	import { formatDineroAmount } from '#lib/money.ts';

	let { data }: PageProps = $props();
	const pendingPayments = $derived(data.pendingPayments);
	const canPay = $derived(mayPay(data.user));

	let expanded = new SvelteSet<string>();

	function toggle(username: string) {
		if (expanded.has(username)) expanded.delete(username);
		else expanded.add(username);
	}
</script>

<div class="flex flex-col gap-6 xl:flex-row xl:items-start">
	{#if pendingPayments.length === 0}
		<EmptyState icon={CircleCheck} title={$_('tasks.empty')} class="w-full max-w-4xl" />
	{:else}
		<Card padded={false} class="w-full max-w-4xl min-w-0">
			<ul class="divide-y divide-border">
				{#each pendingPayments as pending (pending.owner.username)}
					{@const open = expanded.has(pending.owner.username)}
					<li>
						<button
							type="button"
							aria-expanded={open}
							onclick={() => toggle(pending.owner.username)}
							class={[
								'group flex w-full cursor-pointer items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/60',
								open && 'bg-muted/60'
							]}
						>
							<UserAvatar username={pending.owner.username} class="size-10" />
							<span class="flex min-w-0 flex-1 flex-col">
								<span class="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
									<span class="truncate font-semibold">
										{pending.owner.first_name}
										{pending.owner.last_name}
									</span>
									{#if !pending.owner.has_bank_info}
										<Badge variant="warning"
											><TriangleAlert />{$_('profile.bank_info_missing')}</Badge
										>
									{/if}
								</span>
								<span class="text-sm text-muted-foreground">
									{$_('admin_pay.count', { values: { count: pending.count } })}
								</span>
							</span>
							<span class="shrink-0 font-semibold tabular-nums">
								{formatDineroAmount(pending.total)} kr
							</span>
							<ChevronDown
								class={[
									'size-4 shrink-0 text-muted-foreground transition-transform group-hover:text-foreground',
									open && 'rotate-180'
								]}
							/>
						</button>
						{#if open}
							<PaymentRow
								owner={pending.owner}
								bankInfo={pending.bank_info}
								count={pending.count}
								{canPay}
								onPaid={() => expanded.delete(pending.owner.username)}
							/>
						{/if}
					</li>
				{/each}
			</ul>
		</Card>
	{/if}

	{#if completedPayments.length > 0}
		<Card title={$_('completed_payments')} padded={false} class="w-full xl:max-w-md">
			<ul class="divide-y divide-border">
				{#each completedPayments as completed (completed.id)}
					<li class="flex flex-col gap-2 px-5 py-4">
						<div class="flex items-center justify-between gap-2">
							<span class="min-w-0 truncate text-sm font-medium">
								<UserLink user={completed.receiver} />
							</span>
							<span class="shrink-0 text-sm font-medium tabular-nums">
								{formatDineroAmount(completed.amount)} kr
							</span>
						</div>
						<div class="flex flex-wrap items-center gap-2">
							<CopyableValue display={completed.tag} class="font-mono" />
							<CopyableValue
								display="{formatDineroAmount(completed.amount)} kr"
								value={formatDineroAmount(completed.amount)}
							/>
							{#if completed.bankInfo.bank_account}
								<CopyableValue
									display={formatBankAccount(
										completed.bankInfo.sorting_number,
										completed.bankInfo.bank_account
									)}
									class="font-mono"
								/>
							{/if}
						</div>
						{#if completed.bankInfo.bank_name}
							<span class="text-xs text-muted-foreground">{completed.bankInfo.bank_name}</span>
						{/if}
					</li>
				{/each}
			</ul>
		</Card>
	{/if}
</div>
