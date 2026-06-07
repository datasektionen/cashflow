<script lang="ts">
	import '../app.css';
	import '$lib/i18n'; // initialize i18n
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import favicon from '$lib/assets/favicon.svg';
	import { DarkMode } from 'flowbite-svelte';
	import NavLink from '$lib/components/NavLink.svelte';
	import SideNavLink from '$lib/components/SideNavLink.svelte';
	import { Separator } from 'bits-ui';
	import type { LayoutProps } from './$types';
	import { type Alert, alerts } from '$lib/stores/alerts';
	import AlertToast from '$lib/components/AlertToast.svelte';
	import {
		ReceiptText,
		FileText,
		Receipt,
		Files,
		CircleCheck,
		Stamp,
		Banknote,
		BookText
	} from '@lucide/svelte';

	let { children, data }: LayoutProps = $props();

	let currentAlerts: Alert[] = $state([]);
	const adminView = $derived(page.url.pathname.startsWith('/admin'));

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

{#if adminView}
	<aside
		class="fixed top-16 left-0 z-30 flex h-[calc(100vh-4rem)] w-52 flex-col gap-1 border-r border-base-500 bg-base-200 px-3 py-4 text-sm dark:border-dark-base-200 dark:bg-dark-base-100"
	>
		<SideNavLink to="/expenses/new" text={$_('new_expense.title')} icon={ReceiptText} />
		<SideNavLink to="/invoices/new" text={$_('new_invoice.title')} icon={FileText} />

		<p
			class="mt-4 mb-1 px-3 text-xs font-semibold tracking-wider text-base-subtle uppercase dark:text-dark-base-subtle"
		>
			{$_('admin')}
		</p>
		<SideNavLink to="/admin/expenses" text={$_('admin_expenses.nav_title')} icon={Receipt} />
		<SideNavLink to="/admin/invoices" text={$_('admin_invoices.nav_title')} icon={Files} />

		{#if data.user?.permissions}
			{@const perms = data.user.permissions}
			{#if perms.confirm || perms.attest.length > 0 || perms.pay || perms.accounting.length > 0}
				<Separator.Root
					orientation="horizontal"
					class="my-3 h-px w-full bg-base-500 dark:bg-dark-base-200"
				/>
				{#if perms.attest.length > 0}
					<SideNavLink to="/admin/attest" text={$_('tasks.attest')} icon={Stamp} />
				{/if}
				{#if perms.confirm}
					<SideNavLink to="/admin/confirm" text={$_('tasks.confirm')} icon={CircleCheck} />
				{/if}
				{#if perms.pay}
					<SideNavLink to="/admin/pay" text={$_('tasks.pay')} icon={Banknote} />
				{/if}
				{#if perms.accounting.length > 0}
					<SideNavLink to="/admin/account" text={$_('tasks.account')} icon={BookText} />
				{/if}
			{/if}
		{/if}

		<a
			href="https://github.com/datasektionen/cashflow"
			target="_blank"
			rel="noreferrer"
			class="mt-auto flex items-center justify-start gap-2.5 px-3 text-xs leading-tight text-base-subtle opacity-40 transition-opacity hover:opacity-100 dark:text-dark-base-subtle"
		>
			<svg class="size-5 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
				<path
					d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"
				/>
			</svg>
			<span class="flex flex-col">
				<span>Cashflow</span>
				<span>Datasektionen</span>
			</span>
		</a>
	</aside>
{/if}

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
	{#if page.data.title_key != null || page.data.title != null}
		<header class="mx-auto w-full max-w-7xl px-4 lg:px-8">
			<h1 class="pt-12 pb-6 text-3xl font-semibold tracking-tight">
				{page.data.title ?? $_(page.data.title_key)}
			</h1>
			<Separator.Root
				orientation="horizontal"
				class="h-px w-full bg-base-subtle dark:bg-dark-base-200"
			/>
		</header>
	{/if}

	<main
		class={[
			'mx-auto w-full max-w-7xl flex-1 px-4 py-8 lg:px-8 dark:text-dark-base-text',
			adminView && 'pl-56'
		]}
	>
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
