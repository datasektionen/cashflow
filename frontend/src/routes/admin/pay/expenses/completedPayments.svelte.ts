import type { Payment } from '$lib/api/types';

// uuugh fh ufgh u
export type PaymentWithAmount = Payment & { amount: string };

export const completedPayments: PaymentWithAmount[] = $state([]);
