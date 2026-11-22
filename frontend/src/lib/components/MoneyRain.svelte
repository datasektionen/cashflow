<script lang="ts" module>
	let bills = $state<{ id: number; x: number; y: number }[]>([]);
	let nextId = 0;

	/** Easter egg: each click on the logo throws a bill out of it. */
	export function throwBill(from: Element) {
		if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
		const { left, top, width, height } = from.getBoundingClientRect();
		bills.push({ id: nextId++, x: left + width / 2, y: top + height / 2 });
	}
</script>

<script lang="ts">
	import BillIcon from './nav/BillIcon.svelte';

	const GRAVITY = 1600;

	// Small hop out of the logo with some sideways spread, then falls off screen
	function fly(id: number) {
		return (node: HTMLElement) => {
			const vx = (Math.random() - 0.5) * 500;
			const vy = -100 - Math.random() * 250;
			const spin = (Math.random() - 0.5) * 1080;
			const duration = (-vy + Math.sqrt(vy * vy + 2 * GRAVITY * innerHeight)) / GRAVITY;
			const frames = Array.from({ length: 31 }, (_, i) => {
				const t = (duration * i) / 30;
				const x = vx * t;
				const y = vy * t + (GRAVITY * t * t) / 2;
				return { transform: `translate(${x}px, ${y}px) rotate(${spin * t}deg)` };
			});
			node.animate(frames, duration * 1000).finished.then(() => {
				bills = bills.filter((b) => b.id !== id);
			});
		};
	}
</script>

{#each bills as bill (bill.id)}
	<div
		aria-hidden="true"
		class="pointer-events-none fixed z-60 -mt-3.5 -ml-6 text-primary"
		style:left="{bill.x}px"
		style:top="{bill.y}px"
		{@attach fly(bill.id)}
	>
		<BillIcon class="w-12" />
	</div>
{/each}
