<!--
@component
A single-line text input with an icon, styled to match Combobox/AmountInput.
-->
<script lang="ts">
	import type { Component } from 'svelte';
	import { innerInput, inputShell } from './inputShell';

	let {
		value = $bindable(''),
		placeholder = '',
		icon: Icon,
		onchange
	}: {
		value?: string;
		placeholder?: string;
		icon: Component;
		onchange: (value: string) => void;
	} = $props();
</script>

<div class={inputShell}>
	<span class="flex shrink-0 pl-3 text-muted-foreground [&_svg]:size-4">
		<Icon />
	</span>
	<input
		type="text"
		bind:value
		oninput={() => onchange(value)}
		{placeholder}
		aria-label={placeholder}
		class={[innerInput, 'pl-2']}
	/>
</div>
