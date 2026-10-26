/**
 * AGEN Billing Service
 * Calls /billing/* endpoints for subscription info and upgrade/downgrade.
 */
import api from './api';

export interface SubscriptionInfo {
  plan: 'free' | 'premium' | 'family' | 'team';
  status: 'active' | 'canceled' | 'expired';
  is_premium: boolean;
  current_period_end: string | null;
  provider?: string | null;
  /** G5 · 'own' (paid/trial on this account), 'family' (via a parent's family plan) or null. */
  premium_source?: 'own' | 'family' | 'team' | null;
  /** G7 · team plan seats */
  seats?: number;
}

export type PlanKind = 'premium' | 'family' | 'team';

// G3 · real checkout + trial
export type PaymentProvider = 'vnpay' | 'momo';

export interface BillingOptions {
  prices: { months: number; amount_vnd: number }[];
  providers: PaymentProvider[];
  demo_enabled: boolean;
  trial_available: boolean;
  trial_days: number;
  // G5 · gói gia đình
  family_prices: { months: number; amount_vnd: number }[];
  family_max_children: number;
  can_buy_family: boolean;
  // G7 · gói theo ghế cho lớp học / doanh nghiệp
  team_prices: { months: number; amount_vnd: number }[];
  team_min_seats: number;
  team_max_seats: number;
  can_buy_team: boolean;
  seats: number;
}

export interface CheckoutResult {
  order_id: string;
  provider: PaymentProvider;
  pay_url: string;
}

/** G8 · Thông tin xuất hoá đơn VAT (doanh nghiệp / trường học). */
export interface InvoiceInfo {
  company_name: string;
  tax_code: string;
  address: string;
  email: string;
}

export interface OrderInfo {
  order_id: string;
  provider: PaymentProvider | 'demo';
  plan: PlanKind;
  seats: number;
  months: number;
  amount_vnd: number;
  status: 'pending' | 'paid' | 'failed';
  invoice?: InvoiceInfo | null;
  invoice_issued_at?: string | null;
  created_at?: string | null;
  paid_at?: string | null;
}

export const getBillingOptions = async (): Promise<BillingOptions> => (await api.get('/billing/options')).data;
export const startPremiumTrial = async (): Promise<SubscriptionInfo> => (await api.post('/billing/trial')).data;
export const checkout = async (months: number, provider: PaymentProvider, plan: PlanKind = 'premium', seats = 1, invoice?: InvoiceInfo | null): Promise<CheckoutResult> =>
  (await api.post('/billing/checkout', { months, provider, plan, seats, invoice: invoice ?? null })).data;
export const getOrder = async (orderId: string): Promise<OrderInfo> => (await api.get(`/billing/orders/${orderId}`)).data;
export const getMyOrders = async (): Promise<OrderInfo[]> => (await api.get('/billing/orders')).data;
export const requestInvoice = async (orderId: string, invoice: InvoiceInfo): Promise<OrderInfo> => (await api.put(`/billing/orders/${orderId}/invoice`, invoice)).data;

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

export const upgradeToPremium = async (months: number = 1, plan: PlanKind = 'premium', seats = 1, invoice?: InvoiceInfo | null): Promise<SubscriptionInfo> => {
  const res = await api.post('/billing/upgrade', { months, plan, seats, invoice: invoice ?? null });
  return res.data;
};

export const cancelSubscription = async (): Promise<SubscriptionInfo> => {
  const res = await api.post('/billing/cancel');
  return res.data;
};
