/**
 * AGEN Billing Service
 * Calls /billing/* endpoints for subscription info and upgrade/downgrade.
 */
import api from './api';

export interface SubscriptionInfo {
  plan: 'free' | 'premium';
  status: 'active' | 'canceled' | 'expired';
  is_premium: boolean;
  current_period_end: string | null;
  provider?: string | null;
}

// G3 · real checkout + trial
export type PaymentProvider = 'vnpay' | 'momo';

export interface BillingOptions {
  prices: { months: number; amount_vnd: number }[];
  providers: PaymentProvider[];
  demo_enabled: boolean;
  trial_available: boolean;
  trial_days: number;
}

export interface CheckoutResult {
  order_id: string;
  provider: PaymentProvider;
  pay_url: string;
}

export interface OrderInfo {
  order_id: string;
  provider: PaymentProvider;
  months: number;
  amount_vnd: number;
  status: 'pending' | 'paid' | 'failed';
}

export const getBillingOptions = async (): Promise<BillingOptions> => (await api.get('/billing/options')).data;
export const startPremiumTrial = async (): Promise<SubscriptionInfo> => (await api.post('/billing/trial')).data;
export const checkout = async (months: number, provider: PaymentProvider): Promise<CheckoutResult> =>
  (await api.post('/billing/checkout', { months, provider })).data;
export const getOrder = async (orderId: string): Promise<OrderInfo> => (await api.get(`/billing/orders/${orderId}`)).data;

export interface QuotaInfo {
  plan: string;
  is_premium: boolean;
  used_today: number;
  limit: number | null;
  remaining: number | null;
  allowed: boolean;
}

export const getSubscription = async (): Promise<SubscriptionInfo> => {
  const res = await api.get('/billing/subscription');
  return res.data;
};

export const getQuota = async (): Promise<QuotaInfo> => {
  const res = await api.get('/billing/quota');
  return res.data;
};

export const upgradeToPremium = async (months: number = 1): Promise<SubscriptionInfo> => {
  const res = await api.post('/billing/upgrade', { months });
  return res.data;
};

export const cancelSubscription = async (): Promise<SubscriptionInfo> => {
  const res = await api.post('/billing/cancel');
  return res.data;
};
