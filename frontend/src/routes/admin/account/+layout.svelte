<script lang="ts">
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';

	let { children } = $props();

	const tabs = [
		{ href: '/admin/account/expenses', label: 'admin_account.tabs.expenses' },
		{ href: '/admin/account/invoices', label: 'admin_account.tabs.invoices' }
	];

	// Only show the tab bar on the list pages, not on a detail page.
	const showTabs = $derived(tabs.some((t) => page.url.pathname === t.href));
</script>

<div class="flex flex-col gap-4">
	{#if showTabs}
		<nav class="flex gap-1 border-b border-base-400 dark:border-dark-base-150">
			{#each tabs as tab}
				{@const active = page.url.pathname === tab.href}
				<a
					href={tab.href}
					class={[
						'-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors',
						active
							? 'border-money-green-600 text-base-text dark:border-money-green-400 dark:text-dark-base-text'
							: 'border-transparent text-base-subtle hover:text-base-text dark:text-dark-base-subtle dark:hover:text-dark-base-text'
					]}
				>
					{$_(tab.label)}
				</a>
			{/each}
		</nav>
	{/if}

	{@render children()}
</div>
