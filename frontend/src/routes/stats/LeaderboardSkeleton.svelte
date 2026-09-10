<script lang="ts">
	import Skeleton from '$lib/components/ui/Skeleton.svelte';

	let { rows = 8 }: { rows?: number } = $props();
</script>

<div class="overflow-x-auto">
	<table class="w-full border-collapse">
		<tbody>
			{#each { length: rows } as _, idx (idx)}
				<tr class="border-b border-b-base-400 last:border-0 dark:border-dark-base-150">
					<td class="w-16 px-4 py-3">
						<Skeleton class="mx-auto size-7 rounded-full" />
					</td>
					<td class="w-14 px-4 py-3">
						<Skeleton class="rounded-full {idx < 3 ? 'size-10' : 'size-7'}" />
					</td>
					<td class="px-4 py-3">
						<Skeleton class="h-4 max-w-full rounded-sm {idx < 3 ? 'w-40' : 'w-28'}" />
					</td>
					<td class="px-4 py-3">
						<Skeleton class="ml-auto h-4 w-16 rounded-sm" />
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
</div>
