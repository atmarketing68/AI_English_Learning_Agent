'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuthStore, useAuthHydrated } from '@/store/authStore';
import {
  getChildren, linkChild, unlinkChild, getChildReport, getParentSettings, updateParentSettings,
  type ChildSummary, type ChildReport, type ParentSettings,
} from '@/lib/parentService';
import { BookOpen, BookText, ChartColumn, CircleAlert, CircleCheck, Clock, Flame, Headphones, Lightbulb, Link2, LoaderCircle, Mail, Mic, PenLine, Plus, Sparkles, Star, Target, TriangleAlert, Users, type LucideIcon } from 'lucide-react';
import { apiErrorMessage } from '@/lib/apiError';

const tint = (color: string, pct: number) => `color-mix(in srgb, ${color} ${pct}%, transparent)`;

const SKILL_COLORS: Record<string, string> = {
  vocabulary: 'var(--agen-accent)',
  grammar:    'var(--agen-primary)',
  reading:    'var(--skill-reading)',
  listening:  'var(--skill-listening)',
  speaking:   'var(--skill-speaking)',
  writing:    'var(--skill-writing)',
};

const SKILL_ICONS: Record<string, LucideIcon> = {
  vocabulary: BookText, grammar: PenLine, reading: BookOpen,
  listening: Headphones, speaking: Mic, writing: PenLine,
};

