<script lang="ts">
	import { _ } from 'svelte-i18n';
	import ExpenseTotalLeaderboard from './ExpenseTotalLeaderboard.svelte';
	import ExpenseCountLeaderboard from './ExpenseCountLeaderboard.svelte';
	import YearChart from './YearChart.svelte';
</script>

<h2 class="mb-4 text-lg font-semibold tracking-tight dark:text-slate-100">
	{$_('stats.yearly_title')}
</h2>

<div class="mb-12 w-full">
	<YearChart />
</div>

<h2 class="mb-4 text-lg font-semibold tracking-tight dark:text-slate-100">
	{$_('leaderboard.title')}
</h2>

<div class="grid grid-cols-1 gap-10 lg:grid-cols-2">
	<div>
		<h2
			class="mb-4 text-sm font-semibold tracking-wide text-base-subtle uppercase dark:text-dark-base-subtle"
		>
			{$_('leaderboard.total_title')}
		</h2>
		<ExpenseTotalLeaderboard />
	</div>

	<div>
		<h2
			class="mb-4 text-sm font-semibold tracking-wide text-base-subtle uppercase dark:text-dark-base-subtle"
		>
			{$_('leaderboard.count_title')}
		</h2>
		<ExpenseCountLeaderboard />
	</div>
</div>
