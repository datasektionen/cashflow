<script lang="ts">
	import { HardDriveUpload, File } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';

	let receiptFiles: FileList = $state();
</script>

<div class="flex flex-col">
	{#each receiptFiles as file}
		<div class="flex flex-row space-x-4 bg-base-200 p-4 dark:bg-dark-base-200">
			<span class="flex h-16 w-12 bg-base-300 dark:bg-dark-base-300">
				<File class="m-auto my-auto" />
			</span>

			<div class="flex flex-col">
				<span class="my-auto">{file.name}</span>
				<span class="text-sm text-base-subtle dark:text-dark-base-subtle">
					{Math.ceil(file.size / 1024)} kB
				</span>
			</div>
		</div>
	{/each}
</div>

<label
	for="files"
	class="group flex h-auto cursor-pointer
flex-col items-center bg-base-200 p-5 inset-shadow-sm dark:bg-dark-base-200
"
>
	<input
		bind:files={receiptFiles}
		type="file"
		id="files"
		name="files"
		multiple
		accept="application/pdf"
		class="hidden"
	/>
	<HardDriveUpload class="mx-auto mt-auto mb-4 size-10 transition-all" />
	<span class="mb-2 w-24 bg-money-green-600 p-2 text-center text-base-100">
		{$_('browse_files')}
	</span>
	<span class="dark:text-base-sublte mb-auto text-base-subtle">
		{$_('new_expense.upload_prompt')}
	</span>
</label>
