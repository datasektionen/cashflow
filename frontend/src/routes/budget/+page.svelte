<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { ChevronLeft, ChevronRight, Search, TriangleAlert } from '@lucide/svelte';
	import { afterNavigate, goto, replaceState } from '$app/navigation';
	import { navigating, page } from '$app/state';
	import type { CostCentreType } from '#lib/api/types.ts';
	import { Button, Card, Combobox, Switch } from '#lib/components/ui/index.ts';
	import { formatKronor, formatWholeAmount } from '#lib/money.ts';
	import { rankOptions } from '#lib/search.ts';
	import CostCentreDetail from './CostCentreDetail.svelte';
	import UsageBar from './UsageBar.svelte';

	let { data } = $props();

	// Dims the page while another year loads
	const loading = $derived(navigating.to?.route.id === page.route.id);

	const thisYear = new Date().getFullYear();
	const groups: { key: string; types: CostCentreType[] }[] = [
		{ key: 'committee', types: ['committee'] },
		{ key: 'partition', types: ['partition'] },
		{ key: 'project', types: ['project', 'projectX'] },
		{ key: 'other', types: ['other'] }
	];

	let query = $state('');
	let blownOnly = $state(page.url.searchParams.get('contains_blown') === 'true');
	let selectedId = $state(Number(page.url.searchParams.get('cc')) || null);

	function urlWith(change: Record<string, string | null>) {
		const url = new URL(location.href);
		for (const [key, value] of Object.entries(change)) {
			if (value === null) url.searchParams.delete(key);
			else url.searchParams.set(key, value);
		}
		url.hash = '';
		return url;
	}

	// Only the year needs new data; other changes just update the URL
	const setParams = (change: Record<string, string | null>) =>
		replaceState(urlWith(change), page.state);
	const setYear = (year: number) =>
		goto(urlWith({ year: year >= thisYear ? null : String(year) }), { reset: false });

	function select(id: number) {
		selectedId = id;
		setParams({ cc: String(id) });
	}

	// Parts link here as /budget/#<cost centre name>; the hash keeps the selection on reload
	afterNavigate(() => {
		const name = decodeURIComponent(location.hash.slice(1));
		const match = name && summary.find((cc) => cc.name === name);
		if (match) selectedId = match.id;
	});

	// The list is one tab stop; arrow keys move between cost centres
	function onListKeydown(e: KeyboardEvent) {
		const keys = ['ArrowDown', 'ArrowUp', 'Home', 'End'];
		if (!keys.includes(e.key)) return;
		const buttons = [
			...(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('[data-cc]')
		];
		const current = buttons.indexOf(document.activeElement as HTMLElement);
		const next =
			e.key === 'Home'
				? 0
				: e.key === 'End'
					? buttons.length - 1
					: Math.max(0, Math.min(buttons.length - 1, current + (e.key === 'ArrowDown' ? 1 : -1)));
		e.preventDefault();
		buttons[next]?.focus();
		buttons[next]?.click();
	}

	let nav = $state<HTMLElement | null>(null);

	// Enter picks the best match, ArrowDown moves into the list
	function onSearchKeydown(e: KeyboardEvent) {
		const best = list[0];
		if (!best || (e.key !== 'ArrowDown' && e.key !== 'Enter')) return;
		e.preventDefault();
		const id = e.key === 'Enter' ? best.id : focusId;
		nav?.querySelector<HTMLElement>(`[data-cc="${id}"]`)?.focus();
		if (e.key === 'Enter') select(best.id);
	}

	const summary = $derived(data.summary ?? []);
	// The selection stays within the exceeded filter so the detail never shows a filtered-out cost centre
	const shown = $derived(summary.filter((cc) => !blownOnly || cc.blown_lines > 0));
	const selected = $derived(
		shown.find((cc) => cc.id === selectedId) ??
			shown.find((cc) => Number(cc.amount_uploaded) > 0) ??
			shown[0]
	);
	const list = $derived(query.trim() ? rankOptions(shown, query, (cc) => cc.name) : shown);

	// Keeps the selected cost centre in view, e.g. after a deep link
	$effect(() => {
		nav?.querySelector(`[data-cc="${selected?.id}"]`)?.scrollIntoView({ block: 'nearest' });
	});
	const selectedVisible = $derived(list.some((cc) => cc.id === selected?.id));
	const focusId = $derived(selectedVisible ? selected?.id : list[0]?.id);
</script>

<header class="flex flex-wrap items-center gap-x-6 gap-y-3 pb-6">
	<h1 class="mr-auto text-3xl font-bold tracking-tight">{$_('budget.title')}</h1>
	<label
		class="order-last flex w-full cursor-pointer items-center gap-2 text-sm sm:order-none sm:w-auto"
	>
		<Switch
			checked={blownOnly}
			onCheckedChange={(checked) => {
				blownOnly = checked;
				setParams({ contains_blown: checked ? 'true' : null });
			}}
		/>
		{$_('budget.exceeded_filter_help')}
	</label>
	<div class="-mr-2 flex items-center">
		<Button
			variant="ghost"
			size="icon-sm"
			aria-label={$_('previous')}
			onclick={() => setYear(data.year - 1)}
		>
			<ChevronLeft />
		</Button>
		<span class="w-14 text-center text-lg font-bold tabular-nums">{data.year}</span>
		<Button
			variant="ghost"
			size="icon-sm"
			aria-label={$_('next')}
			disabled={data.year >= thisYear}
			onclick={() => setYear(data.year + 1)}
		>
			<ChevronRight />
		</Button>
	</div>
</header>

<div class="flex flex-col gap-6">
	{#if data.summary === null}
		<p class="text-sm text-danger">{$_('budget.load_error')}</p>
	{:else}
		<div
			class={[
				'grid gap-6 transition-opacity lg:h-[calc(100dvh-12rem)] lg:min-h-[28rem] lg:grid-cols-[20rem_minmax(0,1fr)]',
				loading && 'opacity-60'
			]}
		>
			<Combobox
				items={list}
				getValue={(cc) => String(cc.id)}
				getLabel={(cc) => cc.name}
				value={selected && selectedVisible ? String(selected.id) : ''}
				onchange={(v) => v && select(Number(v))}
				label={$_('budget.search')}
				clearable
				class="lg:hidden"
			>
				{#snippet item(cc)}
					<span class="flex items-center gap-2">
						{cc.name}
						{#if cc.blown_lines > 0}<TriangleAlert class="size-3.5 shrink-0 text-danger" />{/if}
					</span>
				{/snippet}
			</Combobox>
			<Card padded={false} class="hidden min-h-0 flex-col lg:flex">
				<label
					class="flex shrink-0 items-center gap-2.5 border-b border-border px-4 ring-primary ring-inset focus-within:ring-1"
				>
					<Search class="size-4 shrink-0 text-muted-foreground" />
					<input
						type="search"
						bind:value={query}
						onkeydown={onSearchKeydown}
						placeholder={$_('budget.search')}
						class="h-11 min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
					/>
				</label>
				<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
				<nav
					bind:this={nav}
					onkeydown={onListKeydown}
					class="min-h-0 flex-1 overflow-y-auto overscroll-contain py-2"
				>
					{#each groups as group (group.key)}
						{@const items = list.filter((cc) => group.types.includes(cc.type))}
						{#if items.length > 0}
							<p
								class="px-4 pt-3 pb-1.5 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase"
							>
								{$_(`budget.types.${group.key}`)}
							</p>
							<ul>
								{#each items as cc (cc.id)}
									{@const active = cc.id === selected?.id}
									<li>
										<button
											type="button"
											aria-current={active || undefined}
											data-cc={cc.id}
											tabindex={cc.id === focusId ? 0 : -1}
											onclick={() => select(cc.id)}
											class={[
												'flex w-full cursor-pointer flex-col gap-1.5 px-4 py-2.5 text-left text-sm transition-colors',
												active ? 'bg-accent font-semibold text-accent-foreground' : 'hover:bg-muted'
											]}
										>
											<span class="flex items-center gap-2">
												<span class="min-w-0 flex-1 wrap-break-word">{cc.name}</span>
												{#if cc.blown_lines > 0}
													<TriangleAlert class="size-3.5 shrink-0 text-danger" />
												{/if}
												<span class="text-xs font-normal text-muted-foreground tabular-nums">
													{formatWholeAmount(cc.amount_uploaded)} / {formatKronor(cc.expense)}
												</span>
											</span>
											<UsageBar
												budget={cc.expense}
												uploaded={Number(cc.amount_uploaded)}
												attested={Number(cc.amount_attested)}
												paid={Number(cc.amount_paid)}
												thin
											/>
										</button>
									</li>
								{/each}
							</ul>
						{/if}
					{/each}
					{#if list.length === 0}
						<p class="px-4 py-6 text-center text-sm text-muted-foreground">{$_('no_results')}</p>
					{/if}
				</nav>
			</Card>

			{#if selected}
				<div class="min-w-0 lg:min-h-0">
					<CostCentreDetail costCentre={selected} year={data.year} {blownOnly} user={data.user} />
				</div>
			{/if}
		</div>
	{/if}
</div>
