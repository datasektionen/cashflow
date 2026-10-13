import type { BankInfo, Payment } from '$lib/api/types';
import type { Dinero } from 'dinero.js';
import { SvelteSet } from 'svelte/reactivity';

// uuugh fh ufgh u
export type PaymentWithAmount = Payment & { amount: Dinero<number, 'SEK'>; bankInfo: BankInfo };

export const completedPayments: PaymentWithAmount[] = $state([]);

export const paidInvoices: SvelteSet<number> = $state(new SvelteSet<number>());
