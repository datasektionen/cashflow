<script lang="ts">
	import { claimColumns } from '#lib/components/TableCells.svelte';
	import type { PageProps } from './$types';
	import { _ } from 'svelte-i18n';
	import PaginatedTable from '#lib/components/PaginatedTable.svelte';
	import type { TableRowProps } from '#lib/components/types.ts';
	import type { Claim } from '#lib/api/types.ts';
	import ClaimFilterBar from '#lib/components/ClaimFilterBar.svelte';
	import { formatBankAccount } from '#lib/bankAccount.ts';
	import UserAvatar from '#lib/components/UserAvatar.svelte';
	import { CopyableValue } from '#lib/components/ui/index.ts';
	import { mayPay } from '#lib/auth.ts';
	import ClaimContextMenu from '#lib/components/ClaimContextMenu.svelte';

	let { data }: PageProps = $props();

	const rowProps: TableRowProps<Claim> = {
		href: (claim) => `/admin/${claim.type === 'invoice' ? 'invoices' : 'expenses'}/${claim.id}`
	};

	const columns = $derived(claimColumns($_));

	const formattedAccount = $derived(
		data.viewedUser.bank_info
			? formatBankAccount(
					data.viewedUser.bank_info.sorting_number,
					data.viewedUser.bank_info.bank_account
				)
			: null
	);
</script>

{#snippet contextSnippet(claim: Claim)}
	<ClaimContextMenu {claim} kind={claim.type} user={data.user} />
{/snippet}

<header class="flex flex-wrap items-center gap-x-6 gap-y-3 pb-6">
	<UserAvatar username={data.viewedUser.username} class="size-12" />
	<div class="mr-auto flex min-w-0 flex-col">
		<h1 class="text-3xl font-bold tracking-tight wrap-break-word">
			{data.viewedUser.first_name}
			{data.viewedUser.last_name}
		</h1>
		<p class="truncate text-sm text-muted-foreground">{data.viewedUser.email}</p>
	</div>
	{#if mayPay(data.user)}
		<div class="flex flex-col items-start gap-1.5 text-sm">
			<p class="text-xs text-muted-foreground">{data.viewedUser.bank_info.bank_name}</p>
			{#if formattedAccount != null}
				<CopyableValue value={formattedAccount} display={formattedAccount} class="font-mono" />
			{/if}
		</div>
	{/if}
</header>

<ClaimFilterBar
	includeChecks={false}
	exclude={['voucher_series', 'verification', 'invoice_number']}
/>
<PaginatedTable paginatedResponse={data.claims} {columns} {rowProps} {contextSnippet} />
