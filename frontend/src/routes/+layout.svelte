<script lang="ts">
	import './layout.css';
	import '$lib/i18n'; // initialize i18n
	import type { LayoutProps } from './$types';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import favicon from '$lib/assets/favicon.svg';
	import { DarkMode } from 'flowbite-svelte';

	let { data, children }: LayoutProps = $props();
</script>

<nav
	class="fixed flex h-16 w-screen flex-row justify-between bg-primary-600 px-4 text-white drop-shadow-xl lg:px-64 dark:bg-gray-800"
>
	<div class="flex h-full">
		<a
			href="/"
			class="flex h-full items-center p-2 text-xl text-white transition-all hover:bg-primary-500"
			>{$_('new_expense')}</a
		>
		<a
			href="/"
			class="flex h-full items-center p-2 text-xl text-white transition-all hover:bg-primary-500"
			>{$_('new_invoice')}</a
		>
		<a
			href="/"
			class="flex h-full items-center p-2 text-xl text-white transition-all hover:bg-primary-500"
			>{$_('user_expenses')}</a
		>
		<a
			href="/"
			class="flex h-full items-center p-2 text-xl text-white transition-all hover:bg-primary-500"
			>{$_('admin')}</a
		>
	</div>

	<div class="flex h-full items-center">
		<DarkMode class="items-center" />
	</div>
</nav>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="flex h-screen flex-col justify-between pt-16">
	<div class="h-16 w-screen bg-primary-500 dark:bg-gray-700">
		<h1 class="flex h-full items-center justify-center text-2xl font-bold text-white">
			{$_(page.data.title_key)}
		</h1>
	</div>

	<main class="h-full px-64 py-16">
		{@render children()}
	</main>

	<footer class="flex h-64 items-center bg-primary-600 px-64 py-4 text-white dark:bg-gray-800">
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
