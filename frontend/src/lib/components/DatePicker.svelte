<script lang="ts">
	import { DatePicker } from 'bits-ui';
	import { locale } from 'svelte-i18n';
	import { type DateValue } from '@internationalized/date';
	import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from '@lucide/svelte';

	type DatePickerProps = {
		value: DateValue | undefined;
		maxValue?: DateValue;
		minValue?: DateValue;
		errors?: string[];
		invalid?: boolean;
		onBlur: (e: FocusEvent) => void;
	};

	let {
		value = $bindable<DateValue | undefined>(),
		maxValue = undefined,
		minValue = undefined,
		errors,
		invalid = false,
		onBlur
	}: DatePickerProps = $props();
</script>

<DatePicker.Root {maxValue} {minValue} disableDaysOutsideMonth={false} bind:value locale={$locale ?? 'sv'}>
	<div
		onfocusout={onBlur}
		class={[
			'flex h-[2.5em] w-full flex-row items-center bg-base-300 inset-shadow-sm dark:bg-dark-base-300',
			invalid && 'border-2 border-red-500'
		]}
	>
		<DatePicker.Input class="flex flex-1 px-2">
			{#snippet children({ segments })}
				{#each segments as { part, value }}
					<DatePicker.Segment
						{part}
						class="px-0.5 {part !== 'literal' && /\p{L}/u.test(value)
							? 'text-base-subtle dark:text-dark-base-subtle'
							: ''}"
					>
						{value}
					</DatePicker.Segment>
				{/each}
			{/snippet}
		</DatePicker.Input>
		<DatePicker.Trigger class="px-2 hover:cursor-pointer">
			<CalendarIcon class="size-4" />
		</DatePicker.Trigger>
	</div>
	<DatePicker.Content class="z-50 bg-base-200 p-2 shadow-lg dark:bg-dark-base-200">
		<DatePicker.Calendar>
			{#snippet children({ months, weekdays })}
				<DatePicker.Header class="mb-2 flex items-center justify-between">
					<DatePicker.PrevButton class="p-1 hover:cursor-pointer">
						<ChevronLeft class="size-4" />
					</DatePicker.PrevButton>
					<DatePicker.Heading class="text-sm font-medium" />
					<DatePicker.NextButton class="p-1 hover:cursor-pointer">
						<ChevronRight class="size-4" />
					</DatePicker.NextButton>
				</DatePicker.Header>
				{#each months as month}
					<DatePicker.Grid>
						<DatePicker.GridHead>
							<DatePicker.GridRow class="flex">
								{#each weekdays as day}
									<DatePicker.HeadCell
										class="w-8 text-xs text-base-subtle dark:text-dark-base-subtle"
									>
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
												class="flex h-8 w-8 items-center justify-center text-sm hover:cursor-pointer hover:bg-base-100 data-disabled:cursor-not-allowed data-disabled:opacity-30 data-outside-month:text-base-subtle data-outside-month:opacity-40 data-selected:bg-money-green-600 data-selected:text-base-100 dark:hover:bg-dark-base-100"
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
