<script>
    import FileInput from './FileInput.svelte';
    import {_} from 'svelte-i18n';
    import {BanknoteArrowUp, Plus, CircleQuestionMark} from '@lucide/svelte';
    import ComboBox from '$lib/components/ComboBox.svelte';

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
</script>

<form
        method="POST"
        enctype="multipart/form-data"
        class="flex flex-col space-y-4"
>

    <div class="flex flex-col lg:flex-row justify-between space-y-6">

        <fieldset class="flex flex-col space-y-6 border-0 p-0">
            <div class="flex flex-col space-y-2">
                <label for="description" class="text-s font-medium mb-1">
                    {$_('new_expense.form.description.label')}
                </label>
                <input
                        class="border-0 bg-base-300 inset-shadow-sm dark:bg-dark-base-300"
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
                <input
                        class="border-0 bg-base-300 inset-shadow-sm dark:bg-dark-base-300"
                        type="date"
                        name="expense-date"
                        id="date"
                />
                <span class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('new_expense.form.date.help')}
		</span>
            </div>
        </fieldset>


        <FileInput/>

    </div>


    <fieldset class="flex flex-col space-y-2 border-0 p-0">
		<legend class="text-s font-medium mb-1 flex flex-row items-center">
			{$_('new_expense.form.expense_parts.label')}
            <a href="/help/expense-parts"
               class="text-money-green-800 dark:text-money-green-600 group"
            >
               <CircleQuestionMark class="size-4 mx-2 group-hover:scale-125 transition-all" />
            </a>
		</legend>

        <span class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('new_expense.form.expense_parts.help')}
		</span>

        <div class="flex flex-col">
            <div class="flex bg-base-300 p-4 dark:bg-dark-base-300 md:justify-between">
                <div class="flex flex-wrap lg:flex-row w-full justify-between border-b border-base-500 dark:border-dark-base-200">
                    <div class="flex flex-col space-y-1">
					<span class="text-sm font-medium mb-1">
						{$_('new_expense.form.expense_parts.cost_center_label')}
					</span>
                        <ComboBox
                                name="part-0-costcenter"
                                placeholder={$_('new_expense.form.expense_parts.cost_center_placeholder')}
                                items={costCenters}
                        />
                    </div>
                    <div class="flex flex-col space-y-1">
					<span class="text-sm font-medium mb-1">
						{$_('new_expense.form.expense_parts.secondary_cost_center_label')}
					</span>
                        <ComboBox
                                name="part-0-secondarycostcenter"
                                placeholder={$_('new_expense.form.expense_parts.secondary_cost_center_placeholder')}
                                items={costCenters}
                        />
                    </div>
                    <div class="flex flex-col space-y-1">
					<span class="text-sm font-medium mb-1">
						{$_('new_expense.form.expense_parts.budget_line_label')}
					</span>
                        <ComboBox
                                name="part-0-budgetline"
                                placeholder={$_('new_expense.form.expense_parts.budget_line_placeholder')}
                                items={budgetLines}
                        />
                    </div>
                    <div class="flex flex-col space-y-1">
					<span class="text-sm font-medium mb-1 text-right">
						{$_('new_expense.form.expense_parts.amount_label')}
					</span>
                        <input
                                type="number"
                                min="0"
                                step="0.01"
                                name="part-0-amount"
                                id="part-0-amount"
                                class="border-0  bg-base-300 dark:bg-dark-base-300 "
                        />
                    </div>
                </div>


            </div>
            <div
                    class="group mt-2 flex cursor-pointer flex-col items-center justify-center gap-1 border-0 bg-base-300 py-3 dark:bg-dark-base-300"
            >
				<span
                        class="flex size-10 items-center rounded-full transition-all group-hover:bg-base-100 dark:group-hover:bg-dark-base-100"
                >
					<Plus class="m-auto"/>
				</span>
                <p class="text-base-subtle dark:text-dark-base-subtle text-center text-xs font-medium">
                    {$_('new_expense.form.add_part')}
                </p>
            </div>
        </div>

        <input class="hidden"/>
    </fieldset>

    <div class="mx-auto flex w-full flex-row justify-between">
        <button class="cursor-pointer bg-base-300 p-4 dark:bg-dark-base-300">
            {$_('cancel')}
        </button>
        <button class="flex cursor-pointer bg-money-green-600 p-4 text-dark-base-text">
            <BanknoteArrowUp class="my-auto mr-2"/>
            {$_('new_expense.form.submit')}
        </button>
    </div>
</form>
