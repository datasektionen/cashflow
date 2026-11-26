<script lang="ts">
	import { _ } from 'svelte-i18n';
	import {
		ArrowRight,
		Banknote,
		BookText,
		CircleCheck,
		FileText,
		ReceiptText,
		Stamp
	} from '@lucide/svelte';

	const steps = [
		{ key: 'registration', icon: ReceiptText },
		{ key: 'validation', icon: CircleCheck },
		{ key: 'attestation', icon: Stamp },
		{ key: 'payment', icon: Banknote },
		{ key: 'accounting', icon: BookText }
	];

	const actions = [
		{ href: '/expenses/new', label: 'new_expense.title', icon: ReceiptText, primary: true },
		{ href: '/invoices/new', label: 'new_invoice.title', icon: FileText, primary: false }
	];
</script>

<div class="mx-auto flex max-w-5xl flex-col gap-12 py-6 md:py-12">
	<header class="flex flex-col gap-3">
		<p class="text-sm font-semibold text-primary-text">
			{$_('welcome.intro')}
		</p>
		<h1 class="max-w-3xl text-3xl font-bold tracking-tight text-balance md:text-5xl">
			{$_('welcome.process.title')}
		</h1>
	</header>

	<ol class="grid gap-x-6 gap-y-8 md:grid-cols-5">
		{#each steps as step, i (step.key)}
			{@const Icon = step.icon}
			<li class="relative flex gap-4 md:flex-col">
				{#if i < steps.length - 1}
					<span
						aria-hidden="true"
						class="absolute top-12 bottom-[-2rem] left-5.5 w-0.5 bg-border md:top-5.5 md:right-[-1.5rem] md:bottom-auto md:left-12 md:h-0.5 md:w-auto"
					></span>
				{/if}
				<span
					class="relative flex size-11 shrink-0 items-center justify-center border-2 border-primary-text bg-background text-primary-text"
				>
					<Icon class="size-5" />
				</span>
				<div class="flex flex-col gap-1">
					<p class="text-sm font-bold">
						<span class="text-primary-text tabular-nums">{i + 1}</span>
						{$_(`welcome.process.${step.key}.title`)}
					</p>
					<p class="text-sm text-muted-foreground">
						{$_(`welcome.process.${step.key}.description`)}
					</p>
				</div>
			</li>
		{/each}
	</ol>

	<div class="grid gap-4 sm:grid-cols-2">
		{#each actions as action (action.href)}
			{@const Icon = action.icon}
			<a
				href={action.href}
				class={[
					'group flex items-center gap-4 border-2 p-5 transition-colors',
					action.primary
						? 'border-primary bg-primary text-primary-foreground hover:border-primary-hover hover:bg-primary-hover'
						: 'border-foreground bg-card hover:bg-muted'
				]}
			>
				<Icon class="size-6" />
				<span class="flex-1 text-lg font-bold">{$_(action.label)}</span>
				<ArrowRight class="size-5 transition-transform group-hover:translate-x-1" />
			</a>
		{/each}
	</div>
</div>
