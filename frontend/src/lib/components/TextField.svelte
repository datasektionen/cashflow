<script lang="ts">
	import { Field, Input } from '#lib/components/ui/index.ts';
	import type { FormValidation } from '#lib/formValidation.svelte.ts';

	let {
		name,
		label,
		help,
		form,
		value = $bindable()
	}: { name: string; label: string; help?: string; form: FormValidation; value: string } = $props();
</script>

<Field {label} for={name} {help} error={form.errorFor(name)}>
	<Input id={name} {name} onblur={form.onblur} bind:value aria-invalid={form.showErrors(name)} />
</Field>
