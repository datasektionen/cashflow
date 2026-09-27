<script lang="ts">
	import Checkbox from '$lib/components/Checkbox.svelte';
	import { page } from '$app/state';
	import ExpandedCostCentre from './ExpandedCostCentre.svelte';
	import { ChevronDown, ChevronUp } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Skeleton from '$lib/components/ui/Skeleton.svelte';

	let { data } = $props();

	let expanded: number | null = $state(null);

	// True only when the expanded row has been scrolled out of view above the viewport
	let showScrollButton = $state(false);

	onMount(() => {
		// "pre-expand" and scroll to the cost centre specified in the hash section of the url
		// e.g. loading /budget/#Dive will expand that row and scroll to it
		let costCentre: string | null =
			page.url.hash != '' ? decodeURIComponent(page.url.hash.replace('#', '')) : null;
		let resolved = data.costCentres.find((cc, _i, _arr) => {
			return cc.name == costCentre;
		});
		expanded = resolved ? resolved.id : null;
		scrollToExpanded();
	});

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

	let filterBlown = $state(false);
	let loading = $state(false);

	async function handleFilterChange(checked: boolean) {
		loading = true;
		const url = new URL(page.url);
		if (checked) {
			url.searchParams.set('contains_blown', 'true');
			filterBlown = true;
		} else {
			url.searchParams.delete('contains_blown');
			filterBlown = false;
		}
		await goto(url, { noScroll: true });
		loading = false;

		if (expanded != null) {
			scrollToExpanded();
		}
	}
</script>

<div class={['flex flex-row py-4']}>
	<span>
		<Checkbox name="Test" onCheckedChange={handleFilterChange}>
			<p>{$_('budget.exceeded_filter_help')}</p>
		</Checkbox>
	</span>
</div>

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
			{#if loading}
				{@const widths = ['w-24', 'w-32', 'w-40', 'w-48']}
				{#each { length: 20 }}
					{@const w = widths[Math.floor(Math.random() * widths.length)]}
					<tr
						class="group cursor-pointer scroll-mt-20 border-b border-b-base-400 hover:bg-base-200 dark:border-dark-base-150 dark:hover:bg-dark-base-200"
					>
						<td class="px-4 py-3">
							<div class="flex h-6 items-center">
								<Skeleton class="h-4 {w} rounded-md"></Skeleton>
							</div>
						</td>
					</tr>
				{/each}
			{/if}

			{#each data.costCentres as costCentre}
				{@const Chevron = expanded === costCentre.id ? ChevronUp : ChevronDown}
				<tr
					class="group cursor-pointer scroll-mt-20 border-b border-b-base-400 hover:bg-base-200 dark:border-dark-base-150 dark:hover:bg-dark-base-200"
					id="cost-centre-{costCentre.id}"
					onclick={async () => {
						const url = new URL(page.url);
						if (expanded === costCentre.id) {
							expanded = null;
							url.hash = '';
						} else {
							expanded = expanded === costCentre.id ? null : costCentre.id;
							url.hash = encodeURIComponent(costCentre.name);
							scrollToExpanded();
						}
						await goto(url, { noScroll: true });
					}}
				>
					<td class="flex flex-row gap-2 px-4 py-3">
						{costCentre.name}
						{#if costCentre.contains_blown}
							<span class="my-auto size-2 animate-pulse rounded-full bg-amber-400"></span>
						{/if}
					</td>
					<td class="px-4 py-3 text-right">
						<Chevron class="ml-auto size-5 transition-transform group-hover:scale-125" />
					</td>
				</tr>

				{#if expanded === costCentre.id}
					<tr class="border-b border-b-base-400 dark:border-dark-base-150">
						<td colspan="2" class="px-4 py-3">
							<ExpandedCostCentre {costCentre} {filterBlown} user={data.user} />
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
