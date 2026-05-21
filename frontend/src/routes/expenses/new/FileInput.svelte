<script lang="ts">
    import {File as FileIcon, HardDriveUpload, X} from '@lucide/svelte';
    import {_} from 'svelte-i18n';

    let fileInput: HTMLInputElement;
    let receiptFiles: File[] = $state([]);

    function syncInput() {
        const dt = new DataTransfer();
        receiptFiles.forEach(f => dt.items.add(f));
        fileInput.files = dt.files;
    }

    function addFiles(e: Event) {
        const input = e.currentTarget as HTMLInputElement;
        if (!input.files?.length) return;
        receiptFiles = [...receiptFiles, ...Array.from(input.files)];
        syncInput();
    }

    function removeFile(i: number) {
        receiptFiles = receiptFiles.filter((_, j) => j !== i);
        syncInput();
    }
</script>


<div class="flex flex-col md:flex-row  md:max-h-56 bg-base-300 dark:bg-dark-base-300 w-full h-full">

    <!--    Uploaded file list-->
    <div class={receiptFiles.length > 0 ? "relative flex flex-col sm:w-full md:w-md" : "hidden"}>
        <div class="flex flex-col overflow-y-auto max-h-56">
            {#each receiptFiles as file, i}
                <div class="flex flex-row space-x-4 mx-4 border-b border-base-600 dark:border-b-dark-base-200">
                    <span class="flex h-16 w-12">
                        <FileIcon class="m-auto my-auto"/>
                    </span>
                    <!-- Thumbnail coming soon(tm) -->
                    <div class="flex flex-col flex-1">
                        <span class="my-auto">{file.name}</span>
                        <span class="text-sm text-base-subtle dark:text-dark-base-subtle">
                            {Math.ceil(file.size / 1024)} kB
                        </span>
                    </div>
                    <button
                        type="button"
                        onclick={() => removeFile(i)}
                        class="ml-auto text-base-subtle dark:text-dark-base-subtle hover:cursor-pointer hover:scale-115 transition-all">
                        <X />
                    </button>
                </div>
            {/each}
        </div>
        <div class="pointer-events-none absolute bottom-0 left-0 right-0 h-8 bg-linear-to-t from-base-300 dark:from-dark-base-300 to-transparent"></div>
    </div>

    <label
            for="files"
            class="group flex flex-1 cursor-pointer flex-col items-center justify-center"
    >
        <input
                bind:this={fileInput}
                onchange={addFiles}
                type="file"
                id="files"
                name="files"
                multiple
                accept="application/pdf"
                class="hidden"
        />
        <HardDriveUpload class="mx-auto mt-auto mb-4 size-10 transition-all"/>
        <span class="mb-2 w-24 bg-money-green-600 p-2 text-center text-base-100 group-hover:bg-money-green-500 transition-all">
		{$_('browse_files')}
	</span>
        <span class="dark:text-base-sublte mb-auto text-base-subtle">
		{$_('new_expense.upload_prompt')}
	</span>
    </label>

</div>
