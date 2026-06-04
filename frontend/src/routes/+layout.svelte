<script lang="ts">
	import '../app.css';
	import '$lib/i18n'; // initialize i18n
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import favicon from '$lib/assets/favicon.svg';
	import { DarkMode } from 'flowbite-svelte';
	import NavLink from '$lib/components/NavLink.svelte';
	import { Separator } from 'bits-ui';
	import type { LayoutProps } from './$types';
	import { type Alert, alerts } from '$lib/stores/alerts';
	import AlertToast from '$lib/components/AlertToast.svelte';

	let { children, data }: LayoutProps = $props();

	let currentAlerts: Alert[] = $state([]);

	alerts.subscribe((val) => (currentAlerts = val));
</script>

<nav
	class="fixed z-40 h-16 w-full bg-money-green-600 text-white drop-shadow-xl dark:bg-dark-base-200 dark:text-dark-base-text"
>
	<div class="mx-auto flex h-full max-w-7xl flex-row justify-between px-4 lg:px-8">
		<div class="flex h-full">
			{#if data.user != null}
				<NavLink to="/expenses/new" text={$_('new_expense.title')}></NavLink>
				<NavLink to="/invoices/new" text={$_('new_invoice.title')}></NavLink>
				<NavLink to="/{data.user.username}/claims/" text={$_('user_claims')}></NavLink>
				<NavLink to="/admin/" text={$_('admin')}></NavLink>
			{/if}
		</div>

		<div class="flex h-full items-center">
			<DarkMode class="items-center" />
			{#if data.user != null}
				<p>{data.user.first_name} {data.user.last_name}</p>
			{:else}
				<a href="http://localhost:8000/login?next=http%3A%2F%2Flocalhost%3A5173%2F">{$_('login')}</a
				>
			{/if}
		</div>
	</div>
</nav>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<!-- Alerts -->
<div class="fixed right-20 bottom-20 z-50 flex flex-col gap-2">
	{#each currentAlerts as alert (alert.id)}
		<AlertToast {alert} />
	{/each}
</div>

<div
	class="base-text-base-text flex min-h-screen flex-col bg-base-200 pt-16 dark:bg-dark-base-100 dark:text-dark-base-text"
>
	{#if page.data.title_key != null}
		<header class="mx-auto w-full max-w-7xl px-4 lg:px-8">
			<h1 class="pt-12 pb-6 text-3xl font-semibold tracking-tight">
				{$_(page.data.title_key)}
			</h1>
			<Separator.Root
				orientation="horizontal"
				class="h-px w-full bg-base-subtle dark:bg-dark-base-200"
			/>
		</header>
	{/if}

	<main class="mx-auto w-full max-w-7xl flex-1 px-4 py-8 lg:px-8 dark:text-dark-base-text">
		{@render children()}
	</main>

	{#if data.user == null}
		<footer class="bg-money-green-700 text-white dark:bg-dark-base-200 dark:text-dark-base-text">
			<div class="mx-auto flex h-64 max-w-7xl flex-row justify-between px-4 py-4 lg:px-8">
				<div class="w-96">
					<h2 class="font-bold">{$_('footer.about.title')}</h2>
					<p>
						{@html $_('footer.about.body').replaceAll(
							'{compsciwebsite}',
							'<a class="font-bold" href="https://datasektionen.se/">Konglig Datasektionen</a>'
						)}
					</p>
				</div>
				<div class="w-96">
					<h2 class="font-bold">{$_('footer.help.title')}</h2>
					<p>
						{$_('footer.help.body')}
					</p>
				</div>
				<div class="w-96">
					<h2 class="font-bold">{$_('footer.issues.title')}</h2>
					<p>
						{$_('footer.issues.body')}
					</p>
				</div>
			</div>
		</footer>
	{/if}
</div>
