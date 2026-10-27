'use client';

/** G10 · Giáo viên xem chi tiết bài làm của một học viên và gửi nhận xét / cấp chứng nhận. */
import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Award, BookOpen, CircleAlert, ClipboardCheck, Flame, LoaderCircle, MessageSquarePlus, Mic, PenLine, Send, Star, Trash2, X } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import {
  IELTS_CRITERIA, SKILL_LABELS, testScoreLabel, addMemberFeedback, deleteFeedback, getMemberDetail, getMemberWriting, gradeMemberWriting, issueCertificate,
  type AssignmentSkill, type IeltsRubric, type FeedbackTarget, type MemberDetail, type WritingDetail,
} from '@/lib/groupsService';
import { formatEstimate, type ExamKind } from '@/lib/examsService';
import { formatSpeakingEstimate } from '@/lib/speakingExamsService';
import Avatar from '@/components/ui/Avatar';
import RubricChart from '@/components/teacher/RubricChart';
import { track } from '@/lib/analytics';

type Tab = 'lessons' | 'writings' | 'exams' | 'speaking' | 'tests' | 'assignments';
interface Target { type: FeedbackTarget; id: string | null; label: string | null }

const SKILL_VI: Record<string, string> = { listening: 'Nghe', speaking: 'Nói', reading: 'Đọc', writing: 'Viết', vocabulary: 'Từ vựng', grammar: 'Ngữ pháp' };
const TARGET_VI: Record<FeedbackTarget, string> = { general: 'Chung', lesson: 'Bài học', writing: 'Bài viết', exam: 'Thi thử', speaking_exam: 'Thi nói' };
const day = (s: string | null) => (s ? new Date(s.endsWith('Z') ? s : `${s}Z`).toLocaleDateString('vi-VN') : '—');
const errText = (err: unknown, fallback: string) => (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || fallback;

const BANDS = Array.from({ length: 19 }, (_, i) => i * 0.5);
/** IELTS rounding of the mean (.25 → .5, .75 → next band) — same rule as the server. */
function ieltsOverall(r: IeltsRubric): number {
  const avg = (r.task + r.coherence + r.lexical + r.grammar) / 4;
  const base = Math.floor(avg);
  const frac = avg - base;
  return base + (frac < 0.25 ? 0 : frac < 0.75 ? 0.5 : 1);
}

function WritingView({ w, onClose, onComment, onGrade }: { w: WritingDetail; onClose: () => void; onComment: () => void; onGrade: (score: number | null, band: number | null, comment: string, rubric?: IeltsRubric | null) => Promise<void> }) {
  const ev = w.evaluation as { strengths?: string[]; improvements?: string[]; grammar_errors?: { original?: string; corrected?: string; explanation_vi?: string }[]; corrected_version?: string; exam_band?: { overall?: number } };
  const [score, setScore] = useState(w.teacher_score != null ? String(w.teacher_score) : w.overall_score != null ? String(Math.round(w.overall_score)) : '');
  const [band, setBand] = useState(w.teacher_band != null ? String(w.teacher_band) : ev.exam_band?.overall != null ? String(ev.exam_band.overall) : '');
  const [comment, setComment] = useState(w.teacher_comment ?? '');
  const [saving, setSaving] = useState(false);
  // G12 · IELTS: grade the 4 official criteria; the band follows, the /100 score defaults to band / 9
  const isIelts = w.exam === 'ielts';
  const aiCrit = (ev as { exam_band?: { criteria?: Record<string, number> } }).exam_band?.criteria ?? {};
  const seed = (k: keyof IeltsRubric, aiKey: string) => w.teacher_rubric?.[k] ?? (typeof aiCrit[aiKey] === 'number' ? Math.round(aiCrit[aiKey] * 2) / 2 : 6);
  const [useRubric, setUseRubric] = useState(isIelts);
  const [rubric, setRubric] = useState<IeltsRubric>({
    task: seed('task', 'task_response'), coherence: seed('coherence', 'coherence_cohesion'),
    lexical: seed('lexical', 'lexical_resource'), grammar: seed('grammar', 'grammatical_range'),
  });
  const [scoreTouched, setScoreTouched] = useState(false);
  const rubricBand = ieltsOverall(rubric);
  const save = async (clear = false) => {
    setSaving(true);
    try {
      if (clear) await onGrade(null, null, '');
      else if (isIelts && useRubric) await onGrade(scoreTouched && score !== '' ? Number(score) : null, null, comment, rubric);
      else await onGrade(Number(score), !w.exam || band === '' ? null : Number(band), comment);
    } finally { setSaving(false); }
  };
  return (
    <section className="card member-writing">
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <div className="eyebrow">Bài viết · {w.genre} · {w.word_count} từ · {day(w.created_at)}</div>
          <h3 style={{ margin: '2px 0 6px' }}>{w.prompt_title}</h3>
          <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>{w.prompt_text}</p>
        </div>
        <button type="button" className="icon-btn" aria-label="Đóng" onClick={onClose}><X size={16} /></button>
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', margin: '10px 0' }}>
        {w.overall_score != null && <span className="xp-badge">Điểm AI {Math.round(w.overall_score)}{w.grade ? ` · ${w.grade}` : ''}</span>}
        {ev.exam_band?.overall != null && <span className="xp-badge">Band AI {ev.exam_band.overall}</span>}
        {w.teacher_score != null && <span className="teacher-score">Giáo viên {w.teacher_score}{w.teacher_band != null ? ` · ${w.exam === 'ielts' ? 'band' : 'TOEIC'} ${w.teacher_band}` : ''}</span>}
        {w.teacher_rubric && <span className="rubric-chips">{IELTS_CRITERIA.map(c => <span key={c.key}>{c.label} {w.teacher_rubric![c.key]}</span>)}</span>}
      </div>
      <div className="member-essay">{w.user_text}</div>
      {!!ev.grammar_errors?.length && (
        <>
          <div style={{ fontWeight: 600, margin: '12px 0 6px' }}>Lỗi AI đã chỉ ra</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: '0.88rem' }}>
            {ev.grammar_errors.map((g, i) => <li key={i}><s>{g.original}</s> → <b>{g.corrected}</b>{g.explanation_vi ? ` — ${g.explanation_vi}` : ''}</li>)}
          </ul>
        </>
      )}
      {!!ev.improvements?.length && <p style={{ fontSize: '0.88rem', margin: '10px 0 0' }}><b>Cần cải thiện:</b> {ev.improvements.join('; ')}</p>}

      <form className="writing-grade" onSubmit={e => { e.preventDefault(); void save(); }}>
        <div style={{ fontWeight: 600, fontSize: '0.92rem' }}>Chấm lại (thay điểm AI khi học viên xem)</div>
        {isIelts && (
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', cursor: 'pointer' }}>
            <input type="checkbox" checked={useRubric} onChange={e => setUseRubric(e.target.checked)} /> Chấm theo 4 tiêu chí IELTS
          </label>
        )}
        {isIelts && useRubric && (
          <>
            <div className="rubric-grid">
              {IELTS_CRITERIA.map(c => (
                <label key={c.key} style={{ display: 'grid', gap: 4, fontSize: '0.8rem' }}>{c.label}
                  <select className="form-input" value={rubric[c.key]} onChange={e => setRubric(r => ({ ...r, [c.key]: Number(e.target.value) }))} aria-label={c.label}>
                    {BANDS.map(b => <option key={b} value={b}>{b.toFixed(1)}</option>)}
                  </select>
                </label>
              ))}
            </div>
            <div style={{ fontSize: '0.85rem' }}>Band tổng: <b>{rubricBand.toFixed(1)}</b> · điểm /100 mặc định {Math.round(rubricBand / 9 * 100)}</div>
          </>
        )}
        <div className="writing-grade-row">
          <label style={{ display: 'grid', gap: 4, fontSize: '0.8rem' }}>Điểm /100{isIelts && useRubric ? ' (tuỳ chọn)' : ''}
            <input className="form-input" type="number" min={0} max={100} step={0.5} value={isIelts && useRubric && !scoreTouched ? String(Math.round(rubricBand / 9 * 100)) : score}
              onChange={e => { setScore(e.target.value); setScoreTouched(true); }} required={!(isIelts && useRubric)} aria-label="Điểm giáo viên" />
          </label>
          {w.exam && !(isIelts && useRubric) && (
            <label style={{ display: 'grid', gap: 4, fontSize: '0.8rem' }}>{w.exam === 'ielts' ? 'Band IELTS (0–9)' : 'TOEIC Writing (0–200)'}
              <input className="form-input" type="number" min={0} max={w.exam === 'ielts' ? 9 : 200} step={w.exam === 'ielts' ? 0.5 : 10} value={band} onChange={e => setBand(e.target.value)} aria-label="Band giáo viên" />
            </label>
          )}
        </div>
        <textarea className="form-input" rows={2} maxLength={2000} value={comment} onChange={e => setComment(e.target.value)} placeholder="Nhận xét kèm điểm (tuỳ chọn)" aria-label="Nhận xét khi chấm" />
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button type="submit" className="btn btn-primary btn-sm" disabled={saving || (score === '' && !(isIelts && useRubric))}>{saving ? <LoaderCircle className="animate-spin" size={14} /> : <Star size={14} />} Lưu điểm & báo học viên</button>
          {w.teacher_score != null && <button type="button" className="btn btn-ghost btn-sm" disabled={saving} onClick={() => save(true)}>Bỏ điểm giáo viên</button>}
          <button type="button" className="btn btn-ghost btn-sm" onClick={onComment}><MessageSquarePlus size={14} /> Chỉ nhận xét</button>
        </div>
      </form>
    </section>
  );
}

