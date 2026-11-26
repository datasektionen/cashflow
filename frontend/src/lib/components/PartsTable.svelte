<script lang="ts">
	import { Check, TriangleAlert, X } from '@lucide/svelte';
	import type { ClaimPart, Profile, User } from '#lib/api/types.ts';
	import { _ } from 'svelte-i18n';
	import { api } from '#lib/api/index.ts';
	import { failed, success } from '#lib/stores/alerts.ts';
	import { SvelteMap, SvelteSet } from 'svelte/reactivity';
	import { Button, Spinner, Table } from '#lib/components/ui/index.ts';
	import { formatDineroAmount, sumDinero } from '#lib/money.ts';
	import type { Dinero } from 'dinero.js';

	type ClaimPartsTableProps = {
		parts: ClaimPart[];
		owner: Profile;
		currentUser?: User;
		includeAttest?: boolean;
		attestDisabled?: boolean;
		partType?: 'expense' | 'invoice';
		/** Called after a part is attested or unattested */
		onchange?: () => void;
	};

	const {
		parts,
		owner,
		currentUser,
		includeAttest = false,
		attestDisabled = false,
		partType = 'expense',
		onchange
	}: ClaimPartsTableProps = $props();

	const lineKey = (cc: string, scc: string, bl: string) => `${cc}/${scc}/${bl}`;

	// Exceeded budget lines in the parts' cost centres
	const blownLines = $derived.by(() => {
		const names = new Set(parts.map((p) => p.cost_centre));
		return api.budget
			.listCostCentres(1, 100, { active: true, contains_blown: true })
			.then((res) =>
				Promise.all(
					res.data.flatMap((cc) =>
						cc.id != null && names.has(cc.name) ? [api.budget.retrieveCostCentre(cc.id)] : []
					)
				)
			)
			.then(
				(ccs) =>
					new Set(
						ccs.flatMap((cc) =>
							(cc.secondary_cost_centres ?? []).flatMap((scc) =>
								(scc.budget_lines ?? [])
									.filter((bl) => bl.blown)
									.map((bl) => lineKey(cc.name, scc.name, bl.name))
							)
						)
					)
			);
	});

	const pending = new SvelteSet<number>();
	// Attested state set here, until the parts reload
	const override = new SvelteMap<number, boolean>();

	async function setAttested(part: ClaimPart, attest: boolean) {
		pending.add(part.id);
		const claims = api[`${partType}s`];
		try {
			await (attest ? claims.attestPart(part.id) : claims.unattestPart(part.id));
			override.set(part.id, attest);
			success($_(`alerts.${partType}_part_${attest ? 'attested' : 'unattested'}`));
			onchange?.();
		} catch (err) {
			failed(err, $_('action_failed'));
		} finally {
			pending.delete(part.id);
		}
	}

	// Expense owners may not attest their own parts
	const mayAttest = (part: ClaimPart) =>
		!!currentUser &&
		currentUser.permissions.attest.includes(part.cost_centre) &&
		(partType === 'invoice' || owner.username !== currentUser.username);

	const totalAmount = $derived(sumDinero(parts.map((part) => part.amount)));
</script>

