<script lang="ts">
	import { Menu, X, LogOut, Wallet } from '@lucide/svelte';
	import NavLink from './NavLink.svelte';
	import ThemeToggle from '#lib/components/ThemeToggle.svelte';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import { getProfilePicture, clearProfilePicture } from '#lib/stores/state.svelte.ts';
	import LanguageToggle from './LanguageToggle.svelte';
	import MoneyRain, { throwBill } from '#lib/components/MoneyRain.svelte';
	import UserAvatar from '#lib/components/UserAvatar.svelte';
	import { Button, DropdownMenu } from '#lib/components/ui/index.ts';
	import type { Profile } from '#lib/api/types.ts';

	let {
		user,
		canAccessAdmin = false,
		sidebarOpen = $bindable(false)
	}: {
		user: Profile | null;
		canAccessAdmin?: boolean;
		sidebarOpen?: boolean;
	} = $props();

	let userDropdownOpen = $state(false);

	const adminView = $derived(page.url.pathname.startsWith('/admin'));

	let logoutForm: HTMLFormElement | undefined = $state();

	const onBar = 'text-white/80 hover:bg-white/10 hover:text-white';

	// Close menus on navigation
	$effect(() => {
		page.url.pathname;
		sidebarOpen = false;
		userDropdownOpen = false;
	});
</script>

<MoneyRain />

<nav
	class="fixed inset-x-0 top-0 z-40 h-16 bg-brand pr-(--scrollbar-width) text-white shadow-md [&_:focus-visible]:outline-white"
>
	<div
		class={[
			'flex h-full w-full items-center justify-between gap-4',
			adminView ? 'px-4 lg:px-6' : 'mx-auto max-w-7xl px-4 lg:px-8'
		]}
	>
		<div class="flex h-full min-w-0 items-center gap-2">
			{#if user != null}
				<Button
					variant="ghost"
					size="icon"
					onclick={() => {
						sidebarOpen = !sidebarOpen;
						userDropdownOpen = false;
					}}
					aria-label={$_('toggle_sidebar')}
					aria-expanded={sidebarOpen}
					class="-ml-2 text-white hover:bg-white/10 lg:hidden"
				>
					{#if sidebarOpen}
						<X class="size-5!" />
					{:else}
						<Menu class="size-5!" />
					{/if}
				</Button>
			{/if}
			<a
				href="/"
				class="mr-4 flex shrink-0 items-center gap-2"
				aria-label={$_('chapter')}
				onclick={(e) =>
					(e.target as HTMLElement).tagName === 'IMG' && throwBill(e.target as Element)}
			>
				<img src="/icon.png" alt="" class="size-7" />
				<span class="font-display text-xl font-bold tracking-tight">Cashflow</span>
			</a>
			{#if user != null}
				<div class="hidden h-full lg:flex">
					<NavLink to="/expenses/new" text={$_('new_expense.title')} />
					<NavLink to="/invoices/new" text={$_('new_invoice.title')} />
					<NavLink to="/claims/" text={$_('user_claims')} />
					<NavLink to="/budget" text={$_('budget.title')} />
					<NavLink to="/stats" text={$_('statistics')} />
					{#if canAccessAdmin}
						<NavLink to="/admin/" text={$_('admin')} />
					{/if}
				</div>
			{/if}
		</div>

		<div class="flex shrink-0 items-center gap-1">
			<LanguageToggle class="mr-1" />
			<ThemeToggle class={onBar} />

			{#if user != null}
				<DropdownMenu.Root
					bind:open={userDropdownOpen}
					onOpenChange={(open) => {
						if (open) sidebarOpen = false;
					}}
				>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<button
								{...props}
								aria-label={`${user.first_name} ${user.last_name}`}
								class="ml-1 flex h-9 cursor-pointer items-center gap-2 px-0.5 text-sm font-medium transition-colors hover:bg-white/10 md:pl-3"
							>
								<span class="hidden md:inline">{user.first_name} {user.last_name}</span>
								{#await getProfilePicture(user.username)}
									<UserAvatar placeholder class="bg-white/20" />
								{:then profilePicture}
									<UserAvatar url={profilePicture ?? undefined} class="bg-white" />
								{/await}
							</button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content>
						<DropdownMenu.Label>{user.first_name} {user.last_name}</DropdownMenu.Label>
						<DropdownMenu.Separator />
						<DropdownMenu.Item>
							{#snippet child({ props })}
								<a href="/claims/" {...props}><Wallet />{$_('user_claims')}</a>
							{/snippet}
						</DropdownMenu.Item>
						<DropdownMenu.Item onSelect={() => logoutForm?.requestSubmit()}>
							<LogOut />{$_('logout')}
						</DropdownMenu.Item>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
				<form
					bind:this={logoutForm}
					method="POST"
					action="/logout"
					onsubmit={() => clearProfilePicture()}
					class="hidden"
				></form>
			{:else}
				<Button
					variant="secondary"
					size="sm"
					href="/oidc/authenticate/?next={encodeURIComponent(page.url.origin + '/')}"
					class="ml-1 border-transparent"
				>
					{$_('login')}
				</Button>
			{/if}
		</div>
	</div>
</nav>