export default function MemberDetailPage() {
  const { groupId, learnerId } = useParams<{ groupId: string; learnerId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [d, setD] = useState<MemberDetail | null>(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<Tab>('lessons');
  const [writing, setWriting] = useState<WritingDetail | null>(null);
  const [target, setTarget] = useState<Target>({ type: 'general', id: null, label: null });
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [cert, setCert] = useState({ title: '', note: '' });
  const [certMsg, setCertMsg] = useState('');

  const load = useCallback(() => getMemberDetail(groupId, learnerId).then(setD).catch(err => setError(errText(err, 'Không tải được học viên.'))), [groupId, learnerId]);
  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    void load();
  }, [hydrated, isAuthenticated, router, load]);

  const comment = (t: Target) => {
    setTarget(t);
    document.getElementById('feedback-form')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => document.getElementById('feedback-text')?.focus(), 300);
  };
  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setBusy(true); setError('');
    try {
      await addMemberFeedback(groupId, learnerId, { text: text.trim(), target_type: target.type, target_id: target.id, target_label: target.label });
      track('teacher_feedback_sent', { target: target.type });
      setText(''); setTarget({ type: 'general', id: null, label: null });
      await load();
    } catch (err) { setError(errText(err, 'Chưa gửi được nhận xét.')); } finally { setBusy(false); }
  };
  const issue = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setCertMsg('');
    try {
      const c = await issueCertificate(groupId, learnerId, cert.title.trim(), cert.note.trim());
      track('certificate_issued', { kind: 'group' });
      setCertMsg(`Đã cấp chứng nhận mã ${c.code}.`);
      setCert({ title: '', note: '' });
      await load();
    } catch (err) { setCertMsg(errText(err, 'Chưa cấp được chứng nhận.')); } finally { setBusy(false); }
  };
  const gradeWriting = async (score: number | null, band: number | null, note: string, rubric?: IeltsRubric | null) => {
    if (!writing) return;
    setError('');
    try {
      const updated = await gradeMemberWriting(groupId, learnerId, writing.id, { score, band, comment: note || null, rubric: rubric ?? null });
      setWriting(updated);
      track(rubric ? 'writing_rubric_graded' : 'writing_regraded', { cleared: score == null && !rubric, exam: updated.exam ?? null });
      await load();
    } catch (err) { setError(errText(err, 'Chưa lưu được điểm.')); }
  };
  const openWriting = async (id: string) => {
    try { setWriting(await getMemberWriting(groupId, learnerId, id)); } catch (err) { setError(errText(err, 'Không mở được bài viết.')); }
  };

  if (!d) return <main className="teacher-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <div style={{ display: 'flex', gap: 10, alignItems: 'center', color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={20} /> Đang tải…</div>}</main>;

  const commentBtn = (t: Target) => <button type="button" className="icon-btn" aria-label="Nhận xét" title="Nhận xét" onClick={() => comment(t)}><MessageSquarePlus size={15} /></button>;
  const tabs: [Tab, string, number][] = [
    ['lessons', 'Bài học', d.lessons.length], ['writings', 'Bài viết', d.writings.length], ['exams', 'Thi thử', d.exams.length],
    ['speaking', 'Thi nói', d.speaking_exams.length], ['tests', 'Kiểm tra lớp', d.tests?.length ?? 0], ['assignments', 'Bài tập', d.assignments.length],
  ];

  return (
    <main className="teacher-page">
      <div className="teacher-column">
        <Link href={`/teacher/${groupId}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> {d.group.name}</Link>
        <section className="card member-hero">
          <Avatar avatar={d.avatar} name={d.display_name} size={64} />
          <div style={{ flex: 1, minWidth: 200 }}>
            <div className="eyebrow">Học viên · {d.group.name}</div>
            <h1 style={{ fontSize: 'clamp(1.4rem, 4vw, 1.9rem)', margin: '2px 0 6px' }}>{d.display_name}</h1>
            <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
              <span className="level-badge">{d.level.replace('PRE_', 'Pre-')}</span>
              <span><Star size={13} color="var(--agen-accent)" fill="var(--agen-accent)" /> {d.weekly_xp} XP tuần · {d.total_xp} tổng</span>
              <span><Flame size={13} color="var(--agen-secondary)" /> {d.streak} ngày</span>
              <span>{d.lessons_completed} bài đã học</span>
              <span>Hoạt động: {day(d.last_active_at)}</span>
            </div>
          </div>
        </section>

        <div className="member-skills">
          {Object.entries(d.skills).map(([k, v]) => (
            <div key={k} className="member-skill"><span>{SKILL_VI[k] ?? k}</span><div className="club-progress"><span style={{ width: `${Math.min(100, v)}%` }} /></div><b>{v}</b></div>
          ))}
        </div>

        {!!d.rubric_history?.length && <RubricChart points={d.rubric_history} onOpen={openWriting} />}
        {!!d.speaking_history?.length && <RubricChart kind="speaking" points={d.speaking_history} onOpen={() => setTab('speaking')} />}

        {error && <div className="alert-error" style={{ margin: '12px 0' }}><CircleAlert size={16} /> {error}</div>}
        {writing && <WritingView key={writing.id + (writing.teacher_scored_at ?? '')} w={writing} onClose={() => setWriting(null)} onComment={() => comment({ type: 'writing', id: writing.id, label: writing.prompt_title })} onGrade={gradeWriting} />}

        <div className="segmented" style={{ margin: '16px 0 10px', overflowX: 'auto', maxWidth: '100%' }} role="tablist">
          {tabs.map(([k, label, n]) => <button key={k} type="button" aria-pressed={tab === k} onClick={() => setTab(k)}>{label} ({n})</button>)}
        </div>
        <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
          <table className="teacher-table">
            {tab === 'lessons' && (<>
              <thead><tr><th>Bài học</th><th>Kỹ năng</th><th>Điểm</th><th>Ngày</th><th /></tr></thead>
              <tbody>{d.lessons.length === 0 ? <tr><td colSpan={5} style={{ color: 'var(--text-muted)' }}>Chưa hoàn thành bài nào.</td></tr> : d.lessons.map(l => (
                <tr key={l.id}><td><BookOpen size={13} /> {l.title}</td><td>{SKILL_VI[l.skill] ?? l.skill}</td><td><b>{l.score}</b></td><td>{day(l.completed_at)}</td><td>{commentBtn({ type: 'lesson', id: l.id, label: l.title })}</td></tr>
              ))}</tbody>
            </>)}
            {tab === 'writings' && (<>
              <thead><tr><th>Đề</th><th>Thể loại</th><th>Điểm</th><th>Số từ</th><th>Ngày</th><th /></tr></thead>
              <tbody>{d.writings.length === 0 ? <tr><td colSpan={6} style={{ color: 'var(--text-muted)' }}>Chưa có bài viết.</td></tr> : d.writings.map(w => (
                <tr key={w.id}>
                  <td><button type="button" className="teacher-member-link" onClick={() => openWriting(w.id)}><PenLine size={13} /> {w.prompt_title}</button></td>
                  <td>{w.genre}</td><td><b>{w.band != null ? `Band ${w.band}` : w.score != null ? Math.round(w.score) : '—'}</b>{w.grade ? ` · ${w.grade}` : ''}{w.teacher_score != null && <> <span className="teacher-score" title="Giáo viên đã chấm lại">GV {w.teacher_band != null ? w.teacher_band : w.teacher_score}</span></>}</td><td>{w.word_count}</td><td>{day(w.created_at)}</td>
                  <td>{commentBtn({ type: 'writing', id: w.id, label: w.prompt_title })}</td>
                </tr>
              ))}</tbody>
            </>)}
            {tab === 'exams' && (<>
              <thead><tr><th>Đề thi</th><th>Đúng</th><th>Ước tính</th><th>Ngày</th><th /></tr></thead>
              <tbody>{d.exams.length === 0 ? <tr><td colSpan={5} style={{ color: 'var(--text-muted)' }}>Chưa làm đề thi thử.</td></tr> : d.exams.map(x => (
                <tr key={x.id}><td><ClipboardCheck size={13} /> {x.title}</td><td>{Math.round(x.pct)}%</td><td><b>{x.estimate != null ? formatEstimate(x.exam as ExamKind, x.estimate) : '—'}</b></td><td>{day(x.created_at)}</td><td>{commentBtn({ type: 'exam', id: x.id, label: x.title })}</td></tr>
              ))}</tbody>
            </>)}
            {tab === 'speaking' && (<>
              <thead><tr><th>Đề thi nói</th><th>Ước tính</th><th>Ngày</th><th /></tr></thead>
              <tbody>{d.speaking_exams.length === 0 ? <tr><td colSpan={4} style={{ color: 'var(--text-muted)' }}>Chưa thi nói.</td></tr> : d.speaking_exams.map(x => (
                <tr key={x.id}><td><Mic size={13} /> {x.title}</td><td><b>{x.estimate != null ? formatSpeakingEstimate(x.exam as ExamKind, x.estimate) : '—'}</b></td><td>{day(x.created_at)}</td><td>{commentBtn({ type: 'speaking_exam', id: x.id, label: x.title })}</td></tr>
              ))}</tbody>
            </>)}
            {tab === 'tests' && (<>
              <thead><tr><th>Bài kiểm tra</th><th>Hạn</th><th>Kết quả</th><th>TB lớp</th></tr></thead>
              <tbody>{!d.tests?.length ? <tr><td colSpan={4} style={{ color: 'var(--text-muted)' }}>Lớp chưa có bài kiểm tra.</td></tr> : d.tests.map(t => (
                <tr key={t.id}><td><ClipboardCheck size={13} /> {t.title}</td><td>{day(`${t.due_on}T12:00:00`)}</td>
                  <td>{t.mine?.done ? <b>{testScoreLabel(t.exam, t.mine)}</b> : <span className="plan-chip">{t.status === 'closed' ? 'Không làm' : 'Chưa làm'}</span>}</td>
                  <td>{t.avg_estimate != null ? testScoreLabel(t.exam, { estimate: t.avg_estimate, pct: t.avg_pct }) : '—'}</td></tr>
              ))}</tbody>
            </>)}
            {tab === 'assignments' && (<>
              <thead><tr><th>Bài tập</th><th>Kỹ năng</th><th>Hạn</th><th>Trạng thái</th></tr></thead>
              <tbody>{d.assignments.length === 0 ? <tr><td colSpan={4} style={{ color: 'var(--text-muted)' }}>Nhóm chưa giao bài.</td></tr> : d.assignments.map(a => (
                <tr key={a.id}><td>{a.title}</td><td>{SKILL_LABELS[a.skill as AssignmentSkill] ?? a.skill}</td><td>{a.due_on ?? '—'}</td>
                  <td>{a.done ? <span className="plan-chip is-premium">Xong{a.score != null ? ` · ${Math.round(a.score)}` : ''}</span> : a.overdue ? <span className="plan-chip">Quá hạn</span> : a.started ? <span className="plan-chip">Đang làm</span> : <span className="plan-chip">Chưa làm</span>}</td></tr>
              ))}</tbody>
            </>)}
          </table>
        </div>

        <div className="member-columns">
          <section className="card" id="feedback-form">
            <div className="section-head"><h3>Nhận xét gửi học viên</h3></div>
            <form onSubmit={send} style={{ display: 'grid', gap: 8 }}>
              <div style={{ fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                Về: <span className="plan-chip">{TARGET_VI[target.type]}{target.label ? ` · ${target.label}` : ''}</span>
                {target.type !== 'general' && <button type="button" className="icon-btn" aria-label="Bỏ chọn" onClick={() => setTarget({ type: 'general', id: null, label: null })}><X size={13} /></button>}
              </div>
              <textarea id="feedback-text" className="form-input" rows={3} maxLength={2000} value={text} onChange={e => setText(e.target.value)} placeholder="VD: Em dùng thì quá khứ tốt hơn rồi. Tuần này luyện thêm câu điều kiện nhé." />
              <button type="submit" className="btn btn-primary btn-sm" style={{ justifySelf: 'start' }} disabled={busy || !text.trim()}><Send size={14} /> Gửi nhận xét</button>
            </form>
            <div style={{ marginTop: 14, display: 'grid', gap: 8 }}>
              {d.feedback.length === 0 && <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>Chưa có nhận xét. Học viên sẽ nhận thông báo khi bạn gửi.</p>}
              {d.feedback.map(f => (
                <div key={f.id} className="member-feedback">
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: 6, alignItems: 'center' }}>
                    <span style={{ flex: 1 }}>{TARGET_VI[f.target_type]}{f.target_label ? ` · ${f.target_label}` : ''} · {day(f.created_at)} · {f.read_at ? 'đã đọc' : 'chưa đọc'}</span>
                    <button type="button" className="icon-btn" aria-label="Xoá nhận xét" onClick={async () => { if (confirm('Xoá nhận xét này?')) { await deleteFeedback(groupId, f.id); await load(); } }}><Trash2 size={13} /></button>
                  </div>
                  <div style={{ whiteSpace: 'pre-line', fontSize: '0.9rem' }}>{f.text}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="card">
            <div className="section-head"><h3><Award size={16} /> Chứng nhận hoàn thành</h3></div>
            <form onSubmit={issue} style={{ display: 'grid', gap: 8 }}>
              <input className="form-input" value={cert.title} onChange={e => setCert(c => ({ ...c, title: e.target.value }))} maxLength={200} placeholder="VD: Hoàn thành khoá Giao tiếp A2" aria-label="Tên chứng nhận" />
              <input className="form-input" value={cert.note} onChange={e => setCert(c => ({ ...c, note: e.target.value }))} maxLength={300} placeholder="Ghi chú (không bắt buộc)" aria-label="Ghi chú" />
              <button type="submit" className="btn btn-outline btn-sm" style={{ justifySelf: 'start' }} disabled={busy || cert.title.trim().length < 3}><Award size={14} /> Cấp chứng nhận</button>
            </form>
            {certMsg && <p style={{ fontSize: '0.85rem', margin: '8px 0 0' }}>{certMsg}</p>}
            {d.certificates.map(c => (
              <a key={c.code} href={`/certificate/${c.code}`} target="_blank" rel="noreferrer" className="member-cert"><Award size={14} /> {c.title} <span style={{ color: 'var(--text-muted)' }}>· {c.code}</span></a>
            ))}
          </section>
        </div>
      </div>
    </main>
  );
}
