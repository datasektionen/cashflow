<!--
@component
Table cell component that shows cost centre, secondary cost centre, and budget line
-->
<script lang="ts">
	import { ChevronRight } from '@lucide/svelte';

	let {
		costCentre,
		secondaryCostCentre,
		budgetLine
	}: {
		costCentre: string;
		secondaryCost: string;
		budgetLine: string;
	} = $props();
</script>

<div class="flex flex-row items-center">
	<span class="text-xs text-base-subtle dark:text-dark-base-subtle">{costCentre}</span>
	<ChevronRight class="size-3" />
	<span class="text-xs text-base-subtle dark:text-dark-base-subtle">{costCentre}</span>
	<ChevronRight class="size-3" />
	<span class="text-xs text-base-subtle dark:text-dark-base-subtle">{costCentre}</span>
</div>
