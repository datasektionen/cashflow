import type { User } from '$lib/api/types';

export function mayAccount(user: User | null | undefined): boolean {
	if (user == null) return false;
	return user.permissions.accounting?.length > 0;
}

export function mayConfirm(user: User | null | undefined): boolean {
	if (user == null) return false;
	return user.permissions.confirm;
}

export function mayPay(user: User | null | undefined): boolean {
	if (user == null) return false;
	return user.permissions.pay;
}

export function hasAdminAccess(user: User | null | undefined): boolean {
	if (user == null) return false;
	return Object.values(user.permissions).some((v) => (Array.isArray(v) ? v.length > 0 : v));
}
