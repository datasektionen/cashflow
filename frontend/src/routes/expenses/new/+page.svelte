<script>
	import FileInput from './FileInput.svelte';
	import { _ } from 'svelte-i18n';
	import { Plus, BanknoteArrowUp } from '@lucide/svelte';
	import ComboBox from "$lib/components/ComboBox.svelte";

	const costCenters = [
		"Sektionslokalsgruppen",
		"Mottagningen",
		"D-rektoratet",
		"Studienämnden",
		"Näringslivsnämnden",
		"Internationella nämnden",
		"Idrottsnämnden",
		"Jämlikhetsnämnden",
		"DKM",
		"METAspexet",
		"Fanborgen",
		"Sånggruppen",
		"METAdorerna",
		"Valberedningen",
		"Revisorerna",
	]

	const budgetLines = [
		"Lokalskostnader",
		"Mat och dryck",
		"Transport",
		"Trycksaker",
		"Övrigt",
	]
</script>

<form
	method="POST"
	enctype="multipart/form-data"
	class="mx-auto flex flex-col space-y-4 lg:max-w-2/3"
>
	<FileInput />

	<div class="flex flex-col space-y-2">
		<label for="description">
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
		<label for="date">
			{$_('new_expense.form.date.label')}
		</label>
		<input
			class="border-0 bg-base-300 inset-shadow-sm dark:bg-dark-base-300"
			type="date"
			name="expense_date"
			id="date"
		/>
		<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('new_expense.form.date.help')}
		</span>
	</div>

	<div class="flex flex-col space-y-2">
		<span>
			{$_('new_expense.form.expense_parts.label')}
		</span>

		<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
			{$_('new_expense.form.expense_parts.help')}
		</span>

		<div class="flex flex-col">
			<div class="flex flex-row justify-between bg-base-300 p-4 space-x-2 dark:bg-dark-base-300">

				<div class="flex flex-col">
					<label for="part-0-costcenter">
						{$_('new_expense.form.expense_parts.cost_center_label')}
					</label>
					<ComboBox name="part-0-costcenter" placeholder={$_('new_expense.form.expense_parts.cost_center_placeholder')} items={costCenters}/>
				</div>
				<div class="flex flex-col">
					<label for="part-0-secondarycostcenter">
						{$_('new_expense.form.expense_parts.secondary_cost_center_label')}
					</label>
					<ComboBox name="part-0-secondarycostcenter" placeholder={$_('new_expense.form.expense_parts.secondary_cost_center_placeholder')} items={costCenters}/>
				</div>
				<div class="flex flex-col">
					<label for="part-0-budgetline">
						{$_('new_expense.form.expense_parts.budget_line_label')}
					</label>
					<ComboBox name="part-0-budgetline" placeholder={$_('new_expense.form.expense_parts.budget_line_placeholder')} items={budgetLines}/>
				</div>
				<div class="flex flex-col">
					<label for="part-0-amount">
						{$_('new_expense.form.expense_parts.amount_label')}
					</label>
					<input
						type="number"
						min="0"
						step="0.01"
						name="part-0-amount"
						id="part-0-amount"
						class="border-0 bg-base-300 dark:bg-dark-base-200"
					/>
				</div>
			</div>
			<div
				class="group flex h-16 cursor-pointer flex-row border-0 bg-base-300 dark:bg-dark-base-300"
			>
				<span
					class="m-auto flex size-10 items-center rounded-full transition-all group-hover:bg-base-100 dark:group-hover:bg-dark-base-100"
				>
					<Plus class="m-auto" />
				</span>
			</div>
		</div>

		<input class="hidden" />
	</div>

	<div class="mx-auto flex w-full flex-row justify-between">
		<button class="cursor-pointer bg-base-300 p-4 dark:bg-dark-base-300">
			{$_('cancel')}
		</button>
		<button class="flex cursor-pointer bg-money-green-600 p-4 text-dark-base-text">
			<BanknoteArrowUp class="my-auto mr-2" />
			{$_('new_expense.form.submit')}
		</button>
	</div>
</form>
