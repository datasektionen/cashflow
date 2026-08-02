<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { page } from '$app/state';
	import { api } from '$lib/api';
	import type { LeaderboardEntry, PaginatedResponse } from '../../lib/api/types';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import { formatAmount } from '$lib/money';

	let range = $state(0);

	function rangeStart(r: number): string {
		const now = new Date();
		const year = now.getFullYear();
		const month = String(now.getMonth() + 1).padStart(2, '0');
		if (r === 1) return `${year}-01-01`;
		if (r === 2) return `${year}-${month}-01`;
		return '2000-01-01';
	}

	let leaderboard: Promise<PaginatedResponse<LeaderboardEntry>> = $derived(
		api.stats.leaderboard(1, 20, rangeStart(range))
	);
</script>

{#snippet leaderboardPosition(idx: number)}
	<div
		class={[
			'mx-auto flex size-7 items-center justify-center font-bold',
			idx === 0 && 'rounded-full bg-gradient-to-br from-yellow-200 to-yellow-400 text-yellow-950',
			idx === 1 && 'rounded-full bg-gradient-to-br from-zinc-100 to-zinc-300 text-zinc-950',
			idx === 2 && 'rounded-full bg-gradient-to-br from-orange-300 to-orange-500 text-orange-950',
			idx >= 3 && 'text-zinc-500'
		]}
	>
		{idx + 1}
	</div>
{/snippet}

<div class="max-w-3xl">
	<div class="mb-6 flex items-start justify-between gap-6">
		<p class="min-h-10 text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('leaderboard.help')}
		</p>

		<div
			class="relative flex w-36 shrink-0 flex-row overflow-hidden bg-base-300 dark:bg-dark-base-300"
		>
			<div
				class={[
					'absolute inset-y-0 w-12 bg-money-green-500 transition-all',
					range === 0 && 'left-0',
					range === 1 && 'left-12',
					range === 2 && 'left-24'
				]}
			></div>

			<button
				onclick={() => (range = 0)}
				class={[
					'z-2 w-12 cursor-pointer py-1.5 text-center text-xs font-medium uppercase transition-colors',
					range === 0 ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
				]}>Alltid</button
			>
			<button
				onclick={() => (range = 1)}
				class={[
					'z-2 w-12 cursor-pointer py-1.5 text-center text-xs font-medium uppercase transition-colors',
					range === 1 ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
				]}>År</button
			>
			<button
				onclick={() => (range = 2)}
				class={[
					'z-2 w-12 cursor-pointer py-1.5 text-center text-xs font-medium uppercase transition-colors',
					range === 2 ? 'text-white' : 'text-base-subtle dark:text-dark-base-subtle'
				]}>Månad</button
			>
		</div>
	</div>

	{#await leaderboard}
		<div class="flex justify-center py-16">
			<CashSpinner class="size-8 text-money-green-500" />
		</div>
	{:then res}
		{@const avatarUrls = api.profilePictures.getMany(res.data.map((entry) => entry.owner.username))}

		<div class="overflow-x-auto">
			<table class="w-full border-collapse">
				<thead>
					<tr>
						<th
							class="px-4 py-3 text-center text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
							>{$_('leaderboard.position')}</th
						>
						<th></th>
						<th></th>
						<th
							class="px-4 py-3 text-right text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
							>{$_('leaderboard.amount')}</th
						>
					</tr>
				</thead>
				<tbody>
					{#each res.data as entry, idx}
						{@const isCurrentUser = entry.owner.username === page.data.user?.username}
						<tr
							class={[
								'border-b border-b-base-400 last:border-0 hover:bg-base-200 dark:border-dark-base-150 dark:hover:bg-dark-base-200',
								isCurrentUser && 'bg-money-green-500/10'
							]}
						>
							<td class="w-16 px-4 py-3 text-center align-middle">
								{@render leaderboardPosition(idx)}
							</td>

							<td class="w-14 px-4 py-3 align-middle">
								{#await avatarUrls}
									<UserAvatar placeholder={true} class={idx < 3 ? 'size-10' : ''} />
								{:then avatars}
									<UserAvatar
										url={avatars[entry.owner.username] ?? undefined}
										class={idx < 3 ? 'size-10' : ''}
									/>
								{/await}
							</td>

							<td
								class={[
									'px-4 py-3 align-middle',
									idx < 3 && 'font-medium uppercase',
									idx === 0 && 'font-bold',
									idx >= 3 && 'text-sm'
								]}>{entry.owner.first_name} {entry.owner.last_name}</td
							>

							<td class="px-4 py-3 text-right align-middle whitespace-nowrap tabular-nums"
								>{formatAmount(entry.expense_total)}</td
							>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/await}
</div>
