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
  { months: 12, price: '799.000₫', label: '12 tháng', badge: '⭐ Tốt nhất' },
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
      confetti({ particleCount: 200, spread: 100, origin: { y: 0.5 } });
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
    <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: 16 }}>⚡</div>
        <p style={{ color: 'var(--text-muted)' }}>Đang tải thông tin gói...</p>
      </div>
    </main>
  );

  const isPremium = subscription?.is_premium;

  return (
    <main style={{ minHeight: '100vh', padding: 'var(--spacing-lg)' }}>
      <div className="container" style={{ maxWidth: 920 }}>

        {/* Back */}
        <Link href="/dashboard" style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 32 }}>
          ← Về Dashboard
        </Link>

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ textAlign: 'center', marginBottom: 48 }}
        >
          <div style={{ fontSize: '3.5rem', marginBottom: 12 }}>⚡</div>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 900, background: 'linear-gradient(135deg, var(--agen-primary), var(--agen-accent))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: 12 }}>
            AGEN Premium
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem', maxWidth: 500, margin: '0 auto' }}>
            Mở khóa toàn bộ tiềm năng học tiếng Anh với AI Coach cá nhân và bài học không giới hạn.
          </p>
        </motion.div>

        {/* Current Plan Banner */}
        {isPremium && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            style={{
              padding: '20px 24px', marginBottom: 40, borderRadius: 16,
              background: 'linear-gradient(135deg, rgba(108,99,255,0.15), rgba(255,152,0,0.1))',
              border: '1px solid var(--agen-primary)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--agen-primary-light)' }}>
                ✅ Bạn đang dùng AGEN Premium
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
              {canceling ? '⏳' : 'Hủy gói'}
            </button>
          </motion.div>
        )}

        {/* Success Banner */}
        {success && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              padding: '20px 24px', marginBottom: 32, borderRadius: 16,
              background: 'rgba(6,214,160,0.1)', border: '1px solid var(--agen-success)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '2rem', marginBottom: 8 }}>🎉</div>
            <div style={{ fontWeight: 800, color: 'var(--agen-success)', fontSize: '1.1rem' }}>
              Chào mừng đến với AGEN Premium!
            </div>
            <p style={{ color: 'var(--text-secondary)', marginTop: 4, fontSize: '0.9rem' }}>
              Tất cả tính năng Premium đã được mở khóa. Chúc bạn học vui!
            </p>
          </motion.div>
        )}

        {error && <div style={{ padding: 12, background: 'rgba(255,107,107,0.1)', color: 'var(--agen-secondary)', marginBottom: 24, borderRadius: 10 }}>⚠️ {error}</div>}

        {/* Pricing Cards */}
        {!isPremium && (
          <div style={{ marginBottom: 48 }}>
            <h3 style={{ textAlign: 'center', marginBottom: 24, color: 'var(--text-secondary)' }}>Chọn gói phù hợp với bạn</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 32 }}>
              {PLAN_PRICES.map((p) => (
                <motion.button
                  key={p.months}
                  whileHover={{ scale: 1.02, y: -2 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setSelectedMonths(p.months)}
                  style={{
                    padding: '20px 16px', borderRadius: 16, cursor: 'pointer', textAlign: 'center',
                    border: selectedMonths === p.months ? '2px solid var(--agen-primary)' : '1px solid var(--border-medium)',
                    background: selectedMonths === p.months ? 'rgba(108,99,255,0.1)' : 'var(--bg-elevated)',
                    position: 'relative', transition: 'all 0.2s',
                  }}
                >
                  {p.badge && (
                    <div style={{
                      position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)',
                      padding: '3px 12px', borderRadius: 99, fontSize: '0.72rem', fontWeight: 700,
                      background: p.months === 12 ? 'var(--agen-accent)' : 'var(--agen-primary)',
                      color: 'white', whiteSpace: 'nowrap',
                    }}>
                      {p.badge}
                    </div>
                  )}
                  <div style={{ fontSize: '1rem', color: 'var(--text-muted)', marginBottom: 6 }}>{p.label}</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 900, color: 'var(--agen-primary-light)' }}>{p.price}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                    ~{Math.round(parseInt(p.price.replace(/\D/g, '')) / p.months / 1000)}K/tháng
                  </div>
                </motion.button>
              ))}
            </div>

            <motion.button
              className="btn btn-primary btn-lg btn-full"
              onClick={handleUpgrade}
              disabled={upgrading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              style={{
                background: 'linear-gradient(135deg, var(--agen-primary), var(--agen-accent))',
                border: 'none', fontSize: '1.1rem', fontWeight: 700, padding: '16px',
                borderRadius: 12, maxWidth: 400, margin: '0 auto', display: 'block',
              }}
            >
              {upgrading ? '⏳ Đang xử lý...' : `⚡ Nâng cấp Premium ${PLAN_PRICES.find(p => p.months === selectedMonths)?.price}`}
            </motion.button>
            <p style={{ textAlign: 'center', fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 12 }}>
              🔒 Demo: Không có thanh toán thật — Chỉ dùng cho mục đích Pilot
            </p>
          </div>
        )}

        {/* Feature Comparison */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h3 style={{ textAlign: 'center', marginBottom: 24 }}>📋 So sánh tính năng</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {/* Free column */}
            <div className="card" style={{ border: '1px solid var(--border-medium)' }}>
              <div style={{ textAlign: 'center', marginBottom: 20 }}>
                <div style={{ fontSize: '1.8rem', marginBottom: 6 }}>🆓</div>
                <div style={{ fontWeight: 800, fontSize: '1.2rem' }}>Miễn phí</div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>0₫ / tháng</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {FREE_FEATURES.map((f) => (
                  <div key={f.label} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.9rem' }}>
                    <span style={{ color: f.included ? 'var(--agen-success)' : 'var(--border-medium)', flexShrink: 0, fontSize: '1rem' }}>
                      {f.included ? '✓' : '✕'}
                    </span>
                    <span style={{ color: f.included ? 'var(--text-primary)' : 'var(--text-muted)' }}>{f.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Premium column */}
            <div className="card" style={{ border: '2px solid var(--agen-primary)', background: 'rgba(108,99,255,0.04)', position: 'relative' }}>
              <div style={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', padding: '4px 16px', borderRadius: 99, background: 'linear-gradient(135deg, var(--agen-primary), var(--agen-accent))', color: 'white', fontSize: '0.75rem', fontWeight: 700, whiteSpace: 'nowrap' }}>
                KHUYẾN NGHỊ
              </div>
              <div style={{ textAlign: 'center', marginBottom: 20 }}>
                <div style={{ fontSize: '1.8rem', marginBottom: 6 }}>⚡</div>
                <div style={{ fontWeight: 800, fontSize: '1.2rem', background: 'linear-gradient(135deg, var(--agen-primary), var(--agen-accent))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>Premium</div>
                <div style={{ color: 'var(--agen-primary-light)', fontSize: '0.85rem', fontWeight: 600 }}>từ 83K₫/tháng</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {PREMIUM_FEATURES.map((f) => (
                  <div key={f.label} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.9rem' }}>
                    <span style={{ color: 'var(--agen-success)', flexShrink: 0, fontSize: '1rem', fontWeight: 700 }}>✓</span>
                    <span style={{ color: 'var(--text-primary)', fontWeight: f.label === 'Bài học không giới hạn' ? 700 : 400 }}>{f.label}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

      </div>
    </main>
  );
}
