<script lang="ts">
	import { _ } from 'svelte-i18n';
</script>

<p>
	{$_('welcome.intro')}
</p>

<h1 class="text-xl font-bold dark:text-slate-100">{$_('welcome.process.title')}</h1>
<ol class="list-inside list-decimal">
	<li class="marker:font-bold marker:text-gray-900 dark:marker:text-slate-100">
		<span class="font-bold text-gray-900 dark:text-slate-100">
			{$_('welcome.process.registration.title')}.
		</span>
		<span>
			{$_('welcome.process.registration.description')}
		</span>
	</li>
	<li class="marker:font-bold marker:text-gray-900 dark:marker:text-slate-100">
		<span class="font-bold text-gray-900 dark:text-slate-100">
			{$_('welcome.process.validation.title')}.
		</span>
		<span>
			{$_('welcome.process.validation.description')}
		</span>
	</li>
	<li class="marker:font-bold marker:text-gray-900 dark:marker:text-slate-100">
		<span class="font-bold text-gray-900 dark:text-slate-100">
			{$_('welcome.process.attestation.title')}.
		</span>
		<span>
			{$_('welcome.process.attestation.description')}
		</span>
	</li>
	<li class="marker:font-bold marker:text-gray-900 dark:marker:text-slate-100">
		<span class="font-bold text-gray-900 dark:text-slate-100">
			{$_('welcome.process.payment.title')}.
		</span>
		<span>
			{$_('welcome.process.payment.description')}
		</span>
	</li>
	<li class="marker:font-bold marker:text-gray-900 dark:marker:text-slate-100">
		<span class="font-bold text-gray-900 dark:text-slate-100">
			{$_('welcome.process.accounting.title')}.
		</span>
		<span>
			{$_('welcome.process.accounting.description')}
		</span>
	</li>
</ol>
