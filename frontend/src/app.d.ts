// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
import { User } from '$lib/api/types';

declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			user: User | null;
		}
		interface PageData {
			title?: string | Promise<string>;
			title_key?: string;
		}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};
