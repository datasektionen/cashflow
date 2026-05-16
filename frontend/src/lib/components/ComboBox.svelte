<!--
@component
A combobox (mix between select and text input) for selecting from a list of options.
Wraps bits-ui's Combobox component. Supports fuzzy text search using fuse.js.
-->
<script lang="ts">
    import {_} from "svelte-i18n"
    import {ChevronDown, ChevronsUpDown, ChevronUp} from "@lucide/svelte";
    import {Combobox} from "bits-ui";
    import Fuse from "fuse.js"

    let { name, items, placeholder = "" }: { name: string, items: string[], placeholder?: string } = $props()

    let searchValue = $state("")
    let selected: string = $state("")

    const fuse = $derived(new Fuse(items))
    let filtered = $derived(fuse.search(searchValue))
</script>


<Combobox.Root
        type="single"
        {name}
        bind:value={selected}
        inputValue={searchValue}
>

    <div class="relative">
        <div class="flex flex-row">
            <Combobox.Input
                    class="bg-base-100 dark:bg-dark-base-200 inseet-shadow-sm p-2 placeholder:text-base-subtle placeholder:text-sm dark:placeholder:text-dark-base-subtle"
                    oninput={(e) => (searchValue = e.currentTarget.value)}
                    onkeydown={(e) => {
                        if (e.key === "Tab" && searchValue !== "") {
                            selected = filtered[0]? filtered[0].item: ""
                            searchValue = filtered[0]? filtered[0].item: searchValue
                        }
                    }}
                    {placeholder}
                    aria-label={placeholder}
            >
            </Combobox.Input>
            <Combobox.Trigger
                class="bg-base-200 dark:bg-dark-base-200"
            >
                <ChevronsUpDown/>
            </Combobox.Trigger>
        </div>

        <Combobox.Portal>
            <Combobox.Content
                    sideOffset={10}
                    class="focus-override w-full bg-base-200 dark:bg-dark-base-200 h-96 border-muted border-base-300 dark:border-dark-base-300 border-2">
                <Combobox.ScrollUpButton class="text-base dark:text-dark-base-text p-2">
                    <ChevronUp class="m-auto"/>
                </Combobox.ScrollUpButton>
                <Combobox.Viewport class="w-full p-2">
                    {#each filtered.map(it => it.item) as item}
                        <Combobox.Item
                                class="p-2 text-base-text dark:text-dark-base-text data-highlighted:bg-base-300 dark:data-highlighted:bg-dark-base-300 cursor-pointer"
                                value={item}
                                label={item}
                        >{item}</Combobox.Item>
                    {:else}
                        <span class="block px-5 py-2 text-sm text-base-subtle dark:text-dark-base-subtle">
                            {$_('no_results')}
                        </span>
                    {/each}
                </Combobox.Viewport>
                <Combobox.ScrollDownButton class="text-base-text dark:text-dark-base-text p-2">
                    <ChevronDown class="m-auto"/>
                </Combobox.ScrollDownButton>
            </Combobox.Content>
        </Combobox.Portal>
    </div>
</Combobox.Root>