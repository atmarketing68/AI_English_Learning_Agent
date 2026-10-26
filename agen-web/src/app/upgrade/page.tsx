'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import {
  getSubscription, upgradeToPremium, cancelSubscription,
  type SubscriptionInfo,
} from '@/lib/billingService';
import { playSound } from '@/lib/soundEffects';
import confetti from 'canvas-confetti';
import { ArrowLeft, Check, CircleAlert, CircleCheck, LoaderCircle, Minus } from 'lucide-react';

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

export default function UpgradePage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [selectedMonths, setSelectedMonths] = useState(3);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [canceling, setCanceling] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    getSubscription()
      .then(setSubscription)
      .catch(() => setError('Không thể tải thông tin gói.'))
      .finally(() => setLoading(false));
  }, [isAuthenticated, router]);

  const handleUpgrade = async () => {
    setUpgrading(true);
    setError('');
    try {
      const updated = await upgradeToPremium(selectedMonths);
      setSubscription(updated);
      setSuccess(true);
      playSound('success');
      confetti({ particleCount: 90, spread: 70, origin: { y: 0.5 }, colors: ['#0071E3', '#1F9D55', '#D97A00', '#8E4EC6'] });
    } catch {
      setError('Nâng cấp thất bại. Vui lòng thử lại.');
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
    <main style={{ minHeight: '100vh', padding: 'clamp(24px, 5vw, 48px) var(--spacing-lg) 80px' }}>
      <div className="container" style={{ maxWidth: 920, padding: 0 }}>

        {/* Back */}
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 32 }}>
          <ArrowLeft size={16} /> Dashboard
        </Link>

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
          style={{ textAlign: 'center', marginBottom: 56 }}
        >
          <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--agen-accent)', marginBottom: 10 }}>Premium</div>
          <h1 style={{ fontSize: 'clamp(2.4rem, 6vw, 3.75rem)', letterSpacing: '-0.04em', marginBottom: 14 }}>
            Học không giới hạn.
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.15rem', maxWidth: 520, margin: '0 auto' }}>
            Mở khóa toàn bộ tiềm năng học tiếng Anh với AI Coach cá nhân và bài học không giới hạn.
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
                <CircleCheck size={18} color="var(--agen-success)" /> Bạn đang dùng AGEN Premium
              </div>
              {subscription?.current_period_end && (
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  Hết hạn: {new Date(subscription.current_period_end).toLocaleDateString('vi-VN')}
                </div>
              )}
            </div>
            <button
              className="btn btn-ghost btn-sm"
              style={{ color: 'var(--agen-secondary)' }}
              onClick={handleCancel}
              disabled={canceling}
            >
              {canceling ? 'Đang hủy…' : 'Hủy gói'}
            </button>
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
              Chào mừng đến với AGEN Premium
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
            <h3 style={{ textAlign: 'center', marginBottom: 24 }}>Chọn gói phù hợp với bạn</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 32 }}>
              {PLAN_PRICES.map((p) => {
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

            <div style={{ textAlign: 'center' }}>
              <button
                className="btn btn-primary btn-lg"
                onClick={handleUpgrade}
                disabled={upgrading}
                style={{ minWidth: 300 }}
              >
                {upgrading ? 'Đang xử lý…' : `Nâng cấp Premium · ${PLAN_PRICES.find(p => p.months === selectedMonths)?.price}`}
              </button>
            </div>
            <p style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 12 }}>
              Demo: không có thanh toán thật — chỉ dùng cho mục đích Pilot.
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
            {[
              { name: 'Miễn phí', price: '0₫ / tháng', features: FREE_FEATURES, highlight: false },
              { name: 'Premium', price: 'từ 83K₫ / tháng', features: PREMIUM_FEATURES, highlight: true },
            ].map(plan => (
              <div key={plan.name} className="card" style={{ padding: 'var(--spacing-xl)', border: plan.highlight ? '1.5px solid var(--agen-primary)' : undefined }}>
                <div style={{ marginBottom: 24 }}>
                  {plan.highlight && <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--agen-accent)', marginBottom: 4 }}>Khuyến nghị</div>}
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
