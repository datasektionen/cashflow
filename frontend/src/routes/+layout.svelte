<script lang="ts">
	import './layout.css';
	import '$lib/i18n'; // initialize i18n
	import { _ } from 'svelte-i18n';
	import favicon from '$lib/assets/favicon.svg';
	import {DarkMode} from "flowbite-svelte";

	let { children } = $props();
</script>

<nav class="flex flex-row justify-between px-4 h-16 bg-primary-600  text-white dark:bg-gray-800 ">
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

	<div class="h-full flex items-center">
		<DarkMode class="items-center"/>
	</div>

</nav>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>
{@render children()}
