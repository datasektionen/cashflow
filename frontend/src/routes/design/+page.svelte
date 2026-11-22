<script lang="ts">
	import {
		Avatar,
		Badge,
		Button,
		Card,
		Checkbox,
		ConfirmDialog,
		CopyableValue,
		Dialog,
		DropdownMenu,
		EmptyState,
		Field,
		Input,
		PageHeader,
		Section,
		SegmentedControl,
		Select,
		Separator,
		Skeleton,
		Spinner,
		Switch,
		Table,
		LinkTabs,
		Textarea,
		Tooltip
	} from '#lib/components/ui/index.ts';
	import {
		Check,
		Download,
		Ellipsis,
		Flag,
		Inbox,
		Pencil,
		Plus,
		ReceiptText,
		Search,
		Trash2
	} from '@lucide/svelte';

	const variants = ['primary', 'secondary', 'ghost', 'danger', 'danger-outline'] as const;
	const badges = ['neutral', 'success', 'warning', 'danger', 'outline'] as const;

	let range = $state<'all' | 'year' | 'month'>('all');
	let costCentre = $state<string>();
	let checked = $state(true);
	let enabled = $state(false);
	let dialogOpen = $state(false);

	const rows = [
		{ id: 29, description: 'Pynt till Höstsittning', owner: 'Diana Datalog', amount: '2 359,15' },
		{ id: 28, description: 'Hyra av släpvagn', owner: 'Diana Datalog', amount: '4 765,14' },
		{ id: 27, description: 'Tryck av affischer', owner: 'Ture Teknolog', amount: '18 956,13' }
	];
</script>

