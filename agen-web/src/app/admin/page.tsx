'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useAuthHydrated } from '@/store/authStore';
import {
  getAdminMe, getEvaluationSummary, listEvaluations,
  listContent, setContentStatus, batchGenerateContent,
  getPilotSummary, getRevenueSummary, listOrders, markInvoiceIssued,
  deleteGeneratedExam, generateExam, getGeneratedExam, listGeneratedExams, setGeneratedExamStatus,
  type AdminOrder, type GeneratedExam, type EvalSummary, type EvalTraceItem, type ContentItem, type PilotSummary, type RevenueSummary,
} from '@/lib/adminService';
import { ArrowLeft, Check, Flag, LoaderCircle, Lock, Settings, ShieldCheck, X, Zap } from 'lucide-react';

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
          <div key={label} style={{ padding: 14, background: 'var(--bg-elevated)', borderRadius: 14 }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', minHeight: 32 }}>{label}</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.02em' }}>
              {typeof value === 'number' && label === 'AI không bị flag' ? value.toFixed(1) : value}
            </div>
            {rate !== null && <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{rate}%</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── G5 · Doanh thu & chuyển đổi ──────────────────────────────────────────────
const vnd = (n: number) => n.toLocaleString('vi-VN') + '₫';

function RevenuePanel({ r }: { r: RevenueSummary }) {
  const max = Math.max(1, ...r.by_month.map(b => b.revenue_vnd));
  const kpis: [string, string | number, string][] = [
    ['Doanh thu (đơn đã trả)', vnd(r.total_vnd), `${r.paid_orders} đơn · ${r.pending_orders} chờ · ${r.failed_orders} lỗi`],
    ['Premium đang hoạt động', r.active_premium, 'tài khoản học viên trả phí'],
    ['Gói gia đình', r.active_family, 'phụ huynh đang trả phí'],
    ['Dùng thử → trả phí', `${r.trial_conversion_pct}%`, `${r.trials_converted}/${r.trials_started} tài khoản dùng thử`],
    ['Học thử → đăng ký', r.guests_claimed, `${r.guests_now} khách chưa lưu tài khoản`],
    ['Học viên đã đăng ký', r.registered_learners, 'không tính khách'],
  ];
  return (
    <div className="card">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12, marginBottom: 24 }}>
        {kpis.map(([label, value, sub]) => (
          <div key={label} style={{ padding: 14, background: 'var(--bg-elevated)', borderRadius: 14 }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', minHeight: 32 }}>{label}</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 600, letterSpacing: '-0.02em' }}>{value}</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{sub}</div>
          </div>
        ))}
      </div>
      <div style={{ fontWeight: 600, marginBottom: 10 }}>Doanh thu 6 tháng gần nhất</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 8, alignItems: 'end', height: 140, marginBottom: 24 }}>
        {r.by_month.map(b => (
          <div key={b.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, height: '100%', justifyContent: 'flex-end' }} title={`${b.label}: ${vnd(b.revenue_vnd)} · ${b.orders} đơn`}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', fontVariantNumeric: 'tabular-nums' }}>{b.revenue_vnd ? Math.round(b.revenue_vnd / 1000) + 'K' : ''}</div>
            <div style={{ width: '70%', height: `${Math.max(4, (b.revenue_vnd / max) * 100)}%`, borderRadius: 6, background: b.revenue_vnd ? 'linear-gradient(180deg, var(--skill-listening), var(--agen-primary))' : 'var(--bg-glass-hover)' }} />
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{b.label}</div>
          </div>
        ))}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
        {[['Theo cổng', r.by_provider], ['Theo gói', r.by_plan]].map(([title, rows]) => (
          <div key={title as string}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>{title as string}</div>
            {(rows as RevenueSummary['by_plan']).length === 0 && <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Chưa có đơn nào.</div>}
            {(rows as RevenueSummary['by_plan']).map(b => (
              <div key={b.key} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderTop: '1px solid var(--border-subtle)', fontSize: '0.88rem' }}>
                <span>{b.label} <span style={{ color: 'var(--text-muted)' }}>· {b.orders} đơn</span></span><strong>{vnd(b.revenue_vnd)}</strong>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── G8 · Đơn hàng & hoá đơn VAT ──────────────────────────────────────────────
const PLAN_VI: Record<string, string> = { premium: 'Premium', family: 'Gia đình', team: 'Doanh nghiệp' };

function OrdersPanel() {
  const [orders, setOrders] = useState<AdminOrder[] | null>(null);
  const [invoiceOnly, setInvoiceOnly] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  useEffect(() => { listOrders(invoiceOnly, 200).then(setOrders).catch(() => setOrders([])); }, [invoiceOnly]);

  const toggle = async (o: AdminOrder) => {
    setBusy(o.order_id);
    try {
      const updated = await markInvoiceIssued(o.order_id, !o.invoice_issued_at);
      setOrders(list => (list ? list.map(x => (x.order_id === o.order_id ? updated : x)) : list));
    } finally { setBusy(null); }
  };
  const exportCsv = () => {
    if (!orders) return;
    const head = ['Ngày', 'Email', 'Gói', 'Tháng', 'Ghế', 'Số tiền', 'Cổng', 'Trạng thái', 'Tên đơn vị', 'MST', 'Địa chỉ', 'Email HĐ', 'Đã xuất HĐ'];
    const rows = orders.map(o => [new Date(o.created_at).toLocaleDateString('vi-VN'), o.email ?? '', PLAN_VI[o.plan] ?? o.plan, o.months, o.seats, o.amount_vnd, o.provider, o.status,
      o.invoice?.company_name ?? '', o.invoice?.tax_code ?? '', o.invoice?.address ?? '', o.invoice?.email ?? '', o.invoice_issued_at ? 'x' : '']);
    const csv = '\ufeff' + [head, ...rows].map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const a = document.createElement('a'); a.href = url; a.download = 'don-hang-hoa-don.csv'; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <div className="card" style={{ marginTop: 'var(--spacing-lg)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
        <div style={{ fontWeight: 600, flex: 1 }}>Đơn hàng & hoá đơn VAT</div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', cursor: 'pointer' }}>
          <input type="checkbox" checked={invoiceOnly} onChange={e => setInvoiceOnly(e.target.checked)} /> Chỉ đơn yêu cầu hoá đơn
        </label>
        <button type="button" className="btn btn-ghost btn-sm" onClick={exportCsv} disabled={!orders?.length}>Tải CSV</button>
      </div>
      {!orders ? <div style={{ color: 'var(--text-muted)' }}>Đang tải…</div> : orders.length === 0 ? <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Chưa có đơn nào.</div> : (
        <div style={{ overflowX: 'auto', margin: '0 calc(-1 * var(--spacing-lg, 24px))', padding: '0 var(--spacing-lg, 24px)' }}>
          <table className="teacher-table" style={{ minWidth: 980 }}>
            <thead><tr><th>Ngày</th><th>Khách</th><th>Gói</th><th>Số tiền</th><th>Trạng thái</th><th>Đơn vị · MST</th><th>Email HĐ</th><th>Hoá đơn</th></tr></thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.order_id}>
                  <td>{new Date(o.created_at).toLocaleDateString('vi-VN')}</td>
                  <td>{o.email}</td>
                  <td>{PLAN_VI[o.plan] ?? o.plan} · {o.months} th{o.plan === 'team' ? ` · ${o.seats} ghế` : ''}</td>
                  <td>{vnd(o.amount_vnd)}</td>
                  <td><span className={`plan-chip${o.status === 'paid' ? ' is-premium' : ''}`}>{o.status === 'paid' ? 'Đã trả' : o.status === 'pending' ? 'Chờ' : 'Lỗi'}</span></td>
                  <td style={{ whiteSpace: 'normal', minWidth: 200 }}>{o.invoice ? <>{o.invoice.company_name}<div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>MST {o.invoice.tax_code} · {o.invoice.address}</div></> : <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                  <td>{o.invoice?.email ?? '—'}</td>
                  <td>{o.invoice ? <button type="button" className={`btn btn-sm ${o.invoice_issued_at ? 'btn-ghost' : 'btn-primary'}`} disabled={busy === o.order_id || o.status !== 'paid'} onClick={() => toggle(o)} title={o.status !== 'paid' ? 'Chỉ xuất khi đơn đã thanh toán' : ''}>{o.invoice_issued_at ? <><Check size={13} /> Đã xuất</> : 'Đánh dấu đã xuất'}</button> : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── G9 · Đề thi thử do AI sinh ────────────────────────────────────────────────
function ExamsPanel() {
  const [items, setItems] = useState<GeneratedExam[] | null>(null);
  const [form, setForm] = useState({ exam: 'ielts' as 'ielts' | 'toeic', skill: 'reading' as 'listening' | 'reading', topic: '', level: 'B1' });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');
  const [preview, setPreview] = useState<Awaited<ReturnType<typeof getGeneratedExam>> | null>(null);
  const load = () => listGeneratedExams().then(setItems).catch(() => setItems([]));
  useEffect(() => { void load(); }, []);

  const generate = async () => {
    setBusy(true); setMsg('Đang sinh đề (1 lượt gọi AI, 30–60 giây)…');
    try {
      const r = await generateExam({ exam: form.exam, skill: form.skill, topic: form.topic || undefined, level: form.level });
      setMsg(`Đã tạo bản nháp "${r.title}" (${r.questions} câu). Xem và duyệt bên dưới.`);
      await load();
    } catch (err: unknown) {
      setMsg((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không sinh được đề.');
    } finally { setBusy(false); }
  };
  const setStatus = async (id: string, status: 'draft' | 'approved' | 'rejected') => { await setGeneratedExamStatus(id, status); await load(); if (preview?.meta.id === id) setPreview(null); };
  const STATUS_VI = { draft: 'Nháp', approved: 'Đã duyệt', rejected: 'Từ chối' } as const;

  return (
    <div style={{ display: 'grid', gap: 'var(--spacing-lg)' }}>
      <div className="card" style={{ display: 'grid', gap: 10 }}>
        <div style={{ fontWeight: 600 }}>Sinh đề thi thử mới bằng AI</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 8 }}>
          <select className="form-input" value={form.exam} onChange={e => setForm(f => ({ ...f, exam: e.target.value as 'ielts' | 'toeic' }))} aria-label="Kỳ thi"><option value="ielts">IELTS</option><option value="toeic">TOEIC</option></select>
          <select className="form-input" value={form.skill} onChange={e => setForm(f => ({ ...f, skill: e.target.value as 'listening' | 'reading' }))} aria-label="Kỹ năng"><option value="reading">Reading</option><option value="listening">Listening</option></select>
          <select className="form-input" value={form.level} onChange={e => setForm(f => ({ ...f, level: e.target.value }))} aria-label="Trình độ">{['A2', 'B1', 'B2', 'C1'].map(l => <option key={l} value={l}>{l}</option>)}</select>
          <input className="form-input" placeholder="Chủ đề (tuỳ chọn)" value={form.topic} onChange={e => setForm(f => ({ ...f, topic: e.target.value }))} maxLength={120} />
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-primary btn-sm" onClick={generate} disabled={busy}>{busy ? <LoaderCircle className="animate-spin" size={14} /> : <Zap size={14} />} Sinh bản nháp</button>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{msg || 'Đề mới ở trạng thái nháp; học viên chỉ thấy đề đã duyệt.'}</span>
        </div>
      </div>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {!items ? <div style={{ padding: 16, color: 'var(--text-muted)' }}>Đang tải…</div> : items.length === 0 ? <div style={{ padding: 16, color: 'var(--text-muted)', fontSize: '0.88rem' }}>Chưa có đề nào do AI sinh.</div> : (
          <div style={{ overflowX: 'auto' }}>
            <table className="teacher-table">
              <thead><tr><th>Đề</th><th>Kỳ thi</th><th>Câu</th><th>Chất lượng AI</th><th>Trạng thái</th><th>Ngày</th><th /></tr></thead>
              <tbody>
                {items.map(x => (
                  <tr key={x.id}>
                    <td style={{ whiteSpace: 'normal', minWidth: 200 }}><button type="button" className="btn btn-ghost btn-sm" style={{ padding: 0 }} onClick={async () => setPreview(await getGeneratedExam(x.id))}>{x.title}</button></td>
                    <td>{x.exam.toUpperCase()} {x.skill}</td>
                    <td>{x.questions}</td>
                    <td>{x.eval_score != null ? `${x.eval_score.toFixed(0)}${x.eval_flagged ? ' ⚑' : ''}` : '—'}</td>
                    <td><span className={`plan-chip${x.status === 'approved' ? ' is-premium' : ''}`}>{STATUS_VI[x.status]}</span></td>
                    <td>{new Date(x.created_at).toLocaleDateString('vi-VN')}</td>
                    <td style={{ display: 'flex', gap: 6 }}>
                      {x.status !== 'approved' && <button type="button" className="btn btn-primary btn-sm" onClick={() => setStatus(x.id, 'approved')}><Check size={13} /> Duyệt</button>}
                      {x.status !== 'rejected' && <button type="button" className="btn btn-ghost btn-sm" onClick={() => setStatus(x.id, 'rejected')}><X size={13} /> Từ chối</button>}
                      <button type="button" className="icon-btn" aria-label="Xoá" onClick={async () => { if (confirm('Xoá đề này?')) { await deleteGeneratedExam(x.id); await load(); } }}><X size={14} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {preview && (
        <div className="card" style={{ display: 'grid', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <div><div className="eyebrow">Xem trước · có đáp án</div><h3 style={{ margin: 0 }}>{preview.meta.title}</h3></div>
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setPreview(null)}>Đóng</button>
          </div>
          {preview.paper.sections.map((sec, si) => (
            <div key={si} style={{ display: 'grid', gap: 8 }}>
              <div style={{ fontWeight: 600 }}>{sec.title}</div>
              <div style={{ fontSize: '0.85rem', fontStyle: 'italic', color: 'var(--text-secondary)' }}>{sec.instructions}</div>
              {sec.passage && <div className="exam-passage" style={{ maxHeight: 260 }}>{sec.passage}</div>}
              {sec.audio && <details className="exam-transcript"><summary>Lời thoại ({sec.audio.length} dòng)</summary>{sec.audio.map((l, i) => <p key={i}><b>{l.speaker}:</b> {l.text}</p>)}</details>}
              {sec.questions.map(q => (
                <div key={q.id} style={{ fontSize: '0.88rem', padding: '6px 10px', borderRadius: 10, background: 'var(--bg-elevated)' }}>
                  <b>{q.id}.</b> {q.prompt}
                  {q.options && <div style={{ color: 'var(--text-muted)' }}>{q.options.map((o, i) => <span key={i} style={{ marginRight: 10, fontWeight: i === q.answer ? 700 : 400, color: i === q.answer ? 'var(--agen-success)' : undefined }}>{String.fromCharCode(65 + i)}. {o}</span>)}</div>}
                  {Array.isArray(q.answer) && <div style={{ color: 'var(--agen-success)' }}>Đáp án: {q.answer.join(' / ')}</div>}
                  <div style={{ color: 'var(--text-muted)' }}>{q.explanation_vi}</div>
                </div>
              ))}
            </div>
          ))}
          <div style={{ display: 'flex', gap: 8 }}>
            {preview.meta.status !== 'approved' && <button type="button" className="btn btn-primary btn-sm" onClick={() => setStatus(preview.meta.id, 'approved')}><Check size={13} /> Duyệt và phát hành</button>}
            <button type="button" className="btn btn-ghost btn-sm" onClick={() => setStatus(preview.meta.id, 'rejected')}><X size={13} /> Từ chối</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Summary cards ────────────────────────────────────────────────────────────
function SummaryPanel({ summary }: { summary: EvalSummary }) {
  const cards = [
    { label: 'Đã đánh giá', value: summary.evaluated },
    { label: 'Điểm TB', value: summary.avg_score !== null ? summary.avg_score.toFixed(1) : '—' },
    { label: 'Bị gắn cờ', value: summary.flagged },
    { label: '% gắn cờ', value: `${summary.flagged_pct}%` },
  ];
  return (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12, marginBottom: 'var(--spacing-lg)' }}>
        {cards.map((c) => (
          <div key={c.label} style={{ padding: 16, background: 'var(--bg-elevated)', borderRadius: 14 }}>
            <div style={{ fontSize: '1.5rem', fontWeight: 600, letterSpacing: '-0.02em' }}>{c.value}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{c.label}</div>
          </div>
        ))}
      </div>

      {summary.per_agent.length > 0 && (
        <div style={{ marginBottom: 'var(--spacing-lg)' }}>
          <div style={{ fontWeight: 600, marginBottom: 10 }}>Theo từng agent</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {summary.per_agent.map((a) => (
              <div key={a.agent} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.85rem', padding: '8px 12px', background: 'var(--bg-elevated)', borderRadius: 10 }}>
                <span style={{ flex: '1 1 auto', fontFamily: 'var(--font-mono)' }}>{a.agent}</span>
                <span style={{ color: 'var(--text-muted)' }}>{a.total} bài</span>
                {a.flagged > 0 && <span style={{ color: 'var(--agen-secondary)', display: 'inline-flex', alignItems: 'center', gap: 4 }}><Flag size={12} /> {a.flagged}</span>}
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
            padding: 14,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span style={{ width: 8, height: 8, borderRadius: 99, background: t.eval_flagged ? 'var(--agen-secondary)' : 'var(--agen-success)', flexShrink: 0 }} />
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500, fontSize: '0.9rem' }}>{t.agent}</span>
            {t.eval_flagged && <span style={{ fontSize: '0.75rem', color: 'var(--agen-secondary)', display: 'inline-flex', alignItems: 'center', gap: 4 }}><Flag size={12} /> cần review</span>}
            <span style={{ marginLeft: 'auto', fontWeight: 600, color: scoreColor(t.eval_score) }}>
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
  draft: 'Nháp', approved: 'Đã duyệt', rejected: 'Từ chối',
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
          <Settings size={14} /> Sinh (nháp)
        </button>
        <button className="btn btn-primary btn-sm" disabled={busy} onClick={() => handleGenerate(true)}>
          <Zap size={14} /> Sinh + duyệt tự động
        </button>
        <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          {approvedCount}/{items.length} đã duyệt
        </span>
      </div>

      {msg && <div className="card" style={{ marginBottom: 'var(--spacing-md)', fontSize: '0.85rem' }}>{msg}</div>}

      {loading ? (
        <div style={{ padding: 30, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8, color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={18} /> Đang tải…</div>
      ) : items.length === 0 ? (
        <div className="card" style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)' }}>
          Chưa có nội dung cho cấp {level}. Bấm &quot;Sinh + duyệt tự động&quot; để tạo.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {items.map((it) => (
            <div key={it.curriculum_code} className="card" style={{ padding: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500, fontSize: '0.9rem' }}>{it.curriculum_code}</span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{it.skill} · {it.topic}</span>
                {it.eval_flagged && <Flag size={12} color="var(--agen-secondary)" />}
                <span style={{ marginLeft: 'auto', fontWeight: 600, color: scoreColor(it.eval_score) }}>
                  {it.eval_score !== null ? it.eval_score.toFixed(1) : '—'}
                </span>
                <span className="xp-badge" style={{ fontSize: '0.72rem', padding: '2px 8px', color: it.status === 'approved' ? 'var(--agen-success)' : it.status === 'rejected' ? 'var(--agen-secondary)' : undefined }}>{STATUS_LABELS[it.status] || it.status}</span>
              </div>
              <div style={{ marginTop: 8, display: 'flex', gap: 6 }}>
                {it.status !== 'approved' && (
                  <button className="btn btn-ghost btn-sm" style={{ fontSize: '0.72rem', color: 'var(--agen-success)' }} onClick={() => handleStatus(it.curriculum_code, 'approved')}>
                    <Check size={13} /> Duyệt
                  </button>
                )}
                {it.status !== 'rejected' && (
                  <button className="btn btn-ghost btn-sm" style={{ fontSize: '0.72rem', color: 'var(--agen-secondary)' }} onClick={() => handleStatus(it.curriculum_code, 'rejected')}>
                    <X size={13} /> Từ chối
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
  const hydrated = useAuthHydrated();
  const [authorized, setAuthorized] = useState<boolean | null>(null);
  const [summary, setSummary] = useState<EvalSummary | null>(null);
  const [traces, setTraces] = useState<EvalTraceItem[]>([]);
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [agent, setAgent] = useState('');
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'pilot' | 'revenue' | 'quality' | 'content' | 'exams'>('pilot');
  const [pilotSummary, setPilotSummary] = useState<PilotSummary | null>(null);
  const [revenue, setRevenue] = useState<RevenueSummary | null>(null);

  // Access check
  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getAdminMe()
      .then((me) => setAuthorized(me.is_admin))
      .catch(() => setAuthorized(false));
  }, [hydrated, isAuthenticated, router]);

  // Load data once authorized / filters change
  useEffect(() => {
    if (authorized !== true) return;
    let active = true;
    const load = async () => {
      try {
        const [p, s, t, rv] = await Promise.all([
          getPilotSummary(),
          getEvaluationSummary(),
          listEvaluations({ flaggedOnly, agent: agent || undefined, limit: 100 }),
          getRevenueSummary().catch(() => null),
        ]);
        if (active) { setPilotSummary(p); setSummary(s); setTraces(t); setRevenue(rv); }
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
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)' }}>
        <LoaderCircle className="animate-spin" size={20} /> Đang kiểm tra quyền…
      </main>
    );
  }

  if (authorized === false) {
    return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
        <div className="card" style={{ textAlign: 'center', padding: 40, maxWidth: 420 }}>
          <Lock size={36} strokeWidth={1.5} color="var(--text-muted)" style={{ marginBottom: 12 }} />
          <h3 style={{ marginBottom: 8 }}>Không có quyền truy cập</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Trang này chỉ dành cho quản trị viên chất lượng AI.
          </p>
          <button className="btn btn-ghost btn-sm" style={{ marginTop: 16 }} onClick={() => router.push('/dashboard')}>
            <ArrowLeft size={14} /> Về trang chính
          </button>
        </div>
      </main>
    );
  }

  return (
    <main style={{ minHeight: '100vh', padding: 'clamp(24px, 5vw, 48px) var(--page-gutter)' }}>
      <div className="container" style={{ padding: 0 }}>

        <div className="animate-fade-in-up" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <h1 style={{ margin: 0, fontSize: 'clamp(1.9rem, 4vw, 2.5rem)', display: 'flex', alignItems: 'center', gap: 10 }}><ShieldCheck size={28} strokeWidth={1.8} /> Quản trị AI AGENT ENGLISH</h1>
          <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
            Giám sát chất lượng AI và quản lý kho nội dung bài học (Master Plan §29 / Content Factory)
          </p>
        </div>

        {/* Tabs */}
        <div className="segmented" style={{ marginBottom: 'var(--spacing-lg)' }}>
          <button onClick={() => setTab('pilot')} aria-pressed={tab === 'pilot'}>Pilot KPI</button>
          <button onClick={() => setTab('revenue')} aria-pressed={tab === 'revenue'}>Doanh thu</button>
          <button onClick={() => setTab('quality')} aria-pressed={tab === 'quality'}>Chất lượng AI</button>
          <button onClick={() => setTab('content')} aria-pressed={tab === 'content'}>Kho nội dung</button>
          <button onClick={() => setTab('exams')} aria-pressed={tab === 'exams'}>Đề thi</button>
        </div>

        {tab === 'pilot' ? (
          pilotSummary ? <div className="card"><PilotPanel summary={pilotSummary} /></div> : <div className="card">Chưa có dữ liệu pilot.</div>
        ) : tab === 'revenue' ? (
          <>{revenue ? <RevenuePanel r={revenue} /> : <div className="card">Chưa có dữ liệu doanh thu.</div>}<OrdersPanel /></>
        ) : tab === 'content' ? (
          <ContentPanel />
        ) : tab === 'exams' ? (
          <ExamsPanel />
        ) : (
          <>
            {/* Filters */}
            <div className="card" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={flaggedOnly} onChange={(e) => setFlaggedOnly(e.target.checked)} />
                Chỉ hiện bị gắn cờ
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
              <div style={{ padding: 30, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8, color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={18} /> Đang tải dữ liệu…</div>
            ) : (
              <>
                {summary && (
                  <div className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
                    <SummaryPanel summary={summary} />
                  </div>
                )}
                <div style={{ fontWeight: 600, marginBottom: 10 }}>
                  Nhật ký đánh giá ({traces.length})
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
