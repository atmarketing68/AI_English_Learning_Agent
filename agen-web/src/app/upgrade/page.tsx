'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuthStore, useAuthHydrated } from '@/store/authStore';
import {
  getSubscription, upgradeToPremium, cancelSubscription, getBillingOptions, startPremiumTrial, checkout, getOrder,
  type SubscriptionInfo, type BillingOptions, type PaymentProvider,
} from '@/lib/billingService';
import { playSound } from '@/lib/soundEffects';
import confetti from 'canvas-confetti';
import { ArrowLeft, Check, CircleAlert, CircleCheck, CreditCard, Gift, LoaderCircle, Minus, Users, Wallet } from 'lucide-react';
import { track } from '@/lib/analytics';

const FREE_FEATURES = [
  { label: '3 bài học AI / ngày', included: true },
  { label: 'Luyện Nói Roleplay', included: true },
  { label: 'Luyện Viết & Chấm AI', included: true },
  { label: 'Placement Test', included: true },
  { label: 'Gamification (XP, Streak)', included: true },
  { label: 'Bài học không giới hạn', included: false },
  { label: 'Báo cáo Phụ huynh', included: false },
  { label: 'Lộ trình học cá nhân hoá', included: false },
  { label: 'Ưu tiên hỗ trợ', included: false },
];

const PREMIUM_FEATURES = [
  { label: '3 bài học AI / ngày', included: true },
  { label: 'Luyện Nói Roleplay', included: true },
  { label: 'Luyện Viết & Chấm AI', included: true },
  { label: 'Placement Test', included: true },
  { label: 'Gamification (XP, Streak)', included: true },
  { label: 'Bài học không giới hạn', included: true },
  { label: 'Báo cáo Phụ huynh', included: true },
  { label: 'Lộ trình học cá nhân hoá', included: true },
  { label: 'Ưu tiên hỗ trợ', included: true },
];

const PLAN_PRICES = [
  { months: 1, price: '99.000₫', label: '1 tháng', badge: null },
  { months: 3, price: '249.000₫', label: '3 tháng', badge: 'Tiết kiệm 17%' },
  { months: 12, price: '799.000₫', label: '12 tháng', badge: 'Tốt nhất' },
];

/** G5 · Gói gia đình: phụ huynh mua, các con đã liên kết được Premium. */
const FAMILY_PRICES = [
  { months: 1, price: '179.000₫', label: '1 tháng', badge: null },
  { months: 12, price: '1.490.000₫', label: '12 tháng', badge: 'Tiết kiệm 31%' },
];
const FAMILY_FEATURES = [
  { label: 'Tối đa 4 con cùng Premium', included: true },
  { label: 'Bài học không giới hạn cho mỗi con', included: true },
  { label: 'Báo cáo tuần + cảnh báo nghỉ học qua email', included: true },
  { label: 'Lộ trình cá nhân hoá, khoá IELTS/TOEIC', included: true },
  { label: 'Một lần thanh toán cho cả nhà', included: true },
];

