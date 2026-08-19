<script lang="ts">
	import type { PageData } from './$types';
	import type { Component } from 'svelte';
	import type { CostCentreCount, OwnerCount } from '$lib/api/types';
	import { _ } from 'svelte-i18n';
	import { Stamp, BookText, CircleCheck, Banknote } from '@lucide/svelte';
	import { api } from '$lib/api';
	import CashSpinner from '$lib/components/CashSpinner.svelte';
	import PendingList from './PendingList.svelte';

	let { data }: { data: PageData } = $props();

	const perms = $derived(data.user?.permissions);

	const overviewPromise = api.users.actionOverview();

	const costCentreRows = (base: string, counts: CostCentreCount[]) =>
		counts.map((c) => ({
			label: c.cost_centre,
			href: `${base}?cost_centre=${encodeURIComponent(c.cost_centre)}`,
			count: c.count
		}));

	const ownerRows = (base: string, counts: OwnerCount[]) =>
		counts.map((o) => ({
			label: `${o.first_name} ${o.last_name}`.trim() || o.username,
			href: `${base}?user=${encodeURIComponent(o.username)}`,
			count: o.count
		}));
</script>

<!-- Prominent, linked section header for an action. -->
{#snippet header(title: string, Icon: Component, href: string)}
	<a
		{href}
		class="mb-4 flex w-fit items-center gap-2 text-base-text transition-colors hover:text-money-green-700 dark:text-dark-base-text dark:hover:text-money-green-400"
	>
		<Icon class="size-6 text-money-green-600 dark:text-money-green-500" />
		<h2 class="text-2xl font-semibold">{title}</h2>
	</a>
{/snippet}

{#if perms}
	<div class="grid max-w-5xl grid-cols-1 gap-8 lg:grid-cols-2">
		{#await overviewPromise}
			<div
				class="flex justify-center border border-base-500 p-6 lg:col-span-2 dark:border-dark-base-200"
			>
				<CashSpinner class="size-5 text-base-subtle dark:text-dark-base-subtle" />
			</div>
		{:then overview}
			{#if perms.attest.length > 0}
				<section>
					{@render header($_('tasks.attest'), Stamp, '/admin/attest')}
					<PendingList
						rows={costCentreRows('/admin/attest', overview.attest)}
						emptyText={$_('tasks.empty')}
					/>
				</section>
			{/if}

			{#if perms.accounting.length > 0}
				<section>
					{@render header($_('tasks.account'), BookText, '/admin/account')}
					<!-- Link to the expenses tab directly: /admin/account 307-redirects
					     and would drop the ?cost_centre filter. -->
					<PendingList
						rows={costCentreRows('/admin/account/expenses', overview.account)}
						emptyText={$_('tasks.empty')}
					/>
				</section>
			{/if}

			{#if perms.confirm}
				<section>
					{@render header($_('tasks.confirm'), CircleCheck, '/admin/confirm')}
					<PendingList
						rows={costCentreRows('/admin/confirm', overview.confirm)}
						emptyText={$_('tasks.empty')}
					/>
				</section>
			{/if}

			{#if perms.pay}
				<section>
					{@render header($_('tasks.pay'), Banknote, '/admin/pay')}
					<PendingList rows={ownerRows('/admin/pay', overview.pay)} emptyText={$_('tasks.empty')} />
				</section>
			{/if}
		{/await}
	</div>
{/if}
