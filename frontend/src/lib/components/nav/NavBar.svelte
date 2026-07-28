<script lang="ts">
	import { Menu, X, LogOut } from '@lucide/svelte';
	import { Separator } from 'bits-ui';
	import NavLink from './NavLink.svelte';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';
	import { page } from '$app/state';
	import { _ } from 'svelte-i18n';
	import { getProfilePicture, clearProfilePicture } from '$lib/stores/state.svelte';
	import UserAvatar from '$lib/components/UserAvatar.svelte';
	import type { Profile } from '$lib/api/types';

	let {
		user,
		canAccessAdmin = false,
		sidebarOpen = $bindable(false)
	}: {
		user: Profile | null;
		canAccessAdmin?: boolean;
		sidebarOpen?: boolean;
	} = $props();

	let showUserDropdown = $state(false);
	const adminView = $derived(page.url.pathname.startsWith('/admin'));

	$effect(() => {
		page.url.pathname;
		showUserDropdown = false;
	});
</script>

<svelte:window
	onkeydown={(e) => {
		if (e.key === 'Escape') showUserDropdown = false;
	}}
/>

<nav
	class="fixed z-40 h-16 w-full bg-money-green-600 text-white drop-shadow-xl dark:bg-dark-base-200 dark:text-dark-base-text"
>
	<div
		class={[
			'flex h-full w-full flex-row justify-between',
			adminView ? 'px-4 pr-8 lg:px-8 lg:pr-12' : 'mx-auto max-w-7xl px-4 lg:px-8'
		]}
	>
		<div class="flex h-full">
			{#if user != null}
				<button
					type="button"
					onclick={() => (sidebarOpen = !sidebarOpen)}
					aria-label="Toggle sidebar"
					aria-expanded={sidebarOpen}
					class="my-auto mr-2 cursor-pointer rounded-full p-2 transition-colors hover:bg-white/10 lg:hidden dark:hover:bg-dark-base-300"
				>
					{#if sidebarOpen}
						<X class="size-5" />
					{:else}
						<Menu class="size-5" />
					{/if}
				</button>
				<div class="hidden h-full lg:flex">
					<NavLink to="/expenses/new" text={$_('new_expense.title')}></NavLink>
					<NavLink to="/invoices/new" text={$_('new_invoice.title')}></NavLink>
					<NavLink to="/{user.username}/claims/" text={$_('user_claims')}></NavLink>
					{#if canAccessAdmin}
						<NavLink to="/admin/" text={$_('admin')}></NavLink>
					{/if}
				</div>
			{/if}
		</div>

		<div class="flex h-full items-center space-x-2">
			<ThemeToggle />

			{#if user != null}
				<button
					type="button"
					onclick={() => (showUserDropdown = !showUserDropdown)}
					aria-haspopup="menu"
					aria-expanded={showUserDropdown}
					aria-controls="user-menu"
					aria-label={`${user.first_name} ${user.last_name}`}
					class="flex cursor-pointer items-center gap-2 p-1 transition-colors"
				>
					<span class="hidden md:inline">{user.first_name} {user.last_name}</span>
					{#await getProfilePicture(user.username)}
						<UserAvatar class="bg-white dark:bg-dark-base-50" placeholder />
					{:then profilePicture}
						<UserAvatar class="bg-white dark:bg-dark-base-50" url={profilePicture ?? undefined} />
					{/await}
				</button>
			{:else}
				<a href="/oidc/authenticate/?next={encodeURIComponent(page.url.origin + '/')}"
					>{$_('login')}</a
				>
			{/if}
		</div>
	</div>
</nav>

{#if user != null}
	{#if showUserDropdown}
		<button
			type="button"
			aria-label="Close menu"
			onclick={() => (showUserDropdown = false)}
			class="fixed inset-0 top-16 z-20"
		></button>
	{/if}

	<!-- Full-width aligner: reuses the nav's inner container classes so the menu's
	     right edge tracks the avatar in both the centred (non-admin) and
	     full-width (admin) layouts. Non-interactive except for the panel itself. -->
	<div
		class={[
			'pointer-events-none fixed inset-x-0 top-16 z-30 flex justify-end',
			adminView ? 'px-4 pr-8 lg:px-8 lg:pr-12' : 'mx-auto max-w-7xl px-4 lg:px-8'
		]}
	>
		<div
			id="user-menu"
			role="menu"
			inert={!showUserDropdown}
			class={[
				'pointer-events-auto flex w-48 flex-col border-r border-b border-l border-base-500 bg-base-100 py-1 text-sm transition-all dark:border-dark-base-300 dark:bg-dark-base-200',
				showUserDropdown ? 'translate-y-0 shadow-lg' : '-translate-y-full'
			]}
		>
			<p class="px-3 py-2 md:hidden dark:text-dark-base-text">
				{user.first_name}
				{user.last_name}
			</p>
			<Separator.Root
				orientation="horizontal"
				class="my-1 h-px w-full bg-base-500 md:hidden dark:bg-dark-base-300"
			/>
			<form method="POST" action="/logout" onsubmit={() => clearProfilePicture()}>
				<button
					type="submit"
					role="menuitem"
					class="flex w-full cursor-pointer flex-row items-center gap-x-1 px-3 py-2 text-left text-base-subtle transition-colors hover:bg-base-300 dark:text-dark-base-subtle dark:hover:bg-dark-base-300"
				>
					<LogOut class="size-4" />
					{$_('logout')}
				</button>
			</form>
		</div>
	</div>
{/if}
