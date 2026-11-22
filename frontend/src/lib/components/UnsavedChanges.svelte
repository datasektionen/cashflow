<script lang="ts">
	import { _ } from 'svelte-i18n';
	import { beforeNavigate, goto } from '$app/navigation';
	import { ConfirmDialog } from '#lib/components/ui/index.ts';

	// Asks before leaving a form whose data changed: stay, leave, or save and leave
	type Props = {
		data: () => unknown;
		submit: { saved: boolean; save: () => Promise<string | undefined> };
	};

	let { data, submit }: Props = $props();

	const snapshot = () =>
		JSON.stringify(data(), (key, v) => {
			if (key === 'budgetUsage') return undefined; // budget usage fills in by itself
			// Sets and files would otherwise serialise to {}
			return v instanceof Set ? [...v] : v instanceof File ? [v.name, v.size] : v;
		});
	const initial = snapshot();

	let open = $state(false);
	let target: URL | undefined;
	let leaving = false;

	beforeNavigate((nav) => {
		if (leaving || submit.saved || snapshot() === initial) return;
		nav.cancel();
		// Closing or reloading the tab gets the browser's own prompt
		if (nav.type === 'leave' || !nav.to) return;
		target = nav.to.url;
		open = true;
	});

	function leave() {
		if (!target) return;
		leaving = true;
		if (target.origin === location.origin) goto(target);
		else location.href = target.href;
	}
</script>

<ConfirmDialog
	bind:open
	title={$_('unsaved.title')}
	cancelLabel={$_('unsaved.stay')}
	alternative={{ label: $_('unsaved.leave'), onclick: leave }}
	confirmLabel={$_('unsaved.save_and_leave')}
	onConfirm={async () => {
		if (await submit.save()) leave();
	}}
/>
