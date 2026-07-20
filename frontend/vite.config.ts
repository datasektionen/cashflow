import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

import { svelteTesting } from '@testing-library/svelte/vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit(), svelteTesting()],
	server: {
		proxy: {
			'^/(api|admin|oidc|fortnox|static|media)(/|$)': 'http://localhost:8000'
		}
	},
	test: {
		environment: 'jsdom',
		setupFiles: ['./vitest-setup.js']
	}
});
