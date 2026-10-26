'use client';

/** G9 · Kế hoạch ôn thi: đặt ngày thi + band mục tiêu, xem điểm hiện tại, tuần nào học gì, có đúng tiến độ không. */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, CalendarDays, CircleAlert, LoaderCircle, Target, Trash2 } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { EXAM_LABEL, type ExamKind } from '@/lib/examsService';
import { STATUS_COLOR, STATUS_LABEL, clearStudyPlan, formatTarget, getStudyPlan, setStudyPlan, type PlanSkill, type StudyPlan } from '@/lib/studyPlanService';
import { PageSkeleton } from '@/components/Skeleton';
import Mascot from '@/components/ui/Mascot';
import { track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

const SKILL_LINK: Record<PlanSkill, string> = { listening: '/exams', reading: '/exams', writing: '/practice/writing', speaking: '/exams' };

function TargetForm({ plan, onSaved }: { plan: StudyPlan; onSaved: (p: StudyPlan) => void }) {
  const [exam, setExam] = useState<ExamKind>(plan.exam ?? 'ielts');
  const [score, setScore] = useState<string>(plan.target_score != null ? String(plan.target_score) : exam === 'ielts' ? '6.5' : '650');
  const [date, setDate] = useState<string>(plan.exam_date ?? '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [minDate] = useState(() => new Date(Date.now() + 86_400_000).toISOString().slice(0, 10));
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError('');
    try {
      onSaved(await setStudyPlan(exam, Number(score), date));
      track('study_plan_set', { exam, target: Number(score) });
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Không lưu được kế hoạch.'));
    } finally { setBusy(false); }
  };
  return (
    <form onSubmit={submit} className="card" style={{ display: 'grid', gap: 12 }}>
      <div className="segmented">
        {(['ielts', 'toeic'] as ExamKind[]).map(k => <button key={k} type="button" aria-pressed={exam === k} onClick={() => { setExam(k); setScore(k === 'ielts' ? '6.5' : '650'); }}>{EXAM_LABEL[k]}</button>)}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
        <label className="profile-field"><span>{exam === 'ielts' ? 'Band mục tiêu' : 'Điểm mục tiêu'}</span>
          {exam === 'ielts'
            ? <select className="form-input" value={score} onChange={e => setScore(e.target.value)}>{Array.from({ length: 11 }, (_, i) => (4 + i * 0.5).toFixed(1)).map(v => <option key={v} value={v}>{v}</option>)}</select>
            : <select className="form-input" value={score} onChange={e => setScore(e.target.value)}>{[450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950].map(v => <option key={v} value={v}>{v}</option>)}</select>}
        </label>
        <label className="profile-field"><span>Ngày thi</span><input className="form-input" type="date" min={minDate} value={date} onChange={e => setDate(e.target.value)} required /></label>
      </div>
      {error && <div className="alert-error"><CircleAlert size={16} /> {error}</div>}
      <button type="submit" className="btn btn-primary" disabled={busy || !date}>{busy ? <LoaderCircle className="animate-spin" size={16} /> : <Target size={16} />} {plan.configured ? 'Cập nhật kế hoạch' : 'Lập kế hoạch'}</button>
    </form>
  );
}

export default function PlanPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getStudyPlan().then(setPlan).catch(() => setError('Không tải được kế hoạch.'));
  }, [hydrated, isAuthenticated, router]);

  if (!plan) return <main className="friends-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={2} />}</main>;
  const showForm = !plan.configured || editing;
  const skills = (['listening', 'reading', 'writing', 'speaking'] as PlanSkill[]);

  return (
    <main className="friends-page">
      <div className="friends-column" style={{ maxWidth: 760 }}>
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Trang chủ</Link>
        <section className="card friends-hero">
          <span className="icon-tile" style={{ width: 56, height: 56, borderRadius: 18, background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}><CalendarDays size={28} strokeWidth={1.7} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow">Kế hoạch ôn thi</div>
            <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>
              {plan.configured ? `${EXAM_LABEL[plan.exam!]} ${formatTarget(plan.exam, plan.target_score)} · còn ${Math.max(0, plan.days_left ?? 0)} ngày` : 'Đặt ngày thi và mục tiêu'}
            </h1>
            <p style={{ margin: 0, fontSize: '0.9rem' }}>{plan.configured ? plan.status_vi : 'App chia kế hoạch theo tuần từ điểm hiện tại, báo khi bạn chậm tiến độ.'}</p>
          </div>
          {plan.configured && !editing && <button type="button" className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>Sửa</button>}
        </section>
        <Mascot size={64} mood={plan.status === 'behind' ? 'think' : 'happy'} say={plan.status === 'behind' ? 'Hơi chậm rồi, học một bài ngay thôi!' : plan.configured ? 'Mỗi tuần một kỹ năng, đến ngày thi là tự tin!' : 'Cho mình biết ngày thi, mình lên kế hoạch cho nhé!'} className="league-mascot" />

        {showForm && <div style={{ marginTop: 14 }}><TargetForm plan={plan} onSaved={p => { setPlan(p); setEditing(false); }} /></div>}

        {plan.configured && (
          <>
            <section className="card" style={{ marginTop: 16 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
                <span className="plan-chip" style={{ background: `color-mix(in srgb, ${STATUS_COLOR[plan.status]} 14%, transparent)`, color: STATUS_COLOR[plan.status] }}>{STATUS_LABEL[plan.status]}</span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Tuần này: {plan.this_week.lessons ?? 0}/{plan.weekly_lessons} bài · {plan.this_week.mock_tests ?? 0} đề thi thử · {plan.this_week.writing_tasks ?? 0} bài viết · {plan.this_week.speaking_sessions ?? 0} lượt nói</span>
              </div>
              <div className="plan-kpis">
                <div><span>Hiện tại</span><strong>{formatTarget(plan.exam, plan.current_overall)}</strong></div>
                <div><span>Mục tiêu</span><strong>{formatTarget(plan.exam, plan.target_score)}</strong></div>
                <div><span>Dự kiến ngày thi</span><strong style={{ color: plan.projected != null && plan.target_score != null && plan.projected >= plan.target_score ? 'var(--agen-success)' : undefined }}>{formatTarget(plan.exam, plan.projected)}</strong></div>
                <div><span>Còn lại</span><strong>{plan.weeks_left} tuần</strong></div>
              </div>
              <div className="plan-skills">
                {skills.map(s => (
                  <Link key={s} href={SKILL_LINK[s]} className="plan-skill">
                    <span>{plan.skill_labels[s]}</span>
                    <strong>{formatTarget(plan.exam, plan.current[s])}</strong>
                    <small>{plan.current[s] == null ? 'Làm thi thử để đo' : plan.target_score != null && plan.current[s]! >= plan.target_score ? 'Đạt mục tiêu' : 'Cần luyện thêm'}</small>
                  </Link>
                ))}
              </div>
              {plan.advice_vi.length > 0 && <ul style={{ margin: '12px 0 0', paddingLeft: 18, fontSize: '0.88rem', display: 'grid', gap: 4 }}>{plan.advice_vi.map(a => <li key={a}>{a}</li>)}</ul>}
            </section>

            <section style={{ marginTop: 20 }}>
              <div className="section-head"><h3>Lộ trình theo tuần</h3></div>
              <div style={{ display: 'grid', gap: 8 }}>
                {plan.weeks.map(w => (
                  <div key={w.index} className="card plan-week" data-current={w.is_current}>
                    <div style={{ minWidth: 80 }}><div className="eyebrow">Tuần {w.index}</div><div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{new Date(w.start).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })} – {new Date(w.end).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })}</div></div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600 }}>Tập trung: {w.focus.map(f => plan.skill_labels[f]).join(' + ')}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{w.lessons} bài học · {w.mock_tests} đề thi thử · {w.writing_tasks} bài viết · {w.speaking_sessions} lượt nói</div>
                    </div>
                    {w.is_current && <Link href="/learn" className="btn btn-primary btn-sm">Học ngay</Link>}
                  </div>
                ))}
                {plan.weeks.length === 0 && <div className="card" style={{ color: 'var(--text-muted)' }}>Ngày thi đã qua hoặc quá gần — cập nhật ngày thi mới.</div>}
              </div>
            </section>
            <button type="button" className="btn btn-ghost btn-sm" style={{ marginTop: 16 }} onClick={async () => { if (confirm('Xoá kế hoạch ôn thi?')) setPlan(await clearStudyPlan()); }}><Trash2 size={14} /> Xoá kế hoạch</button>
          </>
        )}
      </div>
    </main>
  );
}
