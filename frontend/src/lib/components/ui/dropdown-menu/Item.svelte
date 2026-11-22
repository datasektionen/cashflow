<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import { cn } from 'tailwind-variants';
	import { menuItem } from '../styles';

	let { class: className, ...rest }: DropdownMenu.ItemProps = $props();
</script>

<DropdownMenu.Item class={cn(menuItem, className as string)} {...rest} />