const LEVEL_COLORS: Record<string, string> = {
  PRE_A1: 'var(--text-muted)', A1: 'var(--skill-listening)', A2: 'var(--skill-reading)',
  B1: 'var(--agen-primary)', B2: 'var(--skill-writing)', C1: 'var(--agen-accent)', C2: 'var(--agen-secondary)',
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
// ── G3 · weekly e-mail + inactivity alerts ───────────────────────────────────
function ParentEmailCard() {
  const [prefs, setPrefs] = useState<ParentSettings | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { getParentSettings().then(setPrefs).catch(() => null); }, []);
  if (!prefs) return null;
  const toggle = async () => {
    setBusy(true);
    try { setPrefs(await updateParentSettings({ weekly_report_email: !prefs.weekly_report_email })); } finally { setBusy(false); }
  };
  return (
    <div className="card" style={{ marginBottom: 'var(--spacing-lg)', display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
      <span className="icon-tile" style={{ flexShrink: 0 }}><Mail size={20} strokeWidth={1.8} /></span>
      <div style={{ flex: 1, minWidth: 220 }}>
        <div style={{ fontWeight: 600 }}>Email báo cáo tuần và cảnh báo nghỉ học</div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Chủ nhật 18h gửi báo cáo tuần của con; cảnh báo khi con nghỉ 2 ngày liên tiếp. Gửi tới {prefs.email_address}.
          {!prefs.email_available && ' (Máy chủ chưa bật gửi email.)'}
        </div>
      </div>
      <button type="button" className={`btn btn-sm ${prefs.weekly_report_email ? 'btn-outline' : 'btn-primary'}`} onClick={toggle} disabled={busy}>
        {busy ? <LoaderCircle className="animate-spin" size={14} /> : prefs.weekly_report_email ? 'Đang bật · Tắt' : 'Bật'}
      </button>
    </div>
  );
}

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
      setError(apiErrorMessage(err, 'Không thể liên kết.'));
    } finally { setLoading(false); }
  };

  return (
    <div style={{ marginBottom: 'var(--spacing-lg)' }}>
      {!open ? (
        <button
          className="btn btn-ghost"
          onClick={() => setOpen(true)}
          style={{ color: 'var(--agen-primary-light)' }}
        >
          <Plus size={16} />
          Liên kết với con
        </button>
      ) : (
        <motion.form
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          onSubmit={submit}
          className="card"
        >
          <h3 style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}><Link2 size={18} /> Liên kết với con</h3>
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
              {loading ? 'Đang liên kết…' : 'Liên kết'}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>Huỷ</button>
          </div>
          {error && <div className="alert-error" style={{ marginTop: 12 }}><CircleAlert size={16} style={{ flexShrink: 0 }} /> {error}</div>}
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
      <LoaderCircle className="animate-spin" size={20} />
      Đang phân tích dữ liệu…
    </div>
  );
  if (!report) return <div style={{ padding: 20, color: 'var(--agen-secondary)', textAlign: 'center' }}>Không thể tải báo cáo.</div>;

  const kpis = [
    { label: 'Buổi học', value: report.sessions_this_week, suffix: '', icon: BookOpen, color: 'var(--agen-primary)' },
    { label: 'XP tuần', value: report.xp_this_week, suffix: '', icon: Star, color: 'var(--agen-accent)' },
    { label: 'Phút học', value: report.study_minutes_estimate, suffix: '′', icon: Clock, color: 'var(--skill-listening)' },
    { label: 'Chuỗi ngày', value: report.current_streak, suffix: '', icon: Flame, color: 'var(--agen-secondary)' },
    { label: 'Chính xác', value: report.accuracy_pct, suffix: '%', icon: Target, color: 'var(--agen-success)' },
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
              padding: 16, borderRadius: 14,
              background: 'var(--bg-elevated)',
            }}
          >
            <k.icon size={18} strokeWidth={1.8} color={k.color} style={{ marginBottom: 10 }} />
            <div style={{ fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.02em', lineHeight: 1.1 }}>
              <AnimatedNumber value={k.value} suffix={k.suffix} />
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: 2 }}>{k.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Skill Bars */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontWeight: 600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <ChartColumn size={17} color="var(--text-secondary)" /> Hồ sơ kỹ năng của {childName}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {report.skills.map((sk, i) => {
            const color = SKILL_COLORS[sk.skill] || 'var(--agen-primary)';
            const Icon = SKILL_ICONS[sk.skill] || BookOpen;
            return (
              <motion.div
                key={sk.skill}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.88rem' }}>
                    <Icon size={15} color={color} />
                    <span style={{ color: 'var(--text-secondary)' }}>{sk.label}</span>
                  </div>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{sk.score.toFixed(0)}%</span>
                </div>
                <div className="progress-bar">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${sk.score}%` }}
                    transition={{ duration: 0.8, delay: i * 0.06, ease: 'easeOut' }}
                    style={{ height: '100%', background: color, borderRadius: 99 }}
                  />
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* AI Coach Guidance — Master Plan §21 */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ fontWeight: 600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sparkles size={17} color="var(--agen-primary)" /> Nhận xét từ AI Coach
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <motion.div
            initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}
            style={{ padding: '16px 18px', borderRadius: 14, background: 'var(--bg-elevated)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <CircleCheck size={16} color="var(--agen-success)" />
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Con đã tiến bộ gì?</span>
            </div>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.65, color: 'var(--text-secondary)' }}>{report.what_improved}</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}
            style={{ padding: '16px 18px', borderRadius: 14, background: 'var(--bg-elevated)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <TriangleAlert size={16} color="var(--agen-accent)" />
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Con cần hỗ trợ gì?</span>
            </div>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.65, color: 'var(--text-secondary)' }}>{report.what_needs_help}</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 }}
            style={{ padding: '16px 18px', borderRadius: 14, background: 'var(--bg-elevated)' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <Lightbulb size={16} color="var(--agen-primary)" />
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Phụ huynh nên làm gì?</span>
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
  const hydrated = useAuthHydrated();
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
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, isAuthenticated]);

  const handleUnlink = async (id: string) => {
    await unlinkChild(id);
    if (selected === id) setSelected(null);
    load();
  };

  if (loading) return (
    <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)' }}>
      <LoaderCircle className="animate-spin" size={20} /> Đang tải…
    </main>
  );

  const selectedChild = children.find(c => c.learner_id === selected);

  return (
    <main style={{ minHeight: '100vh', padding: 'clamp(24px, 5vw, 48px) var(--page-gutter)', background: 'var(--bg-base)' }}>
      <div className="container" style={{ padding: 0 }}>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--spacing-xl)' }}
        >
          <div>
            <div className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
              <Users size={14} /> Bảng theo dõi phụ huynh
            </div>
            <h1 style={{ margin: 0, fontSize: 'clamp(1.9rem, 4vw, 2.5rem)' }}>Xin chào, phụ huynh</h1>
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
        <ParentEmailCard />

        {children.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card"
            style={{ textAlign: 'center', padding: '48px 24px' }}
          >
            <Users size={40} strokeWidth={1.4} color="var(--text-muted)" style={{ marginBottom: 16 }} />
            <div style={{ fontWeight: 600, fontSize: '1.1rem', marginBottom: 8 }}>Chưa có con nào được liên kết</div>
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
                const levelColor = LEVEL_COLORS[c.overall_level] || 'var(--text-muted)';
                return (
                  <button
                    key={c.learner_id}
                    onClick={() => setSelected(c.learner_id)}
                    aria-pressed={isActive}
                    style={{
                      cursor: 'pointer', padding: '12px 18px', fontFamily: 'inherit', color: 'var(--text-primary)',
                      display: 'flex', alignItems: 'center', gap: 12,
                      borderRadius: 16,
                      border: `1.5px solid ${isActive ? 'var(--agen-primary)' : 'var(--border-subtle)'}`,
                      background: 'var(--bg-surface)',
                      boxShadow: isActive ? '0 0 0 3px rgba(0,113,227,0.12)' : 'none',
                      transition: 'border-color 0.2s, box-shadow 0.2s',
                    }}
                  >
                    <div style={{ width: 40, height: 40, borderRadius: '50%', background: tint(levelColor, 14), color: levelColor, display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>
                      {c.display_name.charAt(0).toUpperCase()}
                    </div>
                    <div style={{ textAlign: 'left' }}>
                      <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{c.display_name}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                        <span style={{ padding: '1px 7px', borderRadius: 99, background: tint(levelColor, 14), color: levelColor, fontWeight: 600 }}>{c.overall_level}</span>
                        {c.relationship_label && <span>{c.relationship_label}</span>}
                        <span>{c.total_xp} XP</span>
                      </div>
                    </div>
                  </button>
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
                  style={{ padding: 'var(--spacing-xl)' }}
                >
                  {/* Report header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 28 }}>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1.25rem' }}>
                        Báo cáo tuần — {selectedChild.display_name}
                      </h3>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 3 }}>
                        7 ngày gần nhất · {selectedChild.total_lessons_completed} bài đã hoàn thành
                        {selectedChild.current_streak > 0 && ` · chuỗi ${selectedChild.current_streak} ngày`}
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
