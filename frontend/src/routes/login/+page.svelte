<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { Button, Card } from '#lib/components/ui/index.ts';
</script>

<div class="flex min-h-[60vh] items-center justify-center">
	<Card class="w-full max-w-sm">
		<div class="flex flex-col items-center gap-6 px-3 py-6">
			<img src="/icon.png" alt="" class="size-14" />
			<h1 class="text-2xl font-semibold tracking-tight">Cashflow</h1>
			<Button href="/oidc/authenticate/" size="lg" class="w-full">
				{$_('login_with_sso')}
			</Button>
		</div>
	</Card>
</div>
