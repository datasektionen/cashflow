<script lang="ts" module>
	import { tv, type VariantProps } from 'tailwind-variants';

	export const badgeVariants = tv({
		base: 'inline-flex w-fit shrink-0 items-center gap-1 font-semibold whitespace-nowrap [&_svg]:size-3 [&_svg]:shrink-0',
		variants: {
			variant: {
				neutral: 'bg-muted text-muted-foreground',
				success: 'bg-accent text-accent-foreground',
				warning: 'bg-warning-soft text-warning-soft-foreground',
				danger: 'bg-danger-soft text-danger-soft-foreground',
				outline: 'border border-border text-foreground'
			},
			size: {
				sm: 'px-2 py-0.5 text-xs',
				lg: 'h-7 px-2.5 text-xs tracking-wide uppercase [&_svg]:size-3.5'
			}
		},
		defaultVariants: { variant: 'neutral', size: 'sm' }
	});

	export type BadgeVariant = VariantProps<typeof badgeVariants>['variant'];
	export type BadgeSize = VariantProps<typeof badgeVariants>['size'];
</script>

<script lang="ts">
	import type { HTMLAttributes } from 'svelte/elements';

	type Props = HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant; size?: BadgeSize };

	let { variant, size, class: className, children, ...rest }: Props = $props();
</script>

<span class={badgeVariants({ variant, size, class: className as string })} {...rest}>
	{@render children?.()}
</span>