{#snippet amount(value: Dinero<number, 'SEK'>)}
	{formatDineroAmount(value)}
	<span class="text-xs text-muted-foreground">SEK</span>
{/snippet}

{#snippet attestControls(part: ClaimPart)}
	{#if pending.has(part.id)}
		<Spinner />
	{:else if override.get(part.id) ?? !!part.attested_by}
		{@const attestedBy = override.get(part.id) ? (currentUser ?? null) : part.attested_by}
		<div class="flex items-center justify-end gap-1.5">
			<Check class="size-4 shrink-0 text-primary-text" />
			{#if attestedBy}
				<span class="truncate text-xs text-muted-foreground">
					{attestedBy.first_name}
					{attestedBy.last_name}
				</span>
			{/if}
			{#if mayAttest(part)}
				<Button
					variant="ghost"
					size="icon-sm"
					onclick={() => setAttested(part, false)}
					title={$_('tasks.unattest')}
					aria-label={$_('tasks.unattest')}
					class="size-6 text-muted-foreground"
				>
					<X class="size-3.5!" />
				</Button>
			{/if}
		</div>
	{:else if mayAttest(part)}
		<Button
			size="sm"
			onclick={() => setAttested(part, true)}
			disabled={attestDisabled}
			title={attestDisabled ? $_('attest_disabled_flagged') : undefined}
		>
			{$_('tasks.attest')}
		</Button>
	{/if}
{/snippet}

{#snippet blown(part: ClaimPart)}
	{#await blownLines then lines}
		{#if lines.has(lineKey(part.cost_centre, part.secondary_cost_centre, part.budget_line))}
			<span title={$_('budget.exceeded')} class="shrink-0 text-danger-text">
				<TriangleAlert class="size-3.5" aria-label={$_('budget.exceeded')} />
			</span>
		{/if}
	{/await}
{/snippet}

<div class="@container">
	<ul class="divide-y divide-border @xl:hidden">
		{#each parts as part}
			<li class="flex flex-col gap-2 px-4 py-3">
				<div class="flex items-start justify-between gap-3">
					<a href="/budget/#{part.cost_centre}" class="min-w-0 text-sm">
						<span class="font-medium">{part.cost_centre}</span>
						<span class="block text-xs text-muted-foreground">
							{part.secondary_cost_centre} › {part.budget_line}
						</span>
					</a>
					<span class="flex shrink-0 items-center gap-2 text-sm whitespace-nowrap tabular-nums">
						{@render blown(part)}
						{@render amount(part.amount)}
					</span>
				</div>
				{#if includeAttest}
					<div class="flex justify-end">{@render attestControls(part)}</div>
				{/if}
			</li>
		{/each}
		<li class="flex justify-between px-4 py-3 text-sm font-semibold tabular-nums">
			<span>{$_('total')}</span>
			<span>{@render amount(totalAmount)}</span>
		</li>
	</ul>

	<div class="hidden @xl:block">
		<Table.Root class="min-w-136 [&_th]:whitespace-normal">
			<Table.Header>
				<Table.Row>
					<Table.Head>{$_('cost_centre')}</Table.Head>
					<Table.Head>{$_('secondary_cost_centre')}</Table.Head>
					<Table.Head>{$_('budget_line')}</Table.Head>
					<Table.Head align="right" class="w-px">{$_('amount')}</Table.Head>
					{#if includeAttest}<Table.Head class="w-px" />{/if}
				</Table.Row>
			</Table.Header>
			<Table.Body>
				{#each parts as part}
					<Table.Row>
						{#each [part.cost_centre, part.secondary_cost_centre] as name, i (i)}
							<Table.Cell>
								<a
									href="/budget/#{part.cost_centre}"
									class="wrap-break-word underline-offset-4 hover:underline"
								>
									{name}
								</a>
							</Table.Cell>
						{/each}
						<Table.Cell>
							<span class="flex items-center gap-2">
								<a
									href="/budget/#{part.cost_centre}"
									class="min-w-0 wrap-break-word underline-offset-4 hover:underline"
								>
									{part.budget_line}
								</a>
								{@render blown(part)}
							</span>
						</Table.Cell>
						<Table.Cell align="right">{@render amount(part.amount)}</Table.Cell>
						{#if includeAttest}
							<Table.Cell align="right">
								{@render attestControls(part)}
							</Table.Cell>
						{/if}
					</Table.Row>
				{/each}
			</Table.Body>
			<Table.Footer>
				<Table.Row>
					<Table.Cell colspan={3} align="right">{$_('total')}</Table.Cell>
					<Table.Cell align="right">{@render amount(totalAmount)}</Table.Cell>
					{#if includeAttest}<Table.Cell />{/if}
				</Table.Row>
			</Table.Footer>
		</Table.Root>
	</div>
</div>
