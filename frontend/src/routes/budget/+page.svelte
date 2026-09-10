<script lang="ts">
	import ExpandedCostCentre from './ExpandedCostCentre.svelte';
	import { ChevronDown, ChevronUp } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';

	let { data } = $props();

	let expanded: number | null = $state(null);

	// True only when the expanded row has been scrolled out of view above the viewport
	let showScrollButton = $state(false);

	$effect(() => {
		if (expanded === null) {
			showScrollButton = false;
			return;
		}
		const element = document.getElementById(`cost-centre-${expanded}`);
		if (!element) {
			return;
		}
		const observer = new IntersectionObserver(
			([entry]) => {
				// View is below the row when it's not intersecting and sits above the root's
				// top edge (rootBounds.top already includes the rootMargin offset)
				const rootTop = entry.rootBounds?.top ?? 80;
				showScrollButton = !entry.isIntersecting && entry.boundingClientRect.top < rootTop;
			},
			// Matches the navbar offset (scroll-mt-20 = 5rem)
			{ rootMargin: '-80px 0px 0px 0px' }
		);
		observer.observe(element);
		return () => observer.disconnect();
	});

	// Scrolls the view to the expanded row
	// Useful for mobile and cost centres with many budget lines for the user to go back easily
	function scrollToExpanded() {
		const element = document.getElementById(`cost-centre-${expanded}`);
		if (!element) {
			return;
		}
		element.scrollIntoView({
			behavior: 'smooth'
		});
	}
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
					class="group cursor-pointer scroll-mt-20 border-b border-b-base-400 hover:bg-base-200 dark:border-dark-base-150 dark:hover:bg-dark-base-200"
					id="cost-centre-{costCentre.id}"
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

	<button
		onclick={() => {
			scrollToExpanded();
		}}
		class={[
			'bg-black/60 p-1 text-white shadow-lg ring-1 ring-white/10 backdrop-blur-sm',
			'hover-cursor transition-all',
			showScrollButton ? 'flex opacity-100 md:hidden md:opacity-0' : 'hidden opacity-0',
			'fixed bottom-5 left-1/2 h-8 w-16 -translate-x-1/2'
		]}
	>
		<ChevronUp class="m-auto" />
	</button>
</div>
