<script lang="ts">
	import { setContext } from 'svelte';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import {
		Banknote,
		BookCheck,
		BookText,
		CircleCheck,
		FileText,
		Files,
		HandCoins,
		PanelLeftClose,
		PanelLeftOpen,
		PiggyBank,
		Receipt,
		ReceiptText,
		Settings2,
		Stamp,
		Trophy,
		Wallet
	} from '@lucide/svelte';
	import { api } from '#lib/api/index.ts';
	import type { ActionSummary, User } from '#lib/api/types.ts';
	import { hasAdminAccess } from '#lib/auth.ts';
	import { isMediumLayout } from '#lib/stores/state.svelte.ts';
	import { Separator } from '#lib/components/ui/index.ts';
	import SideNavLink from '#lib/components/SideNavLink.svelte';

	let {
		user,
		open = $bindable(false),
		slim = $bindable(false)
	}: { user: User; open?: boolean; slim?: boolean } = $props();

	setContext('sidebar-slim', () => slim);

	const adminView = $derived(page.url.pathname.startsWith('/admin'));
	const canAccessAdmin = $derived(hasAdminAccess(user));
	const viewAll = $derived(user.permissions?.['view-all'] === true);
	const perms = $derived(user.permissions);

	let summary: ActionSummary | null = $state(null);
	$effect(() => {
		if (adminView || open) api.users.actionSummary().then((v) => (summary = v));
	});

	const count = (key: keyof ActionSummary['invoices']) =>
		summary ? summary.expenses[key] + summary.invoices[key] : undefined;
</script>

{#if open}
	<button
		type="button"
		aria-label={$_('close')}
		onclick={() => (open = false)}
		class="fixed inset-0 top-16 z-20 bg-black/40 lg:hidden"
	></button>
{/if}

<aside
	inert={isMediumLayout.current && !open}
	class={[
		'fixed top-16 left-0 z-30 flex h-[calc(100dvh-4rem)] w-60 flex-col gap-0.5 overflow-y-auto border-r border-border bg-card px-3 py-5 transition-[translate,width]',
		open ? 'translate-x-0' : '-translate-x-full',
		adminView ? 'lg:translate-x-0' : 'lg:hidden',
		slim && 'lg:w-16 lg:px-2'
	]}
>
	<div class="flex flex-col gap-0.5 lg:hidden">
		<SideNavLink to="/expenses/new" text={$_('new_expense.title')} icon={ReceiptText} />
		<SideNavLink to="/invoices/new" text={$_('new_invoice.title')} icon={FileText} />
		<SideNavLink to="/claims/" text={$_('user_claims')} icon={Wallet} />
		<SideNavLink to="/stats" text={$_('statistics')} icon={Trophy} />
		<SideNavLink to="/budget" text={$_('budget.title')} icon={PiggyBank} />
	</div>

	<div
		class={[
			'flex items-center justify-end pt-5 pb-1 lg:pt-0',
			slim && 'lg:justify-center',
			!canAccessAdmin && 'max-lg:hidden'
		]}
	>
		{#if canAccessAdmin}
			<p
				class={[
					'flex-1 px-2.5 text-[11px] font-semibold tracking-wide text-muted-foreground uppercase',
					slim && 'lg:sr-only'
				]}
			>
				{$_('admin')}
			</p>
		{/if}
		<button
			type="button"
			onclick={() => (slim = !slim)}
			aria-label={$_('compact_sidebar')}
			title={$_('compact_sidebar')}
			aria-pressed={slim}
			class="hidden size-9 shrink-0 cursor-pointer items-center justify-center text-muted-foreground transition-colors hover:bg-muted hover:text-foreground lg:inline-flex [&_svg]:size-4"
		>
			{#if slim}<PanelLeftOpen />{:else}<PanelLeftClose />{/if}
		</button>
	</div>

	{#if canAccessAdmin}
		<SideNavLink to="/admin/expenses" text={$_('admin_expenses.nav_title')} icon={Receipt} />
		<SideNavLink to="/admin/invoices" text={$_('admin_invoices.nav_title')} icon={Files} />
		<SideNavLink to="/admin/vouchers" text={$_('admin_vouchers.nav_title')} icon={BookCheck} />
		{#if viewAll || perms?.['view-all-payments']}
			<SideNavLink to="/admin/payments" text={$_('admin_payments.nav_title')} icon={HandCoins} />
		{/if}
	{/if}

	{#if perms && (viewAll || perms.confirm || perms.attest.length > 0 || perms.pay || perms.accounting.length > 0)}
		<Separator class="my-3" />
		{#if viewAll || perms.attest.length > 0}
			<SideNavLink
				to="/admin/attest"
				text={$_('tasks.attest')}
				icon={Stamp}
				badge={count('attestable')}
			/>
		{/if}
		{#if viewAll || perms.confirm}
			<SideNavLink
				to="/admin/confirm"
				text={$_('tasks.confirm')}
				icon={CircleCheck}
				badge={summary?.expenses.confirmable}
			/>
		{/if}
		{#if viewAll || perms.pay}
			<SideNavLink
				to="/admin/pay"
				text={$_('tasks.pay')}
				icon={Banknote}
				badge={count('payable')}
			/>
		{/if}
		{#if viewAll || perms.accounting.length > 0}
			<SideNavLink
				to="/admin/account"
				text={$_('tasks.account')}
				icon={BookText}
				badge={count('accountable')}
			/>
		{/if}
	{/if}

	{#if viewAll || perms?.['manage-fortnox']}
		<Separator class="my-3" />
		<SideNavLink to="/admin/fortnox" text={$_('fortnox.title')} icon={Settings2} />
	{/if}

	<div class="mt-auto flex shrink-0 pt-4">
		<a
			href="https://github.com/datasektionen/cashflow"
			target="_blank"
			rel="noreferrer"
			title="datasektionen/cashflow"
			class={[
				'flex min-w-0 flex-1 items-center gap-2.5 px-2.5 text-[11px] text-muted-foreground transition-colors hover:text-foreground',
				slim && 'lg:justify-center lg:px-0'
			]}
		>
			<svg class="size-4 shrink-0" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
				<path
					d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"
				/>
			</svg>
			<span class={['truncate font-mono', slim && 'lg:sr-only']}>datasektionen/cashflow</span>
		</a>
	</div>
</aside>