<div class="flex flex-col gap-12">
	<Section title="Typography">
		<div class="flex flex-col gap-3">
			<p class="text-3xl font-semibold tracking-tight">18 758,83 kr</p>
			<p class="text-2xl font-semibold tracking-tight">Page title</p>
			<p class="text-base font-semibold">Section title</p>
			<p class="text-sm">Pizza till sektionsmöte</p>
			<p class="text-sm text-muted-foreground">Diana Datalog</p>
			<p class="font-mono text-sm">E742 #29 8327-1234567890</p>
		</div>
	</Section>

	<Section title="Colors">
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
			{#each ['bg-background', 'bg-card', 'bg-muted', 'bg-border', 'bg-input', 'bg-primary', 'bg-accent', 'bg-danger'] as swatch (swatch)}
				<div class="flex flex-col gap-1.5">
					<div class={['h-12 border border-border', swatch]}></div>
					<span class="font-mono text-xs text-muted-foreground">{swatch.slice(3)}</span>
				</div>
			{/each}
		</div>
	</Section>

	<Section title="Buttons">
		<div class="flex flex-col gap-4">
			{#each ['sm', 'md', 'lg'] as const as size (size)}
				<div class="flex flex-wrap items-center gap-3">
					{#each variants as variant (variant)}
						<Button {variant} {size}>{variant}</Button>
					{/each}
				</div>
			{/each}
			<div class="flex flex-wrap items-center gap-3">
				<Button><Plus />New expense</Button>
				<Button variant="secondary"><Download />Export</Button>
				<Button variant="secondary" size="icon" aria-label="Edit"><Pencil /></Button>
				<Button variant="ghost" size="icon-sm" aria-label="More"><Ellipsis /></Button>
				<Button disabled>Disabled</Button>
				<Button disabled><Spinner />Saving</Button>
				<Button href="/claims" variant="secondary">Link button</Button>
			</div>
		</div>
	</Section>

	<Section title="Badges">
		<div class="flex flex-wrap items-center gap-2">
			{#each badges as variant (variant)}
				<Badge {variant}>{variant}</Badge>
			{/each}
			<Badge variant="success"><Check />Attested</Badge>
			<Badge variant="warning"><Flag />Flagged</Badge>
			<Badge size="lg" variant="success">Attested</Badge>
		</div>
	</Section>

	<Section title="Form controls">
		<div class="grid gap-6 md:grid-cols-2">
			<Field label="Description" for="d-desc" help="A description of the purchase">
				<Input id="d-desc" placeholder="Pizza till sektionsmöte" />
			</Field>
			<Field label="Account number" for="d-acc" error="Account number is required">
				<Input id="d-acc" aria-invalid="true" />
			</Field>
			<Field label="Cost centre" for="d-cc">
				<Select
					id="d-cc"
					bind:value={costCentre}
					items={[
						{ value: 'ada', label: 'Ada' },
						{ value: 'centralt', label: 'Centralt' },
						{ value: 'dd', label: 'D-Dagen 2026' }
					]}
				/>
			</Field>
			<Field label="Search" for="d-search">
				<div class="relative">
					<Search
						class="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
					/>
					<Input id="d-search" type="search" class="pl-9" placeholder="Search by description" />
				</div>
			</Field>
			<Field label="Comment" for="d-comment" class="md:col-span-2">
				<Textarea id="d-comment" placeholder="Write a comment" />
			</Field>
			<div class="flex flex-wrap items-center gap-6">
				<Checkbox bind:checked>Not attested</Checkbox>
				<Checkbox indeterminate>Some selected</Checkbox>
				<Checkbox disabled>Disabled</Checkbox>
				<label class="flex items-center gap-2 text-sm">
					<Switch bind:checked={enabled} />Only exceeded budget lines
				</label>
			</div>
			<div class="flex flex-wrap items-center gap-3">
				<SegmentedControl
					bind:value={range}
					items={[
						{ value: 'all', label: 'All time' },
						{ value: 'year', label: 'Year' },
						{ value: 'month', label: 'Month' }
					]}
				/>
				<SegmentedControl
					size="sm"
					bind:value={range}
					items={[
						{ value: 'all', label: 'All time' },
						{ value: 'year', label: 'Year' },
						{ value: 'month', label: 'Month' }
					]}
				/>
			</div>
		</div>
	</Section>

	<Section title="Cards">
		<div class="grid gap-4 md:grid-cols-3">
			<Card>
				<p class="text-sm text-muted-foreground">Total cashflowed</p>
				<p class="mt-1 text-2xl font-semibold tabular-nums">18 758,83 kr</p>
			</Card>
			<Card title="Information">
				<dl class="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
					<dt class="text-muted-foreground">Purchased by</dt>
					<dd>Diana Datalog</dd>
					<dt class="text-muted-foreground">Purchase date</dt>
					<dd>2026-10-09</dd>
				</dl>
			</Card>
			<Card title="Comments">
				{#snippet actions()}
					<Button size="sm" variant="secondary"><Plus />Add</Button>
				{/snippet}
				<p class="text-sm text-muted-foreground">No comments yet.</p>
			</Card>
		</div>
	</Section>

	<Section title="Table">
		<Card padded={false}>
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head class="w-16">ID</Table.Head>
						<Table.Head>Description</Table.Head>
						<Table.Head>Owner</Table.Head>
						<Table.Head>Status</Table.Head>
						<Table.Head align="right">Total</Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each rows as row (row.id)}
						<Table.Row class="hover:bg-muted/50">
							<Table.Cell class="text-muted-foreground">#{row.id}</Table.Cell>
							<Table.Cell>{row.description}</Table.Cell>
							<Table.Cell>{row.owner}</Table.Cell>
							<Table.Cell><Badge variant="success">Attested</Badge></Table.Cell>
							<Table.Cell align="right">{row.amount} kr</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
		</Card>
	</Section>

	<Section title="Tabs">
		<LinkTabs
			tabs={[
				{ href: '/design', label: 'Expenses' },
				{ href: '/design/invoices', label: 'Invoices' }
			]}
		/>
	</Section>

	<Section title="Overlays">
		<div class="flex flex-wrap items-center gap-3">
			<Dialog bind:open={dialogOpen} title="Add comment">
				{#snippet trigger({ props })}
					<Button variant="secondary" {...props}>Open dialog</Button>
				{/snippet}
				<Textarea placeholder="Write a comment" />
				{#snippet footer()}
					<Button variant="secondary" onclick={() => (dialogOpen = false)}>Cancel</Button>
					<Button onclick={() => (dialogOpen = false)}>Submit</Button>
				{/snippet}
			</Dialog>

			<ConfirmDialog
				title="Delete expense?"
				confirmLabel="Delete"
				cancelLabel="Cancel"
				danger
				onConfirm={() => {}}
			>
				{#snippet trigger({ props })}
					<Button variant="danger-outline" {...props}><Trash2 />Delete</Button>
				{/snippet}
			</ConfirmDialog>

			<DropdownMenu.Root>
				<DropdownMenu.Trigger>
					{#snippet child({ props })}
						<Button variant="secondary" {...props}>Menu</Button>
					{/snippet}
				</DropdownMenu.Trigger>
				<DropdownMenu.Content>
					<DropdownMenu.Label>Expense #29</DropdownMenu.Label>
					<DropdownMenu.Item><Pencil />Edit</DropdownMenu.Item>
					<DropdownMenu.Item><Flag />Flag</DropdownMenu.Item>
					<DropdownMenu.Separator />
					<DropdownMenu.Item><Trash2 />Delete</DropdownMenu.Item>
				</DropdownMenu.Content>
			</DropdownMenu.Root>

			<Tooltip content="Inbox">
				{#snippet children({ props })}
					<Button variant="ghost" size="icon" aria-label="Info" {...props}><Inbox /></Button>
				{/snippet}
			</Tooltip>
		</div>
	</Section>

	<Section title="Misc">
		<div class="flex flex-col gap-6">
			<div class="flex flex-wrap items-center gap-3">
				<Avatar fallback="TT" />
				<Avatar fallback="DD" class="size-10" />
				<CopyableValue display="Expense #29" value={29} />
				<CopyableValue display="2 359,15" />
			</div>
			<Separator />
			<div class="flex flex-col gap-2">
				<Skeleton class="h-4 w-64" />
				<Skeleton class="h-4 w-48" />
			</div>
			<PageHeader title="Page header" />
			<EmptyState icon={ReceiptText} title="No expenses yet" />
		</div>
	</Section>
</div>
