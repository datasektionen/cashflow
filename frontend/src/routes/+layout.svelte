<script lang="ts">
	import '../app.css';
	import '#lib/i18n/index.ts'; // initialize i18n
	import { page } from '$app/state';
	import { afterNavigate, beforeNavigate } from '$app/navigation';
	import { tick } from 'svelte';
	import { _ } from 'svelte-i18n';
	import NavBar from '#lib/components/nav/NavBar.svelte';
	import { Tooltip } from 'bits-ui';
	import type { LayoutProps } from './$types';
	import { alerts } from '#lib/stores/alerts.ts';
	import AlertToast from '#lib/components/AlertToast.svelte';
	import { PageHeader, Skeleton } from '#lib/components/ui/index.ts';
	import Sidebar from '#lib/components/nav/Sidebar.svelte';
	import { hasAdminAccess } from '#lib/auth.ts';
	import { setPreferences } from '#lib/preferences.svelte.ts';
	import type { Snippet } from 'svelte';

	let { children, data }: LayoutProps = $props();

	// On desktop the content scrolls below the navbar instead of the window
	let scroller: HTMLDivElement;
	const scrollPositions = new Map<string, number>();
	beforeNavigate(({ from }) => {
		if (from) scrollPositions.set(from.url.href, scroller.scrollTop);
	});
	afterNavigate(async ({ from, to, type }) => {
		if (!to) return;
		if (type === 'popstate') {
			await tick();
			scroller.scrollTop = scrollPositions.get(to.url.href) ?? 0;
		} else if (from?.url.pathname !== to.url.pathname) {
			scroller.scrollTop = 0;
		}
	});

	// Scroll keys with nothing focused scroll the content, while Tab still starts at the top bar
	const scrollKeys = ['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '];
	function onWindowKeydown(e: KeyboardEvent) {
		if (document.activeElement === document.body && scrollKeys.includes(e.key))
			scroller.focus({ preventScroll: true });
	}

	const adminView = $derived(page.url.pathname.startsWith('/admin'));
	const canAccessAdmin = $derived(hasAdminAccess(data.user));

	// Pages may return `title` as a promise
	let awaitedTitle: string | null = $state(null);
	$effect(() => {
		const title = page.data.title;
		if (!(title instanceof Promise)) return;
		awaitedTitle = null;
		let stale = false;
		title.then(
			(v) => {
				if (!stale) awaitedTitle = v;
			},
			() => {}
		);
		return () => {
			stale = true;
		};
	});
	const titlePending = $derived(page.data.title instanceof Promise && awaitedTitle == null);
	const pageTitle = $derived.by(() => {
		const title = page.data.title instanceof Promise ? awaitedTitle : page.data.title;
		return title ?? (page.data.title_key ? $_(page.data.title_key) : null);
	});

	let sidebarOpen = $state(false);
	// svelte-ignore state_referenced_locally
	const prefs = setPreferences(data.preferences);

	const aboutBody = $derived($_('footer.about.body').split('{compsciwebsite}'));
</script>

<svelte:window onkeydown={onWindowKeydown} />

<NavBar user={data.user} bind:sidebarOpen {canAccessAdmin} />

{#if data.user != null}
	<Sidebar user={data.user} bind:open={sidebarOpen} bind:slim={prefs.sidebarSlim} />
{/if}

<svelte:head>
	<title>{pageTitle ? `${pageTitle} | Cashflow` : 'Cashflow'}</title>
	<link rel="icon" href="/favicon.ico" sizes="any" />
	<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
	<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
	<link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png" />
	<link rel="icon" type="image/png" sizes="192x192" href="/android-icon-192x192.png" />
	<link rel="apple-touch-icon" sizes="57x57" href="/apple-icon-57x57.png" />
	<link rel="apple-touch-icon" sizes="60x60" href="/apple-icon-60x60.png" />
	<link rel="apple-touch-icon" sizes="72x72" href="/apple-icon-72x72.png" />
	<link rel="apple-touch-icon" sizes="76x76" href="/apple-icon-76x76.png" />
	<link rel="apple-touch-icon" sizes="114x114" href="/apple-icon-114x114.png" />
	<link rel="apple-touch-icon" sizes="120x120" href="/apple-icon-120x120.png" />
	<link rel="apple-touch-icon" sizes="144x144" href="/apple-icon-144x144.png" />
	<link rel="apple-touch-icon" sizes="152x152" href="/apple-icon-152x152.png" />
	<link rel="apple-touch-icon" sizes="180x180" href="/apple-icon-180x180.png" />
	<link rel="manifest" href="/manifest.json" />
	<meta name="msapplication-TileImage" content="/ms-icon-144x144.png" />
</svelte:head>

<!-- Bottom left, away from the action buttons on the right; on phones above the bottom action bar.
     Only the newest few, so quick repeated actions don't stack up over the page. -->
<div class="fixed bottom-20 left-4 z-50 flex flex-col gap-2 lg:bottom-6 lg:left-6">
	{#each $alerts.slice(-3) as alert (alert.id)}
		<AlertToast {alert} />
	{/each}
</div>

{#snippet footerColumn(title: string, body: Snippet)}
	<div class="flex flex-col gap-2 lg:max-w-sm">
		<h2 class="text-sm font-semibold">{title}</h2>
		<p class="text-sm text-white/80">{@render body()}</p>
	</div>
{/snippet}

<div
	bind:this={scroller}
	data-page-scroller
	tabindex="-1"
	class="flex min-h-screen flex-col overflow-x-clip bg-background pt-16 outline-none lg:fixed lg:inset-x-0 lg:top-16 lg:bottom-0 lg:min-h-0 lg:overflow-y-auto lg:pt-0"
>
	<main
		class={[
			'w-full flex-1',
			page.data.fill && 'lg:flex lg:min-h-0 lg:flex-col',
			adminView
				? ['px-4 py-6 lg:pr-8', prefs.sidebarSlim ? 'lg:pl-24' : 'lg:pl-68']
				: 'mx-auto max-w-7xl px-4 py-6 lg:px-8'
		]}
	>
		{#if (pageTitle != null || titlePending) && !page.data.ownHeader}
			<PageHeader>
				{#snippet heading()}
					{#if titlePending}
						<Skeleton class="h-[1lh] w-64 animate-delayed-fade-in" />
					{:else}
						{pageTitle}
					{/if}
				{/snippet}
			</PageHeader>
		{/if}
		<Tooltip.Provider>
			{@render children()}
		</Tooltip.Provider>
	</main>

	{#if data.user == null}
		<footer class="bg-brand text-white">
			<div
				class="mx-auto grid max-w-7xl gap-8 px-4 py-10 lg:grid-cols-3 lg:justify-between lg:px-8"
			>
				{#snippet about()}
					{aboutBody[0]}<a
						class="font-medium text-white underline underline-offset-4"
						href="https://datasektionen.se/">Konglig Datasektionen</a
					>{aboutBody[1]}
				{/snippet}
				{#snippet help()}{$_('footer.help.body')}{/snippet}
				{#snippet issues()}{$_('footer.issues.body')}{/snippet}
				{@render footerColumn($_('footer.about.title'), about)}
				{@render footerColumn($_('footer.help.title'), help)}
				{@render footerColumn($_('footer.issues.title'), issues)}
			</div>
		</footer>
	{/if}
</div>
