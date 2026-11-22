<script lang="ts">
	import type { PageData } from './$types';
	import type { Component } from 'svelte';
	import type { CostCentreCount, OwnerCount } from '#lib/api/types.ts';
	import { _ } from 'svelte-i18n';
	import { ArrowRight, Stamp, BookText, CircleCheck, Banknote } from '@lucide/svelte';
	import { api } from '#lib/api/index.ts';
	import { Card, Skeleton } from '#lib/components/ui/index.ts';
	import PendingList from './PendingList.svelte';

	let { data }: { data: PageData } = $props();

	const perms = $derived(data.user?.permissions);

	const overviewPromise = api.users.actionOverview();

	type PendingRow = { label: string; href: string; count: number };

	const costCentreRows = (base: string, counts: CostCentreCount[]): PendingRow[] =>
		counts.map((c) => ({
			label: c.cost_centre,
			href: `${base}?cost_centre=${encodeURIComponent(c.cost_centre)}`,
			count: c.count
		}));

	const ownerRows = (base: string, counts: OwnerCount[]): PendingRow[] =>
		counts.map((o) => ({
			label: `${o.first_name} ${o.last_name}`.trim() || o.username,
			href: `${base}?user=${encodeURIComponent(o.username)}`,
			count: o.count
		}));
</script>

{#snippet task(title: string, Icon: Component, href: string, rows: Promise<PendingRow[]>)}
	<Card padded={false} class="overflow-hidden">
		<a
			{href}
			class="group flex items-center gap-3 border-b border-border px-5 py-4 transition-colors hover:bg-muted/50"
		>
			<span class="flex size-8 items-center justify-center bg-accent text-accent-foreground">
				<Icon class="size-4" />
			</span>
			<h2 class="flex-1 text-base font-semibold">{title}</h2>
			<ArrowRight
				class="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-foreground"
			/>
		</a>
		{#await rows}
			<ul class="divide-y divide-border">
				{#each { length: 4 }, i (i)}
					<li class="flex items-center justify-between gap-2 px-5 py-3">
						<Skeleton class="h-4 w-36" />
						<Skeleton class="h-4 w-6" />
					</li>
				{/each}
			</ul>
		{:then rows}
			<PendingList {rows} emptyText={$_('tasks.empty')} />
		{:catch}
			<p class="px-5 py-4 text-sm text-danger">{$_('action_failed')}</p>
		{/await}
	</Card>
{/snippet}

{#if perms}
	<div class="grid max-w-5xl grid-cols-1 gap-6 lg:grid-cols-2">
		{#if perms.attest.length > 0}
			{@render task(
				$_('tasks.attest'),
				Stamp,
				'/admin/attest',
				overviewPromise.then((o) => costCentreRows('/admin/attest', o.attest))
			)}
		{/if}
		{#if perms.accounting.length > 0}
			<!-- Rows skip the /admin/account redirect, which would drop ?cost_centre -->
			{@render task(
				$_('tasks.account'),
				BookText,
				'/admin/account',
				overviewPromise.then((o) => costCentreRows('/admin/account/expenses', o.account))
			)}
		{/if}
		{#if perms.confirm}
			{@render task(
				$_('tasks.confirm'),
				CircleCheck,
				'/admin/confirm',
				overviewPromise.then((o) => costCentreRows('/admin/confirm', o.confirm))
			)}
		{/if}
		{#if perms.pay}
			{@render task(
				$_('tasks.pay'),
				Banknote,
				'/admin/pay',
				overviewPromise.then((o) => ownerRows('/admin/pay', o.pay))
			)}
		{/if}
	</div>
{/if}
