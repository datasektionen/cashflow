<script lang="ts" module>
	export function rangeStart(range: number): string {
		const now = new Date();
		const year = now.getFullYear();
		const month = String(now.getMonth() + 1).padStart(2, '0');
		if (range === 1) return `${year}-01-01`;
		if (range === 2) return `${year}-${month}-01`;
		return '2000-01-01';
	}
</script>

<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { SegmentedControl } from '#lib/components/ui/index.ts';

	let { range = $bindable(0) }: { range?: number } = $props();
</script>

<SegmentedControl
	size="sm"
	class="w-fit"
	bind:value={() => String(range), (v) => (range = Number(v))}
	items={[
		{ value: '0', label: $_('leaderboard.all_time') },
		{ value: '1', label: $_('leaderboard.year') },
		{ value: '2', label: $_('leaderboard.month') }
	]}
/>
