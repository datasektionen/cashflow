import type { User } from '$lib/api/types';

export function hasAdminAccess(user: User | null | undefined): boolean {
	if (user == null) return false;
	return Object.values(user.permissions).some((v) => (Array.isArray(v) ? v.length > 0 : v));
}