export default function UpgradePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const hydrated = useAuthHydrated();
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [options, setOptions] = useState<BillingOptions | null>(null);
  const [paying, setPaying] = useState<PaymentProvider | null>(null);
  const [trialing, setTrialing] = useState(false);
  // Back from a gateway: /upgrade?status=success|failed&order=…
  const [returned] = useState(() => {
    if (typeof window === 'undefined') return { status: null as string | null, order: null as string | null };
    const q = new URLSearchParams(window.location.search);
    return { status: q.get('status'), order: q.get('order') };
  });
  const [selectedMonths, setSelectedMonths] = useState(3);
  const { userRole } = useAuthStore();
  const isParent = userRole === 'parent';
  const plan = isParent ? 'family' : 'premium';
  const prices = isParent ? FAMILY_PRICES : PLAN_PRICES;
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [canceling, setCanceling] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getBillingOptions().then(o => { setOptions(o); if (o.can_buy_family) setSelectedMonths(12); }).catch(() => null);
    const load = () => getSubscription().then(setSubscription);
    load()
      .catch(() => setError('Không thể tải thông tin gói.'))
      .finally(() => setLoading(false));
    // A MoMo redirect carries no status: poll the order a few times until the IPN lands.
    if (returned.order) {
      let tries = 0;
      const timer = setInterval(async () => {
        tries += 1;
        try {
          const order = await getOrder(returned.order!);
          if (order.status === 'paid') {
            clearInterval(timer);
            await load();
            setSuccess(true);
            track('upgrade_completed', { months: order.months, provider: order.provider });
            playSound('success');
            confetti({ particleCount: 90, spread: 70, origin: { y: 0.5 }, colors: ['#0071E3', '#1F9D55', '#D97A00', '#8E4EC6'] });
          } else if (order.status === 'failed' || tries >= 10) {
            clearInterval(timer);
            if (order.status === 'failed' || returned.status === 'failed') setError('Thanh toán chưa hoàn tất. Bạn có thể thử lại.');
          }
        } catch { clearInterval(timer); }
      }, 2000);
      return () => clearInterval(timer);
    }
  }, [hydrated, isAuthenticated, router, returned.order, returned.status]);

  const handleCheckout = async (provider: PaymentProvider) => {
    setPaying(provider);
    setError('');
    track('checkout_started', { months: selectedMonths, provider, plan });
    try {
      const res = await checkout(selectedMonths, provider, plan);
      window.location.href = res.pay_url;
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Không mở được cổng thanh toán. Vui lòng thử lại.');
      setPaying(null);
    }
  };

  const handleTrial = async () => {
    setTrialing(true);
    setError('');
    try {
      const updated = await startPremiumTrial();
      setSubscription(updated);
      setOptions(o => (o ? { ...o, trial_available: false } : o));
      setSuccess(true);
      track('trial_started');
      playSound('success');
      confetti({ particleCount: 90, spread: 70, origin: { y: 0.5 }, colors: ['#0071E3', '#1F9D55', '#D97A00', '#8E4EC6'] });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Không bắt đầu được dùng thử.');
    } finally {
      setTrialing(false);
    }
  };

  const handleUpgrade = async () => {
    setUpgrading(true);
    setError('');
    track('upgrade_clicked', { months: selectedMonths, plan });
    try {
      const updated = await upgradeToPremium(selectedMonths, plan);
      setSubscription(updated);
      setSuccess(true);
      track('upgrade_completed', { months: selectedMonths });
      playSound('success');
      confetti({ particleCount: 90, spread: 70, origin: { y: 0.5 }, colors: ['#0071E3', '#1F9D55', '#D97A00', '#8E4EC6'] });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Nâng cấp thất bại. Vui lòng thử lại.');
    } finally {
      setUpgrading(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm('Bạn có chắc muốn hủy gói Premium không?')) return;
    setCanceling(true);
    try {
      const updated = await cancelSubscription();
      setSubscription(updated);
    } catch {
      setError('Hủy gói thất bại. Vui lòng thử lại.');
    } finally {
      setCanceling(false);
    }
  };

  if (loading) return (
    <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)' }}>
      <LoaderCircle className="animate-spin" size={20} /> Đang tải thông tin gói…
    </main>
  );

  const isPremium = subscription?.is_premium;

  return (
    <main style={{ minHeight: '100vh', padding: 'clamp(24px, 5vw, 48px) var(--page-gutter) 80px' }}>
      <div className="container" style={{ padding: 0 }}>

        {/* Back */}
        <Link href={isParent ? '/parent' : '/dashboard'} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 32 }}>
          <ArrowLeft size={16} /> {isParent ? 'Bảng phụ huynh' : 'Dashboard'}
        </Link>

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
          style={{ textAlign: 'center', marginBottom: 56 }}
        >
          <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--agen-accent)', marginBottom: 10 }}>{isParent ? 'Gói gia đình' : 'Premium'}</div>
          <h1 style={{ fontSize: 'clamp(2.4rem, 6vw, 3.75rem)', letterSpacing: '-0.04em', marginBottom: 14 }}>
            {isParent ? 'Cả nhà cùng học.' : 'Học không giới hạn.'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.15rem', maxWidth: 560, margin: '0 auto' }}>
            {isParent
              ? `Một lần thanh toán, tối đa ${options?.family_max_children ?? 4} con đã liên kết đều được Premium: bài học không giới hạn, báo cáo tuần và lộ trình riêng.`
              : 'Mở khóa toàn bộ tiềm năng học tiếng Anh với AI Coach cá nhân và bài học không giới hạn.'}
          </p>
        </motion.div>

        {/* Current Plan Banner */}
        {isPremium && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="card"
            style={{
              marginBottom: 40,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap',
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: 8 }}>
                <CircleCheck size={18} color="var(--agen-success)" /> {subscription?.plan === 'family' ? 'Gói gia đình đang hoạt động — các con đã liên kết đều là Premium' : subscription?.premium_source === 'family' ? 'Bạn đang là Premium qua gói gia đình của bố mẹ' : 'Bạn đang dùng AI AGENT ENGLISH Premium'}
              </div>
              {subscription?.current_period_end && (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  Hết hạn: {new Date(subscription.current_period_end).toLocaleDateString('vi-VN')}
                </div>
              )}
            </div>
            {subscription?.premium_source !== 'family' && (
              <button
                className="btn btn-ghost btn-sm"
                style={{ color: 'var(--agen-secondary)' }}
                onClick={handleCancel}
                disabled={canceling}
              >
                {canceling ? 'Đang hủy…' : 'Hủy gói'}
              </button>
            )}
          </motion.div>
        )}

        {/* Success Banner */}
        {success && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="card"
            style={{ marginBottom: 32, textAlign: 'center', padding: 'var(--spacing-xl)' }}
          >
            <CircleCheck size={36} strokeWidth={1.6} color="var(--agen-success)" style={{ marginBottom: 10 }} />
            <div style={{ fontWeight: 600, fontSize: '1.15rem' }}>
              Chào mừng đến với AI AGENT ENGLISH Premium
            </div>
            <p style={{ color: 'var(--text-secondary)', marginTop: 4, fontSize: '0.92rem' }}>
              Tất cả tính năng Premium đã được mở khóa. Chúc bạn học vui.
            </p>
          </motion.div>
        )}

        {error && <div className="alert-error" style={{ marginBottom: 24 }}><CircleAlert size={16} style={{ flexShrink: 0 }} /> {error}</div>}

        {/* Pricing Cards */}
        {!isPremium && (
          <div style={{ marginBottom: 72 }}>
            <h3 style={{ textAlign: 'center', marginBottom: 24 }}>{isParent ? 'Chọn thời hạn gói gia đình' : 'Chọn gói phù hợp với bạn'}</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 32, maxWidth: isParent ? 520 : undefined, marginLeft: 'auto', marginRight: 'auto' }}>
              {prices.map((p) => {
                const active = selectedMonths === p.months;
                return (
                  <button
                    key={p.months}
                    onClick={() => setSelectedMonths(p.months)}
                    aria-pressed={active}
                    style={{
                      padding: '28px 20px', borderRadius: 18, cursor: 'pointer', textAlign: 'center', fontFamily: 'inherit',
                      border: active ? '1.5px solid var(--agen-primary)' : '1.5px solid var(--border-subtle)',
                      boxShadow: active ? '0 0 0 3px rgba(0,113,227,0.12)' : 'none',
                      background: 'var(--bg-surface)', color: 'var(--text-primary)',
                      position: 'relative', transition: 'border-color 0.2s, box-shadow 0.2s',
                    }}
                  >
                    {p.badge && (
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--agen-accent)', marginBottom: 6 }}>
                        {p.badge}
                      </div>
                    )}
                    <div style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', marginBottom: 6 }}>{p.label}</div>
                    <div style={{ fontSize: '1.9rem', fontWeight: 600, letterSpacing: '-0.03em' }}>{p.price}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 4 }}>
                      ~{Math.round(parseInt(p.price.replace(/\D/g, '')) / p.months / 1000)}K/tháng
                    </div>
                  </button>
                );
              })}
            </div>

            {options?.trial_available && !isParent && (
              <div className="card" style={{ marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap', borderColor: 'color-mix(in srgb, var(--agen-success) 40%, transparent)' }}>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                  <span className="icon-tile" style={{ background: 'color-mix(in srgb, var(--agen-success) 12%, transparent)', color: 'var(--agen-success)' }}><Gift size={20} /></span>
                  <div>
                    <div style={{ fontWeight: 600 }}>Dùng thử Premium {options.trial_days} ngày miễn phí</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Không cần thẻ. Hết hạn tự về gói miễn phí, không trừ tiền.</div>
                  </div>
                </div>
                <button className="btn btn-success" onClick={handleTrial} disabled={trialing}>
                  {trialing ? <LoaderCircle className="animate-spin" size={16} /> : <Gift size={16} />} Bắt đầu dùng thử
                </button>
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
              {options?.providers.includes('vnpay') && (
                <button className="btn btn-primary btn-lg" onClick={() => handleCheckout('vnpay')} disabled={!!paying || upgrading} style={{ minWidth: 300 }}>
                  {paying === 'vnpay' ? <LoaderCircle className="animate-spin" size={18} /> : <CreditCard size={18} />} Thanh toán qua VNPay · {prices.find(p => p.months === selectedMonths)?.price}
                </button>
              )}
              {options?.providers.includes('momo') && (
                <button className="btn btn-lg" onClick={() => handleCheckout('momo')} disabled={!!paying || upgrading} style={{ minWidth: 300, background: '#A50064', color: '#fff' }}>
                  {paying === 'momo' ? <LoaderCircle className="animate-spin" size={18} /> : <Wallet size={18} />} Thanh toán qua Ví MoMo
                </button>
              )}
              {options?.demo_enabled && (
                <button
                  className={`btn btn-lg ${options.providers.length ? 'btn-outline' : 'btn-primary'}`}
                  onClick={handleUpgrade}
                  disabled={upgrading || !!paying}
                  style={{ minWidth: 300 }}
                >
                  {upgrading ? 'Đang xử lý…' : `${options.providers.length ? 'Kích hoạt demo' : isParent ? 'Kích hoạt gói gia đình' : 'Nâng cấp Premium'} · ${prices.find(p => p.months === selectedMonths)?.price}`}
                </button>
              )}
              {options && !options.providers.length && !options.demo_enabled && (
                <p style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem' }}>Thanh toán trực tuyến đang được kích hoạt. Hãy dùng thử 7 ngày miễn phí trước nhé.</p>
              )}
            </div>
            <p style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 12 }}>
              {options?.providers.length
                ? 'Thanh toán an toàn qua VNPay (thẻ ATM/QR/thẻ quốc tế) hoặc Ví MoMo. Gói được kích hoạt ngay sau khi thanh toán thành công.'
                : options?.demo_enabled ? 'Demo: không có thanh toán thật — chỉ dùng cho mục đích Pilot.' : ''}
            </p>
          </div>
        )}

        {/* Feature Comparison */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
        >
          <h2 style={{ textAlign: 'center', marginBottom: 32 }}>So sánh tính năng</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
            {(isParent ? [
              { name: 'Gói gia đình', price: 'từ 124K₫ / tháng cho cả nhà', features: FAMILY_FEATURES, highlight: true },
            ] : [
              { name: 'Miễn phí', price: '0₫ / tháng', features: FREE_FEATURES, highlight: false },
              { name: 'Premium', price: 'từ 83K₫ / tháng', features: PREMIUM_FEATURES, highlight: true },
            ]).map(plan => (
              <div key={plan.name} className="card" style={{ padding: 'var(--spacing-xl)', border: plan.highlight ? '1.5px solid var(--agen-primary)' : undefined }}>
                <div style={{ marginBottom: 24 }}>
                  {plan.highlight && <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--agen-accent)', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>{isParent ? <><Users size={12} /> Cho phụ huynh</> : 'Khuyến nghị'}</div>}
                  <div style={{ fontWeight: 600, fontSize: '1.5rem', letterSpacing: '-0.02em' }}>{plan.name}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>{plan.price}</div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  {plan.features.map((f, i) => (
                    <div key={f.label} style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: '0.92rem', padding: '10px 0', borderTop: i ? '1px solid var(--border-subtle)' : 'none' }}>
                      {f.included
                        ? <Check size={16} strokeWidth={2.2} color="var(--agen-primary)" style={{ flexShrink: 0 }} />
                        : <Minus size={16} color="var(--text-muted)" style={{ flexShrink: 0 }} />}
                      <span style={{ color: f.included ? 'var(--text-primary)' : 'var(--text-muted)' }}>{f.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </motion.div>

      </div>
    </main>
  );
}
