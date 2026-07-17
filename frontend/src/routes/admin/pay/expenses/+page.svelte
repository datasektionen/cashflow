<script lang="ts">
	import type { PageProps } from './$types';
	import type {
		Expense,
		PaginatedResponse,
		PaymentInitiationFile,
		PendingPayment,
		Profile
	} from '$lib/api/types.ts';
	import { api } from '$lib/api';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import UserLink from '$lib/components/UserLink.svelte';
	import { ChevronDown, ChevronUp, Download, TriangleAlert, X } from '@lucide/svelte';
	import { SvelteSet } from 'svelte/reactivity';
	import PaymentRow from './PaymentRow.svelte';
	import { _ } from 'svelte-i18n';
	import { invalidateAll } from '$app/navigation';
	import { alerts, error, success } from '$lib/stores/alerts.ts';
	import { isErrorResponse } from '$lib/api/errors.ts';
	import { logger } from '$lib/logger';

	type pageData = {
		pendingPayments: PaginatedResponse<PendingPayment>;
	};

	let { data }: PageProps = $props();
	let { pendingPayments }: pageData = $derived(data);

	let stagedPayments: SvelteSet<Expense> = new SvelteSet();

	let avatars: Promise<Record<string, string | null>> = $derived.by(() => {
		const usernames = pendingPayments.data.map((p) => p.owner.username);
		return api.profilePictures.getMany(usernames);
	});

	let expandedRows = new SvelteSet<string>();

	type StagedGroup = { owner: Profile; expenses: Expense[]; total: number };

	let stagedByUser: StagedGroup[] = $derived.by(() => {
		const groups = new Map<string, StagedGroup>();
		for (const expense of stagedPayments) {
			const group = groups.get(expense.owner.username) ?? {
				owner: expense.owner,
				expenses: [],
				total: 0
			};
			group.expenses.push(expense);
			group.total += expense.parts.reduce((sum, part) => sum + parseFloat(part.amount), 0);
			groups.set(expense.owner.username, group);
		}
		return [...groups.values()];
	});

	let stagedTotal: number = $derived(stagedByUser.reduce((sum, g) => sum + g.total, 0));

	let visiblePendingPayments: PendingPayment[] = $derived.by(() =>
		pendingPayments.data.filter((p) => {
			const staged = stagedByUser.find((g) => g.owner.username === p.owner.username);
			return !staged || staged.expenses.length < p.count;
		})
	);

	function unstageUser(group: StagedGroup) {
		for (const expense of group.expenses) {
			stagedPayments.delete(expense);
		}
	}

	let creatingPayment = $state(false);
	let lastPainFile: PaymentInitiationFile | null = $state(null);

	async function createPayment() {
		if (stagedByUser.length === 0) return;
		creatingPayment = true;
		try {
			const painFile = await api.payments.create([...stagedPayments]);
			lastPainFile = painFile;
			alerts.update((a) => [
				...a,
				success(`Betalningsfil ${painFile.msg_id} skapad för ${stagedByUser.length} mottagare`)
			]);
			stagedPayments.clear();
			await invalidateAll();
		} catch (e) {
			logger.error(e);
			const msg = isErrorResponse(e) ? e.detail : 'Något gick fel';
			alerts.update((a) => [...a, error(msg)]);
		} finally {
			creatingPayment = false;
		}
	}

	$effect(() => {
		for (const pending of pendingPayments.data) {
			const staged = stagedByUser.find((g) => g.owner.username === pending.owner.username);
			if (staged && staged.expenses.length >= pending.count) {
				expandedRows.delete(pending.owner.username);
			}
		}
	});
</script>

