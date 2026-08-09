import type { BankInfo, Payment } from '$lib/api/types';
import { SvelteSet } from 'svelte/reactivity';

// uuugh fh ufgh u
export type PaymentWithAmount = Payment & { amount: string; bankInfo: BankInfo };

export const completedPayments: PaymentWithAmount[] = $state([]);

export const paidInvoices: SvelteSet<number> = $state(new SvelteSet<number>());
