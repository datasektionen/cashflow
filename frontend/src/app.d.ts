import { User } from '#lib/api/types.ts';

declare global {
	namespace App {
		interface Locals {
			user: User | null;
		}
		interface PageData {
			title?: string | Promise<string>;
			title_key?: string;
			// The page renders its own PageHeader
			ownHeader?: boolean;
		}
	}
}

export {};
