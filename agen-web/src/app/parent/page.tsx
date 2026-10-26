'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore } from '@/store/authStore';
import {
  getChildren, linkChild, unlinkChild, getChildReport,
  type ChildSummary, type ChildReport,
} from '@/lib/parentService';

const SKILL_COLORS: Record<string, string> = {
  vocabulary: 'var(--agen-accent)',
  grammar:    'var(--agen-primary)',
  reading:    'var(--skill-reading)',
  listening:  'var(--skill-listening)',
  speaking:   'var(--skill-speaking)',
  writing:    'var(--skill-writing)',
};

const SKILL_ICONS: Record<string, string> = {
  vocabulary: '📚', grammar: '📝', reading: '📖',
  listening: '🎧', speaking: '🗣️', writing: '✍️',
};

const LEVEL_COLORS: Record<string, string> = {
  PRE_A1: '#9ca3af', A1: '#60a5fa', A2: '#34d399',
  B1: '#a78bfa', B2: '#f59e0b', C1: '#f97316', C2: '#ef4444',
};

// ── Animated count-up ──────────────────────────────────────────────────────────
function AnimatedNumber({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let start = 0;
    const step = Math.ceil(value / 20);
    const timer = setInterval(() => {
      start += step;
      if (start >= value) { setDisplay(value); clearInterval(timer); }
      else setDisplay(start);
    }, 30);
    return () => clearInterval(timer);
  }, [value]);

  return <>{display}{suffix}</>;
}

// ── Link child form ────────────────────────────────────────────────────────────
function LinkChildForm({ onLinked }: { onLinked: () => void }) {
  const [code, setCode] = useState('');
  const [label, setLabel] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      await linkChild(code.trim(), label.trim() || undefined);
      setCode(''); setLabel(''); setOpen(false);
      onLinked();
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không thể liên kết.');
    } finally { setLoading(false); }
  };

  return (
    <div style={{ marginBottom: 'var(--spacing-lg)' }}>
      {!open ? (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="btn btn-outline"
          onClick={() => setOpen(true)}
          style={{ borderStyle: 'dashed', display: 'flex', alignItems: 'center', gap: 8 }}
        >
          <span style={{ fontSize: '1.2rem' }}>+</span>
          Liên kết với con
        </motion.button>
      ) : (
        <motion.form
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={submit}
          className="card"
          style={{ border: '1px dashed var(--agen-primary)' }}
        >
          <h3 style={{ marginBottom: 8 }}>🔗 Liên kết với con</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 16 }}>
            Nhập mã liên kết mà con bạn thấy trong Hồ sơ của bé (ví dụ: AGEN-7K2P).
          </p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input
              className="form-input" placeholder="AGEN-XXXX" value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              style={{ flex: '1 1 150px', textTransform: 'uppercase', letterSpacing: 2 }} required
            />
            <input
              className="form-input" placeholder="Quan hệ (bố / mẹ...)" value={label}
              onChange={(e) => setLabel(e.target.value)} style={{ flex: '1 1 140px' }}
            />
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '⏳' : 'Liên kết'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>Huỷ</button>
          </div>
          {error && <div style={{ marginTop: 12, color: 'var(--agen-secondary)', fontSize: '0.85rem' }}>⚠️ {error}</div>}
        </motion.form>
      )}
    </div>
  );
}

