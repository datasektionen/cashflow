<script lang="ts" module>
	import { tv, type VariantProps } from 'tailwind-variants';

	export const buttonVariants = tv({
		base: 'inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 font-semibold whitespace-nowrap transition-colors select-none disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [&_svg]:size-4 [&_svg]:shrink-0',
		variants: {
			variant: {
				primary: 'bg-primary text-primary-foreground hover:bg-primary-hover',
				secondary:
					'border border-input bg-card text-foreground hover:border-muted-foreground hover:bg-muted',
				ghost: 'text-foreground hover:bg-muted',
				danger: 'bg-danger text-danger-foreground hover:bg-danger-hover',
				'danger-outline':
					'border border-input bg-card text-danger-text hover:bg-danger-soft hover:text-danger-soft-foreground'
			},
			size: {
				sm: 'h-8 px-3 text-xs',
				md: 'h-9 px-4 text-sm',
				lg: 'h-11 px-6 text-sm',
				icon: 'size-9',
				'icon-sm': 'size-8'
			}
		},
		defaultVariants: { variant: 'primary', size: 'md' }
	});

	export type ButtonVariant = VariantProps<typeof buttonVariants>['variant'];
	export type ButtonSize = VariantProps<typeof buttonVariants>['size'];
</script>

<script lang="ts">
	import { Button as ButtonPrimitive } from 'bits-ui';

	type Props = ButtonPrimitive.RootProps & {
		variant?: ButtonVariant;
		size?: ButtonSize;
	};

	let {
		variant,
		size,
		type = 'button',
		class: className,
		ref = $bindable(null),
		...rest
	}: Props = $props();
</script>

<ButtonPrimitive.Root
	bind:ref
	{...{ ...rest, type } as ButtonPrimitive.RootProps}
	class={buttonVariants({ variant, size, class: className as string })}
/>
