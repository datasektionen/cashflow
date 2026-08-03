import type { BankInfo, Payment } from '$lib/api/types';

// uuugh fh ufgh u
export type PaymentWithAmount = Payment & { amount: string; bankInfo: BankInfo };

export const completedPayments: PaymentWithAmount[] = $state([]);
