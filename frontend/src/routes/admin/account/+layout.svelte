<script lang="ts">
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import { LinkTabs } from '#lib/components/ui/index.ts';

	let { children } = $props();

	const tabs = $derived([
		{ href: '/admin/account/expenses', label: $_('admin_account.tabs.expenses') },
		{ href: '/admin/account/invoices', label: $_('admin_account.tabs.invoices') }
	]);
</script>

<div class="flex flex-col gap-6">
	{#if tabs.some((t) => page.url.pathname === t.href)}
		<LinkTabs {tabs} />
	{/if}
	{@render children()}
</div>
