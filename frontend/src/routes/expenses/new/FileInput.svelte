<script lang="ts">
	import { File as FileIcon, HardDriveUpload, X } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';

	let { files = $bindable<File[]>([]) }: { files?: File[] } = $props();
	let fileInput: HTMLInputElement;

	function syncInput() {
		const dt = new DataTransfer();
		files.forEach((f) => dt.items.add(f));
		fileInput.files = dt.files;
	}

	function addFiles(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		if (!input.files?.length) return;
		files = [...files, ...Array.from(input.files)];
		syncInput();
	}

	function removeFile(i: number) {
		files = files.filter((_, j) => j !== i);
		syncInput();
	}
</script>

<div class="flex h-full w-full flex-col bg-base-300 md:flex-row dark:bg-dark-base-300">
	<!--    Uploaded file list-->
	<div class={files.length > 0 ? 'relative flex flex-col sm:w-full md:w-md' : 'hidden'}>
		<div class="flex max-h-56 flex-col overflow-y-auto">
			{#each files as file, i}
				<div
					class="mx-4 flex flex-row space-x-4 border-b border-base-600 dark:border-b-dark-base-200"
				>
					<span class="flex h-16 w-12">
						<FileIcon class="m-auto my-auto" />
					</span>
					<!-- Thumbnail coming soon(tm) -->
					<div class="flex flex-1 flex-col">
						<span class="my-auto">{file.name}</span>
						<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
							{Math.ceil(file.size / 1024)} kB
						</span>
					</div>
					<button
						type="button"
						onclick={() => removeFile(i)}
						class="ml-auto text-base-subtle transition-all hover:scale-115 hover:cursor-pointer dark:text-dark-base-subtle"
					>
						<X />
					</button>
				</div>
			{/each}
		</div>
		<div
			class="pointer-events-none absolute right-0 bottom-0 left-0 h-8 bg-linear-to-t from-base-300 to-transparent dark:from-dark-base-300"
		></div>
	</div>

	<label for="files" class="group flex flex-1 cursor-pointer flex-col items-center justify-center">
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
		<HardDriveUpload class="mx-auto mb-4 size-10 transition-all" />
		<span
			class="mb-2 w-24 bg-money-green-600 p-2 text-center text-base-100 transition-all group-hover:bg-money-green-500"
		>
			{$_('browse_files')}
		</span>
		<span class="dark:text-base-sublte text-base-subtle">
			{$_('new_expense.upload_prompt')}
		</span>
	</label>
</div>
