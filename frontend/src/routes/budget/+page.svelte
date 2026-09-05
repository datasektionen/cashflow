<script lang="ts">
	import ExpandedCostCentre from './ExpandedCostCentre.svelte';
	import { ChevronDown, ChevronUp } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';

	let { data } = $props();

	let expanded: number | null = $state(null);
</script>

<div class="border border-base-500 p-2 dark:border-dark-base-200">
	<table class="w-full table-fixed">
		<thead>
			<tr>
				<th
					class="px-4 py-3 text-left text-xs font-medium text-base-subtle uppercase dark:text-dark-base-subtle"
				>
					{$_('cost_centre')}
				</th>
				<th class="w-12"></th>
			</tr>
		</thead>
		<tbody>
			{#each data.costCentres as costCentre}
				{@const Chevron = expanded === costCentre.id ? ChevronUp : ChevronDown}
				<tr
					class="group cursor-pointer border-b border-b-base-400 hover:bg-base-200 dark:border-dark-base-150 dark:hover:bg-dark-base-200"
					onclick={() => {
						expanded = expanded === costCentre.id ? null : costCentre.id;
					}}
				>
					<td class="px-4 py-3">{costCentre.name}</td>
					<td class="px-4 py-3 text-right">
						<Chevron class="ml-auto size-5 transition-transform group-hover:scale-125" />
					</td>
				</tr>

				{#if expanded === costCentre.id}
					<tr class="border-b border-b-base-400 dark:border-dark-base-150">
						<td colspan="2" class="bg-base-300 px-4 py-3 dark:bg-dark-base-100">
							<ExpandedCostCentre {costCentre} />
						</td>
					</tr>
				{/if}
			{/each}
		</tbody>
	</table>
</div>
