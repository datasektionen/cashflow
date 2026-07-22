<script lang="ts">
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';

	let { children } = $props();

	const tabs = [
		{ href: '/admin/pay/expenses', label: 'admin_pay.tabs.expenses' },
		{ href: '/admin/pay/invoices', label: 'admin_pay.tabs.invoices' }
	];
</script>

<div class="flex flex-col gap-4">
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

	{@render children()}
</div>
