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
}

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
