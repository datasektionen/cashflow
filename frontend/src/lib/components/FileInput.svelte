<script lang="ts">
	import { Columns2, HardDriveUpload, Undo2, X } from '@lucide/svelte';
	import { _ } from 'svelte-i18n';
	import type { ExpenseFile } from '#lib/api/types.ts';
	import FileThumbnail from '#lib/components/FileThumbnail.svelte';
	import { Button } from '#lib/components/ui/index.ts';
	import { fileName } from '#lib/files.ts';

	let {
		files = $bindable<File[]>([]),
		existing = [],
		deleted,
		invalid = false,
		pinned = $bindable()
	}: {
		files?: File[];
		existing?: ExpenseFile[];
		deleted?: Set<number>;
		invalid?: boolean;
		// Bind to show a button that opens an upload next to the form
		pinned?: File | null;
	} = $props();
	let fileInput: HTMLInputElement;
	let dragging = $state(false);

	function syncInput() {
		const dt = new DataTransfer();
		files.forEach((f) => dt.items.add(f));
		fileInput.files = dt.files;
	}

	function add(added: File[]) {
		if (!added.length) return;
		files = [...files, ...added];
		syncInput();
	}

	const hasAny = $derived(existing.length + files.length > 0);

	const accepted = (list?: FileList | null) =>
		Array.from(list ?? []).filter(
			(f) => f.type === 'application/pdf' || f.type.startsWith('image/')
		);

	const hasFiles = (e: DragEvent) => !!e.dataTransfer?.types.includes('Files');

	// Files dropped or pasted anywhere on the page are added
	let dragDepth = 0;
	function ondragenter(e: DragEvent) {
		if (!hasFiles(e)) return;
		dragDepth++;
		dragging = true;
	}
	function ondragleave(e: DragEvent) {
		if (!hasFiles(e)) return;
		dragDepth = Math.max(0, dragDepth - 1);
		if (dragDepth === 0) dragging = false;
	}
	function ondragover(e: DragEvent) {
		if (hasFiles(e)) e.preventDefault();
	}
	function ondrop(e: DragEvent) {
		if (!hasFiles(e)) return;
		e.preventDefault();
		dragDepth = 0;
		dragging = false;
		add(accepted(e.dataTransfer?.files));
	}
	function onpaste(e: ClipboardEvent) {
		const pasted = accepted(e.clipboardData?.files);
		if (!pasted.length) return;
		e.preventDefault();
		add(pasted);
	}

	function removeFile(i: number) {
		if (pinned === files[i]) pinned = null;
		files = files.filter((_, j) => j !== i);
		syncInput();
	}
</script>

<svelte:window {ondragenter} {ondragleave} {ondragover} {ondrop} {onpaste} />

{#snippet row(source: File | string, name: string, meta: string | null, muted: boolean)}
	<div class={['flex min-w-0 flex-1 items-center gap-3', muted && 'opacity-50']}>
		<FileThumbnail {source} class="h-12 w-9 shrink-0" />
		<div class="flex min-w-0 flex-col">
			<span class={['truncate text-sm', muted && 'line-through']}>{name}</span>
			{#if meta}<span class="text-xs text-muted-foreground">{meta}</span>{/if}
		</div>
	</div>
{/snippet}

<div class="flex flex-1 flex-col gap-3">
	{#if hasAny}
		<ul class="flex max-h-56 flex-col divide-y divide-border overflow-y-auto border border-input">
			{#each existing as file (file.id)}
				{@const isDeleted = !!deleted?.has(file.id)}
				<li class="flex items-center gap-3 px-3 py-2">
					{@render row(file.file, fileName(file.file), null, isDeleted)}
					<Button
						tabindex={-1}
						variant="ghost"
						size="icon-sm"
						aria-label={$_('remove')}
						onclick={() => (isDeleted ? deleted?.delete(file.id) : deleted?.add(file.id))}
					>
						{#if isDeleted}<Undo2 />{:else}<X />{/if}
					</Button>
				</li>
			{/each}
			{#each files as file, i}
				<li class="flex items-center gap-3 px-3 py-2">
					{@render row(file, file.name, `${Math.ceil(file.size / 1024)} kB`, false)}
					{#if pinned !== undefined}
						<Button
							tabindex={-1}
							variant="ghost"
							size="sm"
							class={[
								'hidden lg:inline-flex',
								pinned === file && 'bg-accent text-accent-foreground'
							]}
							aria-pressed={pinned === file}
							onclick={() => (pinned = pinned === file ? null : file)}
						>
							<Columns2 />
							{$_('show_beside')}
						</Button>
					{/if}
					<Button
						tabindex={-1}
						variant="ghost"
						size="icon-sm"
						aria-label={$_('remove')}
						onclick={() => removeFile(i)}
					>
						<X />
					</Button>
				</li>
			{/each}
		</ul>
	{/if}

	<div
		class={[
			'flex flex-1 flex-col items-center justify-center gap-3 border-2 border-dashed px-6 text-center transition-colors',
			hasAny ? 'py-4' : 'py-10',
			dragging ? 'border-primary bg-accent/40' : invalid ? 'border-danger' : 'border-input'
		]}
	>
		<input
			bind:this={fileInput}
			onchange={(e) => add(Array.from(e.currentTarget.files ?? []))}
			type="file"
			id="files"
			name="files"
			multiple
			accept="application/pdf,image/*"
			class="hidden"
		/>
		{#if !hasAny}
			<span class="flex size-10 items-center justify-center bg-muted">
				<HardDriveUpload class="size-5 text-muted-foreground" />
			</span>
		{/if}
		<div class="flex flex-wrap items-center justify-center gap-x-3 gap-y-2">
			<Button variant="secondary" size="sm" onclick={() => fileInput.click()}>
				{#if hasAny}<HardDriveUpload />{/if}
				{$_('browse_files')}
			</Button>
			<span class="text-sm text-muted-foreground pointer-coarse:hidden">{$_('drop_hint')}</span>
		</div>
		{#if !hasAny}
			<p class="text-sm text-muted-foreground">{$_('new_expense.upload_prompt')}</p>
		{/if}
	</div>
</div>
