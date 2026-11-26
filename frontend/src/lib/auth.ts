import type { User } from '#lib/api/types.ts';

type MaybeUser = User | null | undefined;

export const mayAccount = (user: MaybeUser) => !!user?.permissions.accounting?.length;
export const mayConfirm = (user: MaybeUser) => !!user?.permissions.confirm;
export const mayPay = (user: MaybeUser) => !!user?.permissions.pay;

export const hasAdminAccess = (user: MaybeUser) =>
	!!user && Object.values(user.permissions).some((v) => (Array.isArray(v) ? v.length > 0 : v));
