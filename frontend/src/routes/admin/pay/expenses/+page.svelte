<script lang="ts">
	import type { PageProps } from './$types';
	import type { PaginatedResponse, PendingPayment } from '$lib/api/types.ts';
	import { api } from '$lib/api';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import { ChevronDown, ChevronUp, TriangleAlert } from '@lucide/svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import PaymentRow from './PaymentRow.svelte';

	type pageData = {
		pendingPayments: PaginatedResponse<PendingPayment>;
	};

	let { data }: PageProps = $props();
	let { pendingPayments }: pageData = $derived(data);

	let avatars: Promise<Record<string, string | null>> = $derived.by(() => {
		const usernames = pendingPayments.data.map((p) => p.owner.username);
		return api.profilePictures.getMany(usernames);
	});

	let expandedRows = new SvelteSet<number>();
</script>

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
								<span class="relative z-10 rounded-full bg-base-200 dark:bg-dark-base-100">
									{#await avatars}
										<UserAvatar placeholder={true} />
									{:then resolved}
										<UserAvatar url={resolved[pending.owner.username] ?? undefined} />
									{:catch _}
										<UserAvatar placeholder={true} />
									{/await}
								</span>
								<span class="flex items-center gap-2">
									<span class="font-semibold"
										>{pending.owner.first_name} {pending.owner.last_name}</span
									>
									{#if !pending.owner.has_bank_info}
										<span
											class="flex w-fit items-center gap-1 rounded-full bg-amber-500/15 px-1.5 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-500/20 dark:text-amber-400"
										>
											<TriangleAlert class="size-3" />
											Bankinfo saknas
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
										onPaid={() => expandedRows.delete(i)}
									/>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
		<!-- Loading overlay -->
		<!--        <div
                        class={[
                        'absolute top-0 left-0 z-20 flex size-full items-center justify-center bg-white/30 text-money-green-500 backdrop-blur-sm transition-opacity duration-200 dark:bg-black/30',
                        loading ? 'opacity-100' : 'pointer-events-none opacity-0'
                    ]}
                >
                    <CashSpinner/>
                </div>-->
	</div>
</div>
