<!--
@component
Right-click menu for a claim row, passed as a PaginatedTable's `contextSnippet`.
-->
<script lang="ts">
	import {
		claimProgress,
		type Claim,
		type Expense,
		type Invoice,
		type User
	} from '#lib/api/types.ts';
	import { _ } from 'svelte-i18n';
	import { page } from '$app/state';
	import { cn } from 'tailwind-variants';
	import { Separator, menuItem, surface } from '#lib/components/ui/index.ts';
	import { BookText, Copy, SquareArrowOutUpRight, User as UserIcon } from '@lucide/svelte';
	import { mayAccount } from '#lib/auth.ts';

	interface Props {
		claim: Expense | Invoice | Claim;
		kind: 'expense' | 'invoice';
		user: User | null | undefined;
	}

	let { claim, kind, user }: Props = $props();

	const segment = $derived(kind === 'expense' ? 'expenses' : 'invoices');
	const detailHref = $derived(`/admin/${segment}/${claim.id}/`);

	const { attested, confirmed, paid } = $derived(claimProgress(claim));
	const canAccount = $derived(
		claim.voucher == null && mayAccount(user) && attested && confirmed && paid
	);

	const itemClass = cn(menuItem, 'w-full text-left hover:bg-muted focus-visible:bg-muted');
</script>

<div
	role="menu"
	aria-label={$_('claim_context_menu.label', { values: { id: claim.id } })}
	class={cn(surface, 'flex w-56 flex-col')}
>
	<a href={detailHref} role="menuitem" class={itemClass} target="_blank" rel="noopener noreferrer">
		<SquareArrowOutUpRight />
		{$_('claim_context_menu.open_new_tab')}
	</a>

	<a href={`/admin/users/${claim.owner.username}/`} role="menuitem" class={itemClass}>
		<UserIcon />
		<span class="truncate">{$_('claim_context_menu.view_owner')}</span>
	</a>

	<button
		type="button"
		role="menuitem"
		onclick={() => navigator.clipboard.writeText(new URL(detailHref, page.url.href).href)}
		class={itemClass}
	>
		<Copy />
		{$_('claim_context_menu.copy_link')}
	</button>

	<Separator class="-mx-1 my-1 w-auto" />

	<a
		href={canAccount ? `/admin/account/${segment}/${claim.id}/` : null}
		role="menuitem"
		aria-disabled={!canAccount}
		tabindex={canAccount ? undefined : -1}
		title={canAccount ? undefined : $_('claim_context_menu.account_blocked')}
		class={[itemClass, !canAccount && 'cursor-not-allowed opacity-50 hover:bg-transparent']}
	>
		<BookText />
		{$_('claim_context_menu.account')}
	</a>
</div>
