<script lang="ts">
	import Skeleton from '$lib/components/ui/Skeleton.svelte';
</script>

<div class="animate-delayed-fade-in [&_.animate-pulse]:[animation-duration:2s]">
	<div class="mb-6 flex flex-wrap items-center justify-between gap-3">
		<div class="flex w-full max-w-xl flex-col items-start gap-3">
			<Skeleton class="h-7 w-full rounded-sm" />
			<Skeleton class="h-5 w-20 rounded-sm" />
		</div>
		<Skeleton class="h-7 w-48 rounded-sm" />
	</div>

	<div class="flex flex-col gap-4 lg:flex-row">
		<div class="flex max-h-256 flex-col lg:w-1/3">
			<Skeleton class="aspect-3/4 max-h-256 w-full rounded-sm" />
		</div>

		<div class="flex flex-col gap-12 lg:w-2/3 lg:pt-1 xl:pr-16">
			<div class="flex flex-col gap-3">
				<Skeleton class="h-5 w-24 rounded-sm" />
				<Skeleton class="h-32 w-full rounded-sm" />
			</div>

			<div class="flex flex-col gap-3">
				<Skeleton class="h-5 w-28 rounded-sm" />
				<Skeleton class="h-52 w-full rounded-sm" />
			</div>
		</div>
	</div>
</div>
