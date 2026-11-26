<script lang="ts">
	import { page } from '$app/state';
	import { getContext, type Component } from 'svelte';
	import { Badge } from '#lib/components/ui/index.ts';
	import { isActivePath } from '#lib/nav.ts';

	let props: { to: string; text: string; icon?: Component; badge?: number } = $props();

	// Icon-only on desktop when the sidebar is collapsed
	const slim = getContext<() => boolean>('sidebar-slim');
	const active = $derived(isActivePath(props.to, page.url.pathname));
</script>

<a
	href={props.to}
	aria-current={active ? 'page' : undefined}
	title={slim() ? props.text : undefined}
	class={[
		'relative flex h-9 w-full shrink-0 items-center gap-2.5 px-2.5 text-sm transition-colors',
		slim() && 'lg:justify-center lg:px-0',
		active
			? 'bg-primary font-semibold text-primary-foreground'
			: 'font-medium text-muted-foreground hover:bg-muted hover:text-foreground'
	]}
>
	{#if props.icon}
		<props.icon class="size-4 shrink-0" />
	{/if}
	<span class={['truncate', slim() && 'lg:sr-only']}>{props.text}</span>
	{#if props.badge != null && props.badge > 0}
		<Badge
			class={[
				'ml-auto tabular-nums',
				active && 'bg-primary-foreground text-primary',
				slim() && 'lg:absolute lg:top-0 lg:right-0 lg:px-1 lg:text-[10px]'
			]}
		>
			{props.badge}
		</Badge>
	{/if}
</a>
