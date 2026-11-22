<script lang="ts">
	import { page } from '$app/state';
	import { isActivePath } from '#lib/nav.ts';

	let props: { to: string; text: string } = $props();
	const active = $derived(isActivePath(props.to, page.url.pathname));
</script>

<a
	href={props.to}
	aria-current={active ? 'page' : undefined}
	class={[
		'relative flex h-full items-center px-3 text-sm font-medium transition-colors',
		active ? 'text-white' : 'text-white/80 hover:bg-white/10 hover:text-white'
	]}
>
	{props.text}
	{#if active}
		<span class="absolute inset-x-0 bottom-0 h-[3px] bg-white"></span>
	{/if}
</a>
