<script lang="ts">
    import FileInput from './FileInput.svelte';
    import {_, locale} from 'svelte-i18n';
    import {BanknoteArrowUp, Calendar as CalendarIcon, ChevronLeft, ChevronRight, CircleQuestionMark, Plus, X} from '@lucide/svelte';
    import ComboBox from '$lib/components/ComboBox.svelte';
    import {DatePicker} from "bits-ui";
    import {today, getLocalTimeZone, type DateValue} from "@internationalized/date";
    import CashSpinner from "$lib/CashSpinner.svelte";


    const costCenters = [
        'Sektionslokalsgruppen',
        'Mottagningen',
        'D-rektoratet',
        'Studienämnden',
        'Näringslivsnämnden',
        'Internationella nämnden',
        'Idrottsnämnden',
        'Jämlikhetsnämnden',
        'DKM',
        'METAspexet',
        'Fanborgen',
        'Sånggruppen',
        'METAdorerna',
        'Valberedningen',
        'Revisorerna'
    ];

    const budgetLines = ['Lokalskostnader', 'Mat och dryck', 'Transport', 'Trycksaker', 'Övrigt'];

    const fmt = new Intl.NumberFormat('sv-SE', {minimumFractionDigits: 2, maximumFractionDigits: 2});

    type Part = { raw: number | null; display: string };
    let submitting: Boolean = $state(false);
    let parts: Part[] = $state([{raw: null, display: ''}]);
    let expenseDate: DateValue | undefined = $state();

    function onAmountFocus(i: number) {
        parts[i].display = parts[i].raw?.toString() ?? '';
    }

    function onAmountBlur(i: number, value: string) {
        const num = parseFloat(value.replace(/\s/g, '').replace(',', '.'));
        if (!isNaN(num) && num >= 0) {
            parts[i].raw = num;
            parts[i].display = fmt.format(num);
        } else {
            parts[i].raw = null;
            parts[i].display = '';
        }
    }
</script>

<form
        method="POST"
        enctype="multipart/form-data"
        class="flex flex-col space-y-4"
