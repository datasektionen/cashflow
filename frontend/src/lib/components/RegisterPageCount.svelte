<!--
@component
Reports a PDF's page count up to the parent once known. Exists only because
Svelte forbids mutating state from a template expression (`{@const}`) — this
does it from a real `$effect` instead.
-->
<script lang="ts">
	export type RegisterPageCountProps = {
		url: string;
		count: number;
		onRegister: (url: string, count: number) => void;
	};

	const { url, count, onRegister }: RegisterPageCountProps = $props();

	$effect(() => {
		onRegister(url, count);
	});
</script>
