<!--
@component
Right-click context menu for a claim row in a PaginatedTable. Pass it as the
table's `contextSnippet`; the table positions it at the cursor, this component
owns its appearance.

Accepts an Expense, an Invoice or a Claim (the union used by the attest/confirm
lists), which all carry the fields the menu needs under different names.
-->
<script lang="ts">
	import type { Claim, Expense, Invoice, ExpensePart, InvoicePart, User } from '$lib/api/types';
	import { _ } from 'svelte-i18n';
	import { page } from '$app/state';
	import { Separator } from 'bits-ui';
	import { BookText, Copy, SquareArrowOutUpRight, User as UserIcon } from '@lucide/svelte';
	import { mayAccount } from '$lib/auth';

	interface Props {
		claim: Expense | Invoice | Claim;
		kind: 'expense' | 'invoice';
		user: User | null | undefined;
	}

	let { claim, kind, user }: Props = $props();

	const segment = $derived(kind === 'expense' ? 'expenses' : 'invoices');
	const detailHref = $derived(`/admin/${segment}/${claim.id}/`);

	const attested = $derived(
		'is_attested' in claim
			? claim.is_attested
			: (claim.parts as (ExpensePart | InvoicePart)[]).length > 0 &&
					(claim.parts as (ExpensePart | InvoicePart)[]).every((p) => p.attested_by != null)
	);
	const confirmed = $derived(
		'confirmed_at' in claim ? claim.confirmed_at != null : claim.is_confirmed
	);
	const paid = $derived(
		'payment' in claim
			? claim.payment != null
			: 'paid_at' in claim
				? claim.paid_at != null
				: claim.is_paid
	);

	const canAccount = $derived(
		claim.voucher == null && mayAccount(user) && attested && confirmed && paid
	);

	const itemClass =
		'flex w-full cursor-pointer flex-row items-center gap-x-2 px-3 py-2 text-left transition-colors hover:bg-base-300 focus-visible:bg-base-300 focus-visible:outline-none dark:hover:bg-dark-base-300 dark:focus-visible:bg-dark-base-300';
</script>

<div
	role="menu"
	aria-label={$_('claim_context_menu.label', { values: { id: claim.id } })}
	class={[
		'flex w-52 flex-col border border-base-500 bg-base-100 py-1 shadow-lg',
		'text-sm text-base-text dark:border-dark-base-300 dark:bg-dark-base-200 dark:text-dark-base-text'
	]}
>
	<a href={detailHref} role="menuitem" class={itemClass} target="_blank" rel="noopener noreferrer">
		<SquareArrowOutUpRight class="size-4 shrink-0" />
		{$_('claim_context_menu.open_new_tab')}
	</a>

	<a href={`/${claim.owner.username}/claims/`} role="menuitem" class={itemClass}>
		<UserIcon class="size-4 shrink-0" />
		<span class="truncate">{$_('claim_context_menu.view_owner')}</span>
	</a>

	<button
		type="button"
		role="menuitem"
		onclick={() => navigator.clipboard.writeText(new URL(detailHref, page.url).href)}
		class={itemClass}
	>
		<Copy class="size-4 shrink-0" />
		{$_('claim_context_menu.copy_link')}
	</button>

	<Separator.Root
		orientation="horizontal"
		class="my-1 h-px w-full bg-base-500 dark:bg-dark-base-300"
	/>

	<a
		href={canAccount ? `/admin/account/${segment}/${claim.id}/` : null}
		role="menuitem"
		aria-disabled={!canAccount}
		tabindex={canAccount ? undefined : -1}
		title={canAccount ? undefined : $_('claim_context_menu.account_blocked')}
		class={[
			itemClass,
			!canAccount && 'cursor-not-allowed opacity-50 hover:bg-transparent dark:hover:bg-transparent'
		]}
	>
		<BookText class="size-4 shrink-0" />
		{$_('claim_context_menu.account')}
	</a>
</div>
