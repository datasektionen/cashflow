<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Card, Section } from '#lib/components/ui/index.ts';
	import { formatDineroAmount } from '#lib/money.ts';
	import Leaderboard from './Leaderboard.svelte';
	import YearChart from './YearChart.svelte';
</script>

<div class="flex flex-col gap-8">
	<Section title={$_('stats.yearly_title')}>
		<Card>
			<YearChart />
		</Card>
	</Section>

	<Section title={$_('leaderboard.title')}>
		<div class="grid grid-cols-1 gap-6 lg:grid-cols-2">
			<Leaderboard
				title={$_('leaderboard.total_title')}
				help={$_('leaderboard.help')}
				valueLabel={$_('leaderboard.amount')}
				value={(entry) => formatDineroAmount(entry.expense_total)}
			/>
			<Leaderboard
				title={$_('leaderboard.count_title')}
				help={$_('leaderboard.help_count')}
				valueLabel={$_('leaderboard.count')}
				ordering="-expense_count"
				value={(entry) => entry.expense_count}
			/>
		</div>
	</Section>
</div>
