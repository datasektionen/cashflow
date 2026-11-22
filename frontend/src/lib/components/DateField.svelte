<script lang="ts">
	import { DatePicker } from 'bits-ui';
	import { locale } from 'svelte-i18n';
	import type { DateValue } from '@internationalized/date';
	import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from '@lucide/svelte';
	import { cn } from 'tailwind-variants';
	import { Field, surface } from '#lib/components/ui/index.ts';
	import { inputShell } from './inputShell';
	import type { FormValidation } from '#lib/formValidation.svelte.ts';

	let {
		name,
		label,
		help,
		maxValue,
		form,
		value = $bindable()
	}: {
		name: string;
		label: string;
		help?: string;
		maxValue?: DateValue;
		form: FormValidation;
		value: DateValue | undefined;
	} = $props();

	// Validate once focus leaves the whole picker
	function handleFocusOut(e: FocusEvent) {
		const wrapper = e.currentTarget as HTMLElement;
		if (e.relatedTarget && wrapper.contains(e.relatedTarget as Node)) return;
		form.validate(name);
	}

	const navButton =
		'inline-flex size-8 cursor-pointer items-center justify-center text-muted-foreground transition-colors hover:bg-muted hover:text-foreground';
</script>

<Field {label} {help} error={form.errorFor(name)}>
	{#key $locale}
		<DatePicker.Root
			{maxValue}
			disableDaysOutsideMonth={false}
			bind:value
			locale={$locale?.startsWith('en') ? 'en-CA' : 'sv-SE'}
		>
			<div
				onfocusout={handleFocusOut}
				class={cn(inputShell, form.showErrors(name) && 'border-danger')}
			>
				<DatePicker.Input aria-label={label} class="flex flex-1 items-center px-2.5 tabular-nums">
					{#snippet children({ segments })}
						{#each segments as { part, value }}
							<DatePicker.Segment
								{part}
								class={[
									part === 'literal' ? 'px-px' : 'px-0.5',
									'outline-none focus:bg-accent focus:text-accent-foreground',
									part !== 'literal' && /\p{L}/u.test(value) && 'text-muted-foreground'
								]}
							>
								{value}
							</DatePicker.Segment>
						{/each}
					{/snippet}
				</DatePicker.Input>
				<DatePicker.Trigger
					tabindex={-1}
					aria-label={label}
					class="flex h-full cursor-pointer items-center px-2.5 text-muted-foreground hover:text-foreground"
				>
					<CalendarIcon class="size-4" />
				</DatePicker.Trigger>
			</div>
			<DatePicker.Content sideOffset={4} class={cn(surface, 'p-3')}>
				<DatePicker.Calendar>
					{#snippet children({ months, weekdays })}
						<DatePicker.Header class="mb-2 flex items-center justify-between">
							<DatePicker.PrevButton class={navButton}>
								<ChevronLeft class="size-4" />
							</DatePicker.PrevButton>
							<DatePicker.Heading class="text-sm font-medium" />
							<DatePicker.NextButton class={navButton}>
								<ChevronRight class="size-4" />
							</DatePicker.NextButton>
						</DatePicker.Header>
						{#each months as month}
							<DatePicker.Grid>
								<DatePicker.GridHead>
									<DatePicker.GridRow class="flex">
										{#each weekdays as day}
											<DatePicker.HeadCell class="w-8 text-xs font-normal text-muted-foreground">
												{day.slice(0, 2)}
											</DatePicker.HeadCell>
										{/each}
									</DatePicker.GridRow>
								</DatePicker.GridHead>
								<DatePicker.GridBody>
									{#each month.weeks as week}
										<DatePicker.GridRow class="flex">
											{#each week as date}
												<DatePicker.Cell {date} month={month.value}>
													<DatePicker.Day
														class="flex size-8 cursor-pointer items-center justify-center text-sm tabular-nums transition-colors hover:bg-muted data-disabled:cursor-not-allowed data-disabled:opacity-30 data-outside-month:text-muted-foreground data-outside-month:opacity-50 data-selected:bg-primary data-selected:text-primary-foreground data-today:font-semibold data-today:text-accent-foreground data-selected:data-today:text-primary-foreground"
													/>
												</DatePicker.Cell>
											{/each}
										</DatePicker.GridRow>
									{/each}
								</DatePicker.GridBody>
							</DatePicker.Grid>
						{/each}
					{/snippet}
				</DatePicker.Calendar>
			</DatePicker.Content>
		</DatePicker.Root>
	{/key}
</Field>
