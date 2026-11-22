<script lang="ts">
	import { page } from '$app/state';

	let { tabs }: { tabs: { href: string; label: string }[] } = $props();
</script>

<nav class="flex items-center gap-1 border-b border-border">
	{#each tabs as tab (tab.href)}
		{@const active = page.url.pathname === tab.href}
		<a
			href={tab.href}
			aria-current={active ? 'page' : undefined}
			class={[
				'-mb-px border-b-3 px-3 py-2.5 text-sm font-semibold transition-colors',
				active
					? 'border-primary text-foreground'
					: 'border-transparent text-muted-foreground hover:text-foreground'
			]}
		>
			{tab.label}
		</a>
	{/each}
</nav>