>

    <div class="flex flex-col lg:flex-row justify-between lg:max-h-128 space-y-6 lg:space-x-6">

        <fieldset class="flex flex-col space-y-6 border-0 p-0">
            <div class="flex flex-col space-y-2">
                <label for="description" class="text-s font-medium mb-1">
                    {$_('new_expense.form.description.label')}
                </label>
                <input
                        class="h-[2.5em] border-0 bg-base-300 inset-shadow-sm dark:bg-dark-base-300"
                        id="description"
                        type="text"
                        name="description"
                />
                <span class="text-sm text-base-subtle dark:text-dark-base-subtle">
                    {$_('new_expense.form.description.help')}
                </span>
            </div>
            <div class="flex flex-col space-y-2">
                <label for="date" class="text-s font-medium mb-1">
                    {$_('new_expense.form.date.label')}
                </label>

                <input type="hidden" name="expense-date" value={expenseDate?.toString() ?? ''} />
                <DatePicker.Root bind:value={expenseDate} maxValue={today(getLocalTimeZone())} locale={$locale ?? 'sv'}>
                    <div class="flex flex-row items-center w-full h-[2.5em] bg-base-300 dark:bg-dark-base-300 inset-shadow-sm">
                        <DatePicker.Input class="flex flex-1 px-2">
                            {#snippet children({segments})}
                                {#each segments as {part, value}}
                                    <DatePicker.Segment
                                        {part}
                                        class="px-0.5 {part !== 'literal' && /\p{L}/u.test(value) ? 'text-base-subtle dark:text-dark-base-subtle' : ''}"
                                    >
                                        {value}
                                    </DatePicker.Segment>
                                {/each}
                            {/snippet}
                        </DatePicker.Input>
                        <DatePicker.Trigger class="px-2 hover:cursor-pointer">
                            <CalendarIcon class="size-4"/>
                        </DatePicker.Trigger>
                    </div>
                    <DatePicker.Content class="z-50 bg-base-200 dark:bg-dark-base-200 p-2 shadow-lg">
                        <DatePicker.Calendar>
                            {#snippet children({months, weekdays})}
                                <DatePicker.Header class="flex items-center justify-between mb-2">
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
                                                    <DatePicker.HeadCell class="w-8 text-xs text-base-subtle dark:text-dark-base-subtle">
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
                                                            <DatePicker.Day class="w-8 h-8 flex items-center justify-center text-sm hover:bg-base-100 dark:hover:bg-dark-base-100 hover:cursor-pointer data-selected:bg-money-green-600 data-selected:text-base-100 data-outside-month:text-base-subtle data-outside-month:opacity-40 data-disabled:opacity-30 data-disabled:cursor-not-allowed" />
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
                <span class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('new_expense.form.date.help')}
		</span>
            </div>
        </fieldset>


        <fieldset class="flex flex-col w-full space-y-6 p-0 lg:h-80">
            <span class="texts font-medium mb-1">
                {$_('new_expense.form.receipts.label')}
            </span>
            <FileInput/>
        </fieldset>

    </div>


    <fieldset class="flex flex-col space-y-2 border-0 p-0">
        <legend class="text-s font-medium mb-1 flex flex-row items-center">
            {$_('new_expense.form.expense_parts.label')}
            <a href="/help/expense-parts"
               class="text-money-green-800 dark:text-money-green-600 group"
            >
                <CircleQuestionMark class="size-4 mx-2 group-hover:scale-125 transition-all"/>
            </a>
        </legend>

        <span class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('new_expense.form.expense_parts.help')}
		</span>

        <!--   Expense parts     -->
        <div class="flex flex-col">
            {#each parts as part, i}
                <div class="flex bg-base-300 p-4 dark:bg-dark-base-300 md:justify-between">
                    <div class="flex flex-wrap lg:flex-row w-full justify-between border-b border-base-500 dark:border-dark-base-200">
                        <div class="flex flex-col space-y-1">
                            {#if i === 0}<span
                                    class="text-sm font-medium mb-1">{$_('new_expense.form.expense_parts.cost_center_label')}</span>{/if}
                            <ComboBox
                                    name="part-{i}-costcenter"
                                    placeholder={$_('new_expense.form.expense_parts.cost_center_placeholder')}
                                    items={costCenters}
                            />
                        </div>
                        <div class="flex flex-col space-y-1">
                            {#if i === 0}<span
                                    class="text-sm font-medium mb-1">{$_('new_expense.form.expense_parts.secondary_cost_center_label')}</span>{/if}
                            <ComboBox
                                    name="part-{i}-secondarycostcenter"
                                    placeholder={$_('new_expense.form.expense_parts.secondary_cost_center_placeholder')}
                                    items={costCenters}
                            />
                        </div>
                        <div class="flex flex-col space-y-1">
                            {#if i === 0}<span
                                    class="text-sm font-medium mb-1">{$_('new_expense.form.expense_parts.budget_line_label')}</span>{/if}
                            <ComboBox
                                    name="part-{i}-budgetline"
                                    placeholder={$_('new_expense.form.expense_parts.budget_line_placeholder')}
                                    items={budgetLines}
                            />
                        </div>
                        <div class="flex flex-col space-y-1">
                            {#if i === 0}<span
                                    class="text-sm font-medium mb-1 text-right">{$_('new_expense.form.expense_parts.amount_label')}</span>{/if}
                            <div class="relative flex items-center">
                                <input type="hidden" name="part-{i}-amount" value={part.raw ?? ''}/>
                                <input
                                        type="text"
                                        id="part-{i}-amount"
                                        bind:value={part.display}
                                        onfocus={() => onAmountFocus(i)}
                                        onblur={(e) => onAmountBlur(i, (e.currentTarget as HTMLInputElement).value)}
                                        placeholder="0,00"
                                        class="border-0 bg-base-300 dark:bg-dark-base-300 pr-12 text-right placeholder:text-base-subtle dark:placeholder:text-dark-base-subtle"
                                />
                                <span class="pointer-events-none absolute right-3 text-sm text-base-subtle dark:text-dark-base-subtle">SEK</span>
                            </div>
                        </div>
                        <button
                                type="button"
                                onclick={() => parts = parts.filter((_, j) => j !== i)}
                                class="ml-4 text-base-subtle dark:text-dark-base-subtle hover:cursor-pointer hover:scale-125 transition-all"
                        >
                            {#if i > 0}
                                <X/>
                            {/if}
                        </button>
                    </div>
                </div>
            {/each}
            <button
                    type="button"
                    onclick={() => parts = [...parts, { raw: null, display: '' }]}
                    class="group mt-2 flex cursor-pointer flex-col items-center justify-center gap-1 border-0 bg-base-300 py-3 dark:bg-dark-base-300"
            >
                <span class="flex size-10 items-center rounded-full transition-all group-hover:bg-base-100 dark:group-hover:bg-dark-base-100">
                    <Plus class="m-auto"/>
                </span>
                <span class="text-base-subtle dark:text-dark-base-subtle text-center text-xs font-medium">
                    {$_('new_expense.form.add_part')}
                </span>
            </button>
        </div>

        <input class="hidden"/>
    </fieldset>

    <div class="mx-auto flex w-full flex-row justify-between">
        <button type="button" class="cursor-pointer bg-base-300 p-4 dark:bg-dark-base-300">
            {$_('cancel')}
        </button>
        <button class="flex cursor-pointer bg-money-green-600 hover:bg-money-green-500 w-72 p-4 text-dark-base-text"
                onclick={_ => submitting = true}
        >

            {#if submitting}
                <CashSpinner/>
            {:else}
                <BanknoteArrowUp class="my-auto m-2"/>
                {$_('new_expense.form.submit')}
            {/if}

        </button>
    </div>
</form>