// ── Child report panel ──────────────────────────────────────────────────────────
function ChildReportPanel({ learnerId, childName }: { learnerId: string; childName: string }) {
  const [report, setReport] = useState<ChildReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    
    // Defer setLoading to avoid synchronous setState warning
    Promise.resolve().then(() => {
      if (active) setLoading(true);
    });
    
    getChildReport(learnerId)
      .then((r) => { if (active) { setReport(r); setLoading(false); } })
      .catch(() => { if (active) { setReport(null); setLoading(false); } });
      
    return () => { active = false; };
  }, [learnerId]);

  if (loading) return (
    <div style={{ padding: '40px 0', display: 'flex', justifyContent: 'center', gap: 12, alignItems: 'center', color: 'var(--text-muted)' }}>
      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: 'linear' }} style={{ fontSize: '1.5rem' }}>⏳</motion.div>
      Đang phân tích dữ liệu...
    </div>
  );
  if (!report) return <div style={{ padding: 20, color: 'var(--agen-secondary)', textAlign: 'center' }}>Không thể tải báo cáo.</div>;

  const kpis = [
    { label: 'Buổi học', value: report.sessions_this_week, suffix: '', emoji: '📚', color: 'var(--agen-primary-light)' },
    { label: 'XP tuần', value: report.xp_this_week, suffix: '', emoji: '⭐', color: 'var(--agen-accent)' },
    { label: 'Thời gian', value: report.study_minutes_estimate, suffix: '′', emoji: '⏱️', color: 'var(--skill-reading)' },
    { label: 'Streak', value: report.current_streak, suffix: 'd', emoji: '🔥', color: '#f97316' },
    { label: 'Chính xác', value: report.accuracy_pct, suffix: '%', emoji: '🎯', color: 'var(--agen-success)' },
  ];

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="animate-fade-in-up">

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 12, marginBottom: 32 }}>
        {kpis.map((k, i) => (
          <motion.div
            key={k.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07 }}
            style={{
              padding: '16px 12px', borderRadius: 14,
              background: 'var(--bg-elevated)',
              border: '1px solid var(--border-subtle)',
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '1.6rem', marginBottom: 4 }}>{k.emoji}</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 900, color: k.color }}>
              <AnimatedNumber value={k.value} suffix={k.suffix} />
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>{k.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Skill Bars */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontWeight: 700, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>📊</span> Hồ sơ kỹ năng của {childName}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {report.skills.map((sk, i) => {
            const color = SKILL_COLORS[sk.skill] || 'var(--agen-primary)';
            const icon = SKILL_ICONS[sk.skill] || '📌';
            return (
              <motion.div
                key={sk.skill}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.88rem' }}>
                    <span>{icon}</span>
                    <span style={{ color: 'var(--text-secondary)' }}>{sk.label}</span>
                  </div>
                  <span style={{ color, fontWeight: 800, fontSize: '0.9rem' }}>{sk.score.toFixed(0)}%</span>
                </div>
                <div style={{ height: 8, borderRadius: 99, background: 'var(--bg-base)', overflow: 'hidden' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${sk.score}%` }}
                    transition={{ duration: 0.8, delay: i * 0.06, ease: 'easeOut' }}
                    style={{ height: '100%', background: `linear-gradient(90deg, ${color}, ${color}88)`, borderRadius: 99 }}
                  />
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* AI Coach Guidance — Master Plan §21 */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ fontWeight: 700, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>🤖</span> Nhận xét từ AI Coach
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <motion.div
            initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}
            style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(6,214,160,0.06)', borderLeft: '4px solid var(--agen-success)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: '1.1rem' }}>✅</span>
              <span style={{ fontWeight: 700, color: 'var(--agen-success)', fontSize: '0.95rem' }}>Con đã tiến bộ gì?</span>
            </div>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.65, color: 'var(--text-secondary)' }}>{report.what_improved}</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}
            style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(255,152,0,0.06)', borderLeft: '4px solid var(--agen-accent)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: '1.1rem' }}>⚠️</span>
              <span style={{ fontWeight: 700, color: 'var(--agen-accent)', fontSize: '0.95rem' }}>Con cần hỗ trợ gì?</span>
            </div>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.65, color: 'var(--text-secondary)' }}>{report.what_needs_help}</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 }}
            style={{ padding: '16px 18px', borderRadius: 14, background: 'rgba(108,99,255,0.06)', borderLeft: '4px solid var(--agen-primary)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <span style={{ fontSize: '1.1rem' }}>💡</span>
              <span style={{ fontWeight: 700, color: 'var(--agen-primary-light)', fontSize: '0.95rem' }}>Phụ huynh nên làm gì?</span>
            </div>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.65, color: 'var(--text-secondary)' }}>{report.what_to_do}</div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function ParentDashboardPage() {
  const router = useRouter();
  const { isAuthenticated, logout } = useAuthStore();
  const [children, setChildren] = useState<ChildSummary[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    getChildren()
      .then((cs) => {
        setChildren(cs);
        if (cs.length && !selected) setSelected(cs[0].learner_id);
      })
      .catch(() => setChildren([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  const handleUnlink = async (id: string) => {
    await unlinkChild(id);
    if (selected === id) setSelected(null);
    load();
  };

  if (loading) return (
    <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', marginBottom: 12 }}>👨‍👩‍👧</div>
        <p style={{ color: 'var(--text-muted)' }}>Đang tải...</p>
      </div>
    </main>
  );

  const selectedChild = children.find(c => c.learner_id === selected);

  return (
    <main style={{ minHeight: '100vh', padding: 'var(--spacing-lg)', background: 'var(--bg-base)' }}>
      <div className="container" style={{ maxWidth: 820 }}>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--spacing-xl)' }}
        >
          <div>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '4px 12px', borderRadius: 99,
              background: 'rgba(108,99,255,0.12)', border: '1px solid rgba(108,99,255,0.3)',
              fontSize: '0.78rem', fontWeight: 700, color: 'var(--agen-primary-light)',
              marginBottom: 10,
            }}>
              👨‍👩‍👧 Bảng theo dõi Phụ huynh
            </div>
            <h2 style={{ margin: 0 }}>Xin chào, Phụ huynh!</h2>
            <p style={{ color: 'var(--text-muted)', marginTop: 4, fontSize: '0.9rem' }}>
              Theo dõi tiến bộ học tiếng Anh của con bạn mỗi tuần.
            </p>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => { logout(); router.push('/'); }}>
            Đăng xuất
          </button>
        </motion.div>

        {/* Link form */}
        <LinkChildForm onLinked={load} />

        {children.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card"
            style={{ textAlign: 'center', padding: '48px 24px' }}
          >
            <div style={{ fontSize: '3.5rem', marginBottom: 16 }}>👶</div>
            <div style={{ fontWeight: 700, fontSize: '1.1rem', marginBottom: 8 }}>Chưa có con nào được liên kết</div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Hãy nhập mã liên kết ở trên. Con bạn có thể tìm mã trong phần Hồ sơ trong ứng dụng.
            </p>
          </motion.div>
        ) : (
          <>
            {/* Child selector tabs */}
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 'var(--spacing-lg)' }}>
              {children.map((c) => {
                const isActive = selected === c.learner_id;
                const levelColor = LEVEL_COLORS[c.overall_level] || '#9ca3af';
                return (
                  <motion.button
                    key={c.learner_id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setSelected(c.learner_id)}
                    style={{
                      cursor: 'pointer', padding: '12px 18px',
                      display: 'flex', alignItems: 'center', gap: 12,
                      borderRadius: 14,
                      border: `2px solid ${isActive ? 'var(--agen-primary)' : 'var(--border-subtle)'}`,
                      background: isActive ? 'rgba(108,99,255,0.09)' : 'var(--bg-elevated)',
                      transition: 'all 0.2s',
                    }}
                  >
                    <div style={{ width: 40, height: 40, borderRadius: '50%', background: `${levelColor}22`, border: `2px solid ${levelColor}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.2rem' }}>
                      🧒
                    </div>
                    <div style={{ textAlign: 'left' }}>
                      <div style={{ fontWeight: 700, fontSize: '0.95rem' }}>{c.display_name}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                        <span style={{ padding: '1px 7px', borderRadius: 99, background: `${levelColor}22`, color: levelColor, fontWeight: 700 }}>{c.overall_level}</span>
                        {c.relationship_label && <span>{c.relationship_label}</span>}
                        <span style={{ color: 'var(--agen-accent)' }}>⭐ {c.total_xp} XP</span>
                      </div>
                    </div>
                  </motion.button>
                );
              })}
            </div>

            {/* Selected child report */}
            <AnimatePresence mode="wait">
              {selected && selectedChild && (
                <motion.div
                  key={selected}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="card"
                >
                  {/* Report header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1.1rem' }}>
                        📈 Báo cáo tuần — {selectedChild.display_name}
                      </h3>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 3 }}>
                        7 ngày gần nhất · {selectedChild.total_lessons_completed} bài đã hoàn thành
                        {selectedChild.current_streak > 0 && ` · 🔥 ${selectedChild.current_streak} ngày streak`}
                      </div>
                    </div>
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => handleUnlink(selected)}
                      style={{ color: 'var(--agen-secondary)', fontSize: '0.8rem' }}
                    >
                      Hủy liên kết
                    </button>
                  </div>

                  <ChildReportPanel key={selected} learnerId={selected} childName={selectedChild.display_name} />
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </div>
    </main>
  );
}
