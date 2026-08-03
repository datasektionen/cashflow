<script lang="ts">
	import type { PageProps } from './$types';
	import type { PaginatedResponse, PendingPayment } from '$lib/api/types';
	import { api } from '$lib/api';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import UserLink from '$lib/components/UserLink.svelte';
	import { ChevronDown, ChevronUp, TriangleAlert } from '@lucide/svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import PaymentRow from './PaymentRow.svelte';
	import { _ } from 'svelte-i18n';
	import { mayPay } from '$lib/auth';
	import CopyableValue from '$lib/components/ui/CopyableValue.svelte';
	import { completedPayments } from './completedPayments.svelte';

	type pageData = {
		pendingPayments: PaginatedResponse<PendingPayment>;
	};

	let { data }: PageProps = $props();
	let { pendingPayments }: pageData = $derived(data);
	const canPay = $derived(mayPay(data.user));

	let avatars: Promise<Record<string, string | null>> = $derived.by(() => {
		const usernames = pendingPayments.data.map((p) => p.owner.username);
		return api.profilePictures.getMany(usernames);
	});

	let expandedRows = new SvelteSet<number>();
</script>

<div class="flex flex-col space-x-4 md:flex-row">
	<div class="max-w-4xl border border-base-500 p-2 dark:border-dark-base-200">
		<div class="relative">
			<div class="overflow-hidden">
				<table class="w-full table-fixed text-sm">
					<thead>
						<tr class="flex">
							<th
								class="flex-1 px-4 py-3 text-left text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
							>
								Användare
							</th>
							<th
								class="w-36 px-4 py-3 text-right text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
							>
								Total
							</th>
							<th class="w-20 py-2 pr-4"></th>
						</tr>
					</thead>
					<tbody>
						{#each pendingPayments.data as pending, i}
							{@const Chevron = expandedRows.has(i) ? ChevronUp : ChevronDown}
							<tr
								class={[
									'group flex cursor-pointer items-center hover:bg-base-200 dark:hover:bg-dark-base-200',
									!expandedRows.has(i) && 'border-b border-b-base-400 dark:border-dark-base-150'
								]}
								onclick={() => {
									if (expandedRows.has(i)) expandedRows.delete(i);
									else expandedRows.add(i);
								}}
							>
								<td class="relative flex flex-1 flex-row items-center gap-x-2 px-4 py-2">
									<span
										class="relative z-10 hidden rounded-full bg-base-200 sm:block dark:bg-dark-base-100"
									>
										{#await avatars}
											<UserAvatar placeholder={true} />
										{:then resolved}
											<UserAvatar url={resolved[pending.owner.username] ?? undefined} />
										{:catch _}
											<UserAvatar placeholder={true} />
										{/await}
									</span>
									<span class="flex items-center gap-2">
										<span class="font-semibold">
											<UserLink user={pending.owner} />
										</span>
										{#if !pending.owner.has_bank_info}
											<span
												class="flex w-fit items-center gap-1 rounded-full bg-amber-500/15 px-1.5 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-500/20 dark:text-amber-400"
											>
												<TriangleAlert class="size-3" />
												{$_('profile.bank_info_missing')}
											</span>
										{/if}
									</span>
								</td>
								<td class="w-36 px-4 py-2 text-right font-semibold tabular-nums">
									{Number(pending.total).toLocaleString('sv-SE', {
										minimumFractionDigits: 2,
										maximumFractionDigits: 2
									})} kr
								</td>
								<td class="flex h-full w-20 flex-row items-center gap-x-2 py-2 pr-4 text-right">
									<span
										class="ml-auto min-w-7 rounded-full bg-money-green-600/15 px-1.5 py-0.5 text-center text-xs font-medium text-money-green-700 dark:bg-money-green-600/20 dark:text-money-green-400"
									>
										{pending.count}
									</span>
									<Chevron class="size-5 transition-transform group-hover:scale-125" />
								</td>
							</tr>

							{#if expandedRows.has(i)}
								<tr
									class="flex border-b border-b-base-400 bg-base-200/60 dark:border-dark-base-150 dark:bg-dark-base-100/60"
								>
									<td class="flex-1">
										<PaymentRow
											owner={pending.owner}
											bankInfo={pending.bank_info}
											{canPay}
											onPaid={() => expandedRows.delete(i)}
										/>
									</td>
								</tr>
							{/if}
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</div>

	{#if completedPayments.length > 0}
		<div class="h-fit w-full max-w-md border border-base-500 p-2 dark:border-dark-base-200">
			<h2
				class="px-2 py-3 text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
			>
				{$_('completed_payments')}
			</h2>
			<ul class="flex flex-col">
				{#each completedPayments as completed}
					<li
						class="flex flex-col gap-y-2 border-t border-base-400 px-2 py-3 dark:border-dark-base-150"
					>
						<div class="flex items-center justify-between gap-x-2">
							<span class="min-w-0 truncate font-semibold">
								<UserLink user={completed.receiver} />
							</span>
							<span class="shrink-0 text-sm font-semibold tabular-nums">
								{Number(completed.amount).toLocaleString('sv-SE', {
									minimumFractionDigits: 2,
									maximumFractionDigits: 2
								})} kr
							</span>
						</div>
						<div class="flex flex-wrap items-center gap-2">
							<CopyableValue display={completed.tag} />
							<CopyableValue
								display={`${Number(completed.amount).toLocaleString('sv-SE', {
									minimumFractionDigits: 2,
									maximumFractionDigits: 2
								})} kr`}
								value={completed.amount}
							/>
						</div>
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</div>
