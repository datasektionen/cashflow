<script lang="ts">
	import { _ } from 'svelte-i18n';
</script>

<div class="flex h-full w-full items-center justify-center">
	<div
		class="flex h-128 w-full items-center justify-center bg-base-400 md:w-1/2 dark:bg-dark-base-200"
	>
		<a
			href="http://localhost:8000/login?next=http%3A%2F%2Flocalhost%3A5173%2F"
			class="flex w-72 cursor-pointer items-center justify-center bg-money-green-600 p-4 text-dark-base-text hover:bg-money-green-500"
		>
			{$_('login_with_sso')}
		</a>
	</div>
</div>
