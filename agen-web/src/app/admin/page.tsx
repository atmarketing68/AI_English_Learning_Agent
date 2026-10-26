'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import {
  getAdminMe, getEvaluationSummary, listEvaluations,
  listContent, setContentStatus, batchGenerateContent,
  getPilotSummary,
  type EvalSummary, type EvalTraceItem, type ContentItem, type PilotSummary,
} from '@/lib/adminService';

const AGENTS = [
  'lesson', 'placement_question', 'writing_prompt', 'writing_evaluation',
  'roleplay_scenario', 'speaking_turn', 'coach_advice', 'weekly_report',
];

function scoreColor(score: number | null): string {
  if (score === null) return 'var(--text-muted)';
  if (score >= 85) return 'var(--agen-success)';
  if (score >= 70) return 'var(--agen-accent)';
  return 'var(--agen-secondary)';
}

function PilotPanel({ summary }: { summary: PilotSummary }) {
  const metrics = [
    ['Đã đăng ký', summary.registered_learners, null],
    ['Hoàn thành placement', summary.placement_completed.value, summary.placement_completed.rate],
    ['Hoàn thành bài đầu', summary.first_lesson_completed.value, summary.first_lesson_completed.rate],
    ['D7 retention', summary.d7_retention.value, summary.d7_retention.rate],
    ['Thói quen 3 ngày/tuần', summary.weekly_habit.value, summary.weekly_habit.rate],
    ['AI không bị flag', summary.ai_quality.value, summary.ai_quality.rate],
    ['Lesson generation', summary.lesson_generation.value, summary.lesson_generation.rate],
  ] as const;

  return (
    <div>
      <div style={{ marginBottom: 'var(--spacing-lg)', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
        Pilot: người học Việt Nam 15–30 tuổi, A1–B1, mục tiêu 10–15 phút mỗi ngày.
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12 }}>
        {metrics.map(([label, value, rate]) => (
          <div key={label} className="card" style={{ padding: 14 }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', minHeight: 32 }}>{label}</div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--agen-primary-light)' }}>
              {typeof value === 'number' && label === 'AI không bị flag' ? value.toFixed(1) : value}
            </div>
            {rate !== null && <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{rate}%</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Summary cards ────────────────────────────────────────────────────────────
function SummaryPanel({ summary }: { summary: EvalSummary }) {
  const cards = [
    { label: 'Đã đánh giá', value: summary.evaluated, emoji: '🔍' },
    { label: 'Điểm TB', value: summary.avg_score !== null ? summary.avg_score.toFixed(1) : '—', emoji: '📊' },
    { label: 'Bị gắn cờ', value: summary.flagged, emoji: '🚩' },
    { label: '% gắn cờ', value: `${summary.flagged_pct}%`, emoji: '⚠️' },
  ];
  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12, marginBottom: 'var(--spacing-lg)' }}>
        {cards.map((c) => (
          <div key={c.label} style={{ textAlign: 'center', padding: 16, background: 'var(--bg-elevated)', borderRadius: 10 }}>
            <div style={{ fontSize: '1.5rem' }}>{c.emoji}</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--agen-primary-light)' }}>{c.value}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{c.label}</div>
          </div>
        ))}
      </div>

      {summary.per_agent.length > 0 && (
        <div style={{ marginBottom: 'var(--spacing-lg)' }}>
          <div style={{ fontWeight: 600, marginBottom: 10 }}>🤖 Theo từng agent</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {summary.per_agent.map((a) => (
              <div key={a.agent} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.85rem', padding: '6px 10px', background: 'var(--bg-elevated)', borderRadius: 8 }}>
                <span style={{ flex: '1 1 auto', fontFamily: 'monospace' }}>{a.agent}</span>
                <span style={{ color: 'var(--text-muted)' }}>{a.total} bài</span>
                {a.flagged > 0 && <span style={{ color: 'var(--agen-secondary)' }}>🚩 {a.flagged}</span>}
                <span style={{ fontWeight: 700, color: scoreColor(a.avg_score), minWidth: 44, textAlign: 'right' }}>
                  {a.avg_score !== null ? a.avg_score.toFixed(1) : '—'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

// ── Trace table ──────────────────────────────────────────────────────────────
function TraceTable({ traces }: { traces: EvalTraceItem[] }) {
  if (traces.length === 0) {
    return <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)' }}>Chưa có đánh giá nào phù hợp bộ lọc.</div>;
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {traces.map((t) => (
        <div
          key={t.trace_id}
          className="card"
          style={{
            padding: 12,
            borderLeft: `3px solid ${t.eval_flagged ? 'var(--agen-secondary)' : 'var(--agen-success)'}`,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{t.agent}</span>
            {t.eval_flagged && <span style={{ fontSize: '0.75rem', color: 'var(--agen-secondary)' }}>🚩 cần review</span>}
            <span style={{ marginLeft: 'auto', fontWeight: 800, color: scoreColor(t.eval_score) }}>
              {t.eval_score !== null ? t.eval_score.toFixed(1) : '—'}
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{t.duration_ms.toFixed(0)}ms</span>
          </div>
          {t.eval_flags && t.eval_flags.length > 0 && (
            <ul style={{ margin: '8px 0 0', paddingLeft: 18, fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              {t.eval_flags.map((f, i) => <li key={i}>{f}</li>)}
            </ul>
          )}
          <div style={{ marginTop: 6, fontSize: '0.68rem', color: 'var(--text-muted)' }}>
            {new Date(t.created_at).toLocaleString('vi-VN')} · {t.trace_id.slice(0, 8)}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Content Factory panel ──────────────────────────────────────────────────────
const CONTENT_LEVELS = ['A1', 'A2', 'B1'];
const STATUS_LABELS: Record<string, string> = {
  draft: '📝 Nháp', approved: '✅ Đã duyệt', rejected: '❌ Từ chối',
};

function ContentPanel() {
  const [level, setLevel] = useState('A1');
  const [items, setItems] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  const load = async (lvl: string) => {
    setLoading(true);
    try {
      setItems(await listContent(lvl));
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;
    (async () => {
      setLoading(true);
      try {
        const data = await listContent(level);
        if (active) setItems(data);
      } catch {
        if (active) setItems([]);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => { active = false; };
  }, [level]);

  const handleGenerate = async (autoApprove: boolean) => {
    setBusy(true);
    setMsg('Đang sinh nội dung (mỗi bài là 1 lượt gọi AI, có thể mất vài phút)...');
    try {
      const r = await batchGenerateContent(level, autoApprove);
      setMsg(`Xong: tạo mới ${r.generated}, bỏ qua ${r.skipped}, lỗi ${r.failed}.`);
      await load(level);
    } catch {
      setMsg('Không thể sinh nội dung. Kiểm tra API key AI và quota.');
    } finally {
      setBusy(false);
    }
  };

  const handleStatus = async (code: string, status: string) => {
    try {
      const updated = await setContentStatus(code, status);
      setItems((prev) => prev.map((x) => (x.curriculum_code === code ? updated : x)));
    } catch { /* ignore */ }
  };

  const approvedCount = items.filter((i) => i.status === 'approved').length;

  return (
    <>
      <div className="card" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
        <select className="form-input" value={level} onChange={(e) => setLevel(e.target.value)} style={{ flex: '0 0 120px' }}>
          {CONTENT_LEVELS.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <button className="btn btn-ghost btn-sm" disabled={busy} onClick={() => handleGenerate(false)}>
          ⚙️ Sinh (nháp)
        </button>
        <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => handleGenerate(true)}>
          ⚡ Sinh + duyệt tự động
        </button>
        <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {approvedCount}/{items.length} đã duyệt
        </span>
      </div>

      {msg && <div className="card" style={{ marginBottom: 'var(--spacing-md)', fontSize: '0.85rem' }}>{msg}</div>}

      {loading ? (
        <div style={{ padding: 30, textAlign: 'center', color: 'var(--text-muted)' }}>⏳ Đang tải...</div>
      ) : items.length === 0 ? (
        <div className="card" style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)' }}>
          Chưa có nội dung cho cấp {level}. Bấm &quot;Sinh + duyệt tự động&quot; để tạo.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {items.map((it) => (
            <div key={it.curriculum_code} className="card" style={{ padding: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{it.curriculum_code}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{it.skill} · {it.topic}</span>
                {it.eval_flagged && <span style={{ fontSize: '0.72rem', color: 'var(--agen-secondary)' }}>🚩</span>}
                <span style={{ marginLeft: 'auto', fontWeight: 700, color: scoreColor(it.eval_score) }}>
                  {it.eval_score !== null ? it.eval_score.toFixed(1) : '—'}
                </span>
                <span style={{ fontSize: '0.72rem' }}>{STATUS_LABELS[it.status] || it.status}</span>
              </div>
              <div style={{ marginTop: 8, display: 'flex', gap: 6 }}>
                {it.status !== 'approved' && (
                  <button className="btn btn-ghost btn-sm" style={{ fontSize: '0.72rem', color: 'var(--agen-success)' }} onClick={() => handleStatus(it.curriculum_code, 'approved')}>
                    ✅ Duyệt
                  </button>
                )}
                {it.status !== 'rejected' && (
                  <button className="btn btn-ghost btn-sm" style={{ fontSize: '0.72rem', color: 'var(--agen-secondary)' }} onClick={() => handleStatus(it.curriculum_code, 'rejected')}>
                    ❌ Từ chối
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}


// ── Page ──────────────────────────────────────────────────────────────────────
export default function AdminDashboardPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [authorized, setAuthorized] = useState<boolean | null>(null);
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [traces, setTraces] = useState<EvalTraceItem[]>([]);
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [agent, setAgent] = useState('');
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'pilot' | 'quality' | 'content'>('pilot');
  const [pilotSummary, setPilotSummary] = useState<PilotSummary | null>(null);

  // Access check
  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    getAdminMe()
      .then((me) => setAuthorized(me.is_admin))
      .catch(() => setAuthorized(false));
  }, [isAuthenticated, router]);

  // Load data once authorized / filters change
  useEffect(() => {
    if (authorized !== true) return;
    let active = true;
    const load = async () => {
      try {
        const [p, s, t] = await Promise.all([
          getPilotSummary(),
          getEvaluationSummary(),
          listEvaluations({ flaggedOnly, agent: agent || undefined, limit: 100 }),
        ]);
        if (active) { setPilotSummary(p); setSummary(s); setTraces(t); }
      } catch {
        if (active) { setPilotSummary(null); setSummary(null); setTraces([]); }
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => { active = false; };
  }, [authorized, flaggedOnly, agent]);

  if (authorized === null) {
    return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}><div style={{ fontSize: '2rem' }}>🛡️</div><p>Đang kiểm tra quyền...</p></div>
      </main>
    );
  }

  if (authorized === false) {
    return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
        <div className="card" style={{ textAlign: 'center', padding: 40, maxWidth: 420 }}>
          <div style={{ fontSize: '2.5rem', marginBottom: 12 }}>🔒</div>
          <h3 style={{ marginBottom: 8 }}>Không có quyền truy cập</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Trang này chỉ dành cho quản trị viên chất lượng AI.
          </p>
          <button className="btn btn-ghost btn-sm" style={{ marginTop: 16 }} onClick={() => router.push('/dashboard')}>
            ← Về trang chính
          </button>
        </div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: '100vh', padding: 'var(--spacing-lg)' }}>
      <div className="container" style={{ maxWidth: 820 }}>

        <div className="animate-fade-in-up" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <h2 style={{ margin: 0 }}>🛡️ Quản trị AGEN</h2>
          <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
            Giám sát chất lượng AI và quản lý kho nội dung bài học (Master Plan §29 / Content Factory)
          </p>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 'var(--spacing-lg)' }}>
          <button
            className="btn btn-sm"
            onClick={() => setTab('pilot')}
            style={{ background: tab === 'pilot' ? 'var(--agen-primary)' : 'transparent', border: '1px solid var(--border-subtle)' }}
          >
            📈 Pilot KPI
          </button>
          <button
            className="btn btn-sm"
            onClick={() => setTab('quality')}
            style={{ background: tab === 'quality' ? 'var(--agen-primary)' : 'transparent', border: '1px solid var(--border-subtle)' }}
          >
            🔍 Chất lượng AI
          </button>
          <button
            className="btn btn-sm"
            onClick={() => setTab('content')}
            style={{ background: tab === 'content' ? 'var(--agen-primary)' : 'transparent', border: '1px solid var(--border-subtle)' }}
          >
            📚 Kho nội dung
          </button>
        </div>

        {tab === 'pilot' ? (
          pilotSummary ? <div className="card"><PilotPanel summary={pilotSummary} /></div> : <div className="card">Chưa có dữ liệu pilot.</div>
        ) : tab === 'content' ? (
          <ContentPanel />
        ) : (
          <>
            {/* Filters */}
            <div className="card" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={flaggedOnly} onChange={(e) => setFlaggedOnly(e.target.checked)} />
                Chỉ hiện bị gắn cờ 🚩
              </label>
              <select
                className="form-input"
                value={agent}
                onChange={(e) => setAgent(e.target.value)}
                style={{ flex: '1 1 200px' }}
              >
                <option value="">Tất cả agent</option>
                {AGENTS.map((a) => <option key={a} value={a}>{a}</option>)}
              </select>
            </div>

            {loading ? (
              <div style={{ padding: 30, textAlign: 'center', color: 'var(--text-muted)' }}>⏳ Đang tải dữ liệu...</div>
            ) : (
              <>
                {summary && (
                  <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
                    <SummaryPanel summary={summary} />
                  </div>
                )}
                <div style={{ fontWeight: 600, marginBottom: 10 }}>
                  📋 Nhật ký đánh giá ({traces.length})
                </div>
                <TraceTable traces={traces} />
              </>
            )}
          </>
        )}
      </div>
    </main>
  );
}
