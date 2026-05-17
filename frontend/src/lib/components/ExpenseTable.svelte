<script lang="ts">
    import type {Expense} from "$lib/api/types.ts";
    import {_} from "svelte-i18n";
    let props = $props()

    type Column<T> = {
        key: keyof T;
        header: string;
        render: (row: T) => string
    }
    const columns: Column<Expense>[] = $derived([
        {
            key: "id",
            header: $_("admin_expenses.columns.id"),
            render: e => e.id.toString()
        },
        {
            key: "verification",
            header: $_("admin_expenses.columns.voucher"),
            render: e => e.verification
        },
        {
            key: "description",
            header: $_("admin_expenses.columns.description"),
            render: e => e.description
        },
        {
            key: "owner",
            header: $_("admin_expenses.columns.owner"),
            render: e => e.owner.toString()
        },
        {
            key: "expense_date",
            header: $_("admin_expenses.columns.expense_date"),
            render: e => e.expense_date
        }
    ])

</script>

<table class="w-full">
    <thead>
    <tr>
        {#each columns as column}
            <th class="text-left py-3 px-4 text-xs uppercase text-base-subtle dark:text-dark-base-subtle font-medium">
                {column.header}
            </th>
        {/each}

    </tr>
    </thead>
    <tbody>
    {#each props.expenses as expense}
        <tr class="border-b border-b-base-400 dark:border-dark-base-300 hover:bg-base-200 dark:hover:bg-dark-base-200">
            {#each columns as column}
                <td class="py-3 px-4">
                    {column.render(expense)}
                </td>
                {/each}

        </tr>
    {/each}
    </tbody>
</table>