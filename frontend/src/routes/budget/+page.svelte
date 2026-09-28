<script lang="ts">
	import Checkbox from '$lib/components/Checkbox.svelte';
	import { page } from '$app/state';
	import type { CostCentre } from '$lib/api/types.js';
	import ExpandedCostCentre from './ExpandedCostCentre.svelte';
	import { ChevronDown, ChevronUp, Receipt, SquareArrowOutUpRight } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';
	import { afterNavigate, goto } from '$app/navigation';
	import { tick } from 'svelte';
	import Skeleton from '$lib/components/ui/Skeleton.svelte';

	let { data } = $props();

	let expanded: number | null = $state(null);

	// True only when the expanded row has been scrolled out of view above the viewport
	let showScrollButton = $state(false);

	// "pre-expand" and scroll to the cost centre specified in the hash section of the url
	// e.g. loading /budget/#Dive will expand that row and scroll to it.
	afterNavigate(async () => {
		const costCentre: string | null =
			page.url.hash != '' ? decodeURIComponent(page.url.hash.replace('#', '')) : null;
		const resolved = data.costCentres.find((cc) => cc.name == costCentre);
		const target = resolved ? resolved.id : null;
		if (target === expanded) {
			return;
		}
		expanded = target;
		await tick();
		scrollToExpanded();
	});

	// Context menu
	let ctx: { selected: CostCentre; x: number; y: number } | null = $state(null);
	// Dismiss context table
	$effect(() => {
		if (!ctx) return;
		const close = () => (ctx = null);
		const onKeyDown = (e: KeyboardEvent) => {
			if (e.key === 'Escape') close();
		};
		window.addEventListener('click', close);
		window.addEventListener('scroll', close, true);
		window.addEventListener('keydown', onKeyDown);
		return () => {
			window.removeEventListener('click', close);
			window.removeEventListener('scroll', close, true);
			window.removeEventListener('keydown', onKeyDown);
		};
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

	let filterBlown = $state(page.url.searchParams.get('contains_blown') == 'true');
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
	const itemClass =
		'flex w-full cursor-pointer flex-row items-center gap-x-2 px-3 py-2 text-left transition-colors hover:bg-base-300 focus-visible:bg-base-300 focus-visible:outline-none dark:hover:bg-dark-base-300 dark:focus-visible:bg-dark-base-300';
</script>

<div class={['flex flex-row py-4']}>
	<span>
		<Checkbox name="Test" onCheckedChange={handleFilterChange} checked={filterBlown}>
			<p>{$_('budget.exceeded_filter_help')}</p>
		</Checkbox>
	</span>
</div>

<!-- Context menu -->
{#if ctx != null}
	<div
		role="menu"
		class={[
			'fixed flex w-52 flex-col border border-base-500 bg-base-100 py-1 shadow-lg',
			'text-sm text-base-text dark:border-dark-base-300 dark:bg-dark-base-200 dark:text-dark-base-text'
		]}
		style="left: {ctx.x}px; top: {ctx.y}px"
	>
		<a
			href="/admin/expenses/?cost_centre={ctx.selected.name}"
			role="menuitem"
			class={itemClass}
			target="_blank"
			rel="noopener noreferrer"
		>
			<Receipt class="size-4" />
			{$_('Visa utlägg')}
			<SquareArrowOutUpRight class="ml-auto size-3 text-base-subtle dark:text-dark-base-subtle" />
		</a>
		<a
			href="/admin/invoices/?cost_centre={ctx.selected.name}"
			role="menuitem"
			class={itemClass}
			target="_blank"
			rel="noopener noreferrer"
		>
			<Receipt class="size-4" />
			{$_('Visa fakturor')}
			<SquareArrowOutUpRight class="ml-auto size-3 text-base-subtle dark:text-dark-base-subtle" />
		</a>
	</div>
{/if}

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
					oncontextmenu={(e) => {
						e.preventDefault();
						ctx = { selected: costCentre, x: e.clientX, y: e.clientY };
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
