<script lang="ts">
	import { page } from '$app/state';
	import type { Component } from 'svelte';

	let props: { to: string; text: string; icon?: Component; badge?: number } = $props();

	const normalizePath = (path: string) => path.replace(/\/+$/, '') || '/';
	const active = $derived.by(() => {
		const target = normalizePath(props.to);
		const current = normalizePath(page.url.pathname);
		if (target === '/') return current === '/';
		return current === target || current.startsWith(target + '/');
	});
</script>

<a
	href={props.to}
	class={[
		'flex w-full items-center gap-2.5 border-l-2 px-3 py-2 transition-colors',
		active
			? 'border-money-green-600 bg-money-green-600/10 font-medium text-base-text dark:text-dark-base-text'
			: 'border-transparent text-base-subtle hover:bg-base-300 hover:text-base-text dark:text-dark-base-subtle dark:hover:bg-dark-base-200 dark:hover:text-dark-base-text'
	]}
>
	{#if props.icon}
		<props.icon
			class={['size-4 shrink-0', active && 'text-money-green-600 dark:text-money-green-500']}
		/>
	{/if}
	<span>{props.text}</span>
	{#if props.badge != null && props.badge > 0}
		<span
			class="ml-auto rounded-full bg-money-green-600/15 px-1.5 py-0.5 text-xs font-medium text-money-green-700 dark:bg-money-green-600/20 dark:text-money-green-400"
		>
			{props.badge}
		</span>
	{/if}
</a>
