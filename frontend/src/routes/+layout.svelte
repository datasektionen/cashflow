<script lang="ts">
	import './layout.css';
	import '$lib/i18n'; // initialize i18n
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import favicon from '$lib/assets/favicon.svg';
	import { DarkMode } from 'flowbite-svelte';
	import NavLink from '$lib/components/NavLink.svelte';

	let { children, data } = $props();
</script>

<nav
	class="fixed flex h-16 w-screen flex-row justify-between bg-money-green-600 px-4 text-white drop-shadow-xl lg:px-64 dark:bg-dark-base-200 dark:text-dark-base-text"
>
	<div class="flex h-full">
		{#if data.user != null}
			<NavLink to="/expenses/new" text={$_('new_expense.title')}></NavLink>
			<NavLink to="/invoices/new" text={$_('new_invoice')}></NavLink>
			<NavLink to="/{data.user.username}/expenses/" text={$_('user_expenses')}></NavLink>
			<NavLink to="/admin/" text={$_('admin')}></NavLink>
		{/if}
	</div>

	<div class="flex h-full items-center">
		<DarkMode class="items-center" />
		{#if data.user != null}
			<p>{data.user.first_name} {data.user.last_name}</p>
		{:else}
			<a href="http://localhost:8000/login?next=http%3A%2F%2Flocalhost%3A5173%2F">{$_('login')}</a>
		{/if}
	</div>
</nav>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div
	class="base-text-base-text flex h-full flex-col justify-between bg-base-200 pt-16 dark:bg-dark-base-100 dark:text-dark-base-text"
>
	<div class="h-16 w-screen p-4">
		<h1 class="flex h-full items-center justify-center text-2xl font-bold">
			{$_(page.data.title_key)}
		</h1>
	</div>

	<main
		class="mx-64 h-full min-h-screen bg-base-100 md:p-4 lg:p-16 dark:bg-dark-base-100 dark:text-dark-base-text"
	>
		{@render children()}
	</main>

	<footer
		class="flex h-64 items-center bg-money-green-700 px-64 py-4 text-white dark:bg-dark-base-200 dark:text-dark-base-text"
	>
		<div class="flex h-full w-full flex-row justify-between">
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
</div>
