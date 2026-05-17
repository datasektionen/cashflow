<script lang="ts">
	import { page } from '$app/state';

	let props: { to: string; text: string } = $props();
	const normalizePath = (path: string) => path.replace(/\/+$/, '') || '/';

	let active = $derived.by(() => {
		const target = normalizePath(props.to);
		const current = normalizePath(page.url.pathname);
		if (target === '/') return current === '/';
		return current === target || current.startsWith(target + '/');
	});
</script>

<a
	href={props.to}
	class={'relative flex h-full items-center p-2 text-xl transition-colors hover:bg-green-600 dark:hover:bg-dark-base-300' +
		(active ? ' hover:text-white dark:text-green-600' : '')}
	>{props.text}
	<span
		class={[
			'absolute right-0 bottom-0 left-0 h-1 bg-white transition-all dark:bg-green-600',
			active ? 'flex' : 'hidden'
		]}
	></span>
</a>