<!-- height = viewport - navbar (4rem) - main's py-4 (2rem) - page-title header (~4rem) -->
<div class="flex flex-col gap-6 lg:h-[calc(100dvh-10rem)] lg:flex-row lg:overflow-hidden">
	<div
		class="max-w-4xl min-w-0 flex-1 border border-base-500 p-2 lg:overflow-y-auto dark:border-dark-base-200"
	>
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
						{#each visiblePendingPayments as pending}
							{@const Chevron = expandedRows.has(pending.owner.username) ? ChevronUp : ChevronDown}
							<tr
								class={[
									'group flex cursor-pointer items-center hover:bg-base-200 dark:hover:bg-dark-base-200',
									!expandedRows.has(pending.owner.username) &&
										'border-b border-b-base-400 dark:border-dark-base-150'
								]}
								onclick={() => {
									if (expandedRows.has(pending.owner.username))
										expandedRows.delete(pending.owner.username);
									else expandedRows.add(pending.owner.username);
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

							{#if expandedRows.has(pending.owner.username)}
								<tr
									class="flex border-b border-b-base-400 bg-base-200/60 dark:border-dark-base-150 dark:bg-dark-base-100/60"
								>
									<td class="flex-1">
										<PaymentRow
											owner={pending.owner}
											bankInfo={pending.bank_info}
											onPaid={() => expandedRows.delete(pending.owner.username)}
											bind:stagedPayments
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

	<div class="flex w-full flex-col gap-4 lg:h-full lg:w-96 lg:shrink-0 lg:overflow-y-auto">
		<div class="flex items-center justify-between gap-2">
			<h2 class="text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle">
				Markerade betalningar
			</h2>
			{#if stagedByUser.length > 0}
				<span class="text-sm font-semibold tabular-nums">
					{stagedTotal.toLocaleString('sv-SE', {
						minimumFractionDigits: 2,
						maximumFractionDigits: 2
					})} kr
				</span>
			{/if}
			<button
				onclick={createPayment}
				class={[
					'bg-money-green-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-money-green-700',
					'cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-money-green-600'
				]}
				disabled={stagedByUser.length === 0 || creatingPayment}
			>
				{creatingPayment ? 'Skapar…' : 'Skapa betalning'}
			</button>
		</div>
		{#if lastPainFile}
			<div
				class="flex items-center justify-between gap-2 border border-money-green-600 bg-money-green-600/10 p-3 text-sm dark:border-money-green-400 dark:bg-money-green-400/10"
			>
				<span>Betalningsfil <span class="font-semibold">{lastPainFile.msg_id}</span> skapad</span>
				<a
					href={lastPainFile.file}
					download
					class="flex shrink-0 items-center gap-1 font-medium text-money-green-700 hover:underline dark:text-money-green-400"
				>
					<Download class="size-4" />
					Ladda ner
				</a>
			</div>
		{/if}
		{#if stagedByUser.length === 0}
			<p class="text-sm text-base-subtle dark:text-dark-base-subtle">Inga markerade betalningar</p>
		{:else}
			{#each stagedByUser as group}
				<div class="border border-base-500 p-4 dark:border-dark-base-200">
					<div class="flex items-center justify-between gap-2">
						<span class="font-semibold"><UserLink user={group.owner} /></span>
						<button
							onclick={() => unstageUser(group)}
							aria-label="Ta bort"
							class="cursor-pointer text-base-subtle transition-all hover:scale-115 dark:text-dark-base-subtle"
						>
							<X class="size-4" />
						</button>
					</div>
					<ul class="mt-3 flex flex-col gap-2">
						{#each group.expenses as expense}
							{@const total = expense.parts.reduce((sum, part) => sum + parseFloat(part.amount), 0)}
							<li
								class="flex items-center justify-between gap-2 text-sm text-base-subtle dark:text-dark-base-subtle"
							>
								<span class="min-w-0 truncate">#{expense.id} {expense.description}</span>
								<span class="shrink-0 tabular-nums">
									{total.toLocaleString('sv-SE', {
										minimumFractionDigits: 2,
										maximumFractionDigits: 2
									})} kr
								</span>
							</li>
						{/each}
					</ul>
					<div
						class="mt-3 flex items-center justify-between border-t border-base-400 pt-3 text-sm font-semibold dark:border-dark-base-150"
					>
						<span>Totalt</span>
						<span class="tabular-nums">
							{group.total.toLocaleString('sv-SE', {
								minimumFractionDigits: 2,
								maximumFractionDigits: 2
							})} kr
						</span>
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>
