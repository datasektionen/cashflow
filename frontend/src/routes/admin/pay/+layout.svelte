<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { LinkTabs } from '#lib/components/ui/index.ts';

	let { children } = $props();
</script>

<div class="flex flex-col gap-6 lg:min-h-0 lg:flex-1">
	<LinkTabs
		tabs={[
			{ href: '/admin/pay/expenses', label: $_('admin_pay.tabs.expenses') },
			{ href: '/admin/pay/invoices', label: $_('admin_pay.tabs.invoices') }
		]}
	/>
	{@render children()}
</div>
