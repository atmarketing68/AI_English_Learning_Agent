'use client';

/** G8 · Thi thử IELTS / TOEIC — catalogue, best results and history. */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, CircleAlert, ClipboardCheck, Clock, Headphones, BookOpen, Lock, Mic, Sparkles, Trophy } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { EXAM_LABEL, formatEstimate, getExamCatalogue, getExamHistory, type ExamAttempt, type ExamCatalogue, type ExamKind } from '@/lib/examsService';
import { formatSpeakingEstimate, getSpeakingCatalogue, type SpeakingCatalogue } from '@/lib/speakingExamsService';
import { PageSkeleton } from '@/components/Skeleton';
import Mascot from '@/components/ui/Mascot';
import { track } from '@/lib/analytics';

export default function ExamsPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [data, setData] = useState<ExamCatalogue | null>(null);
  const [history, setHistory] = useState<ExamAttempt[]>([]);
  const [speaking, setSpeaking] = useState<SpeakingCatalogue | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    Promise.all([getExamCatalogue(), getExamHistory(10)])
      .then(([c, h]) => { setData(c); setHistory(h); })
      .catch(() => setError('Không tải được thư viện đề thi.'));
    getSpeakingCatalogue().then(setSpeaking).catch(() => null);
  }, [hydrated, isAuthenticated, router]);

  if (!data) return <main className="friends-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={3} />}</main>;

  const groups: ExamKind[] = ['ielts', 'toeic'];
  const bestOverall = data.exams.filter(e => e.best_estimate != null);

  return (
    <main className="friends-page">
      <div className="friends-column" style={{ maxWidth: 760 }}>
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Trang chủ</Link>
        <section className="card friends-hero">
          <span className="icon-tile" style={{ width: 56, height: 56, borderRadius: 18, background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}><ClipboardCheck size={28} strokeWidth={1.7} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow">Thi thử</div>
            <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>Đề thi thử IELTS & TOEIC</h1>
            <p style={{ margin: 0, fontSize: '0.9rem' }}>Đúng định dạng đề thật, có đồng hồ, nghe một lần. Nộp bài là biết band / điểm ước tính và lời giải từng câu.</p>
          </div>
        </section>
        <Mascot size={64} mood={bestOverall.length ? 'cheer' : 'think'} say={bestOverall.length ? 'Thi thử xong nhớ đọc lời giải từng câu nhé!' : 'Chọn một đề để thử sức nào!'} className="league-mascot" />

        {!data.is_premium && (
          <div className="card" style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', borderColor: data.can_start ? undefined : 'color-mix(in srgb, var(--agen-accent) 40%, transparent)' }}>
            {data.can_start ? <Sparkles size={18} color="var(--agen-accent)" /> : <Lock size={18} color="var(--agen-accent)" />}
            <div style={{ flex: 1, minWidth: 200, fontSize: '0.88rem' }}>
              {data.can_start
                ? <>Gói miễn phí: <b>{data.free_daily_attempts} đề/ngày</b>. Hôm nay bạn còn {data.free_daily_attempts - data.attempts_today} lượt.</>
                : <>Bạn đã dùng hết {data.free_daily_attempts} đề miễn phí hôm nay. Premium thi không giới hạn.</>}
            </div>
            <Link href="/upgrade" className="btn btn-primary btn-sm">Nâng cấp Premium</Link>
          </div>
        )}

        {groups.map(kind => (
          <section key={kind} style={{ marginTop: 20 }}>
            <div className="section-head"><h3>{EXAM_LABEL[kind]}</h3></div>
            <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
              {data.exams.filter(e => e.exam === kind).map(e => {
                const Icon = e.skill === 'listening' ? Headphones : BookOpen;
                return (
                  <div key={e.id} className="card exam-card">
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span className="icon-tile" style={{ background: 'var(--bg-tint)', color: e.skill === 'listening' ? 'var(--skill-listening)' : 'var(--skill-reading, var(--agen-success))' }}><Icon size={18} /></span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 600 }}>{e.title.replace(/^(IELTS|TOEIC)\s*/, '')}</div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', gap: 10 }}><span><Clock size={12} /> {e.minutes} phút</span><span>{e.questions} câu</span></div>
                      </div>
                      {e.best_estimate != null && <span className="xp-badge" title={`Tốt nhất: ${e.best_pct}%`}><Trophy size={13} /> {formatEstimate(e.exam, e.best_estimate)}</span>}
                    </div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '10px 0 12px' }}>{e.description}</p>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{e.attempts ? `${e.attempts} lần làm` : 'Chưa làm'}</span>
                      {data.can_start
                        ? <Link href={`/exams/${e.id}`} className="btn btn-primary btn-sm" onClick={() => track('exam_started', { exam: e.exam, skill: e.skill })}>{e.attempts ? 'Làm lại' : 'Làm bài'} <ArrowRight size={14} /></Link>
                        : <button type="button" className="btn btn-outline btn-sm" disabled><Lock size={13} /> Hết lượt hôm nay</button>}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}

        {speaking && (
          <section style={{ marginTop: 20 }}>
            <div className="section-head"><h3>Speaking · giám khảo AI</h3></div>
            <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
              {speaking.exams.map(e => (
                <div key={e.id} className="card exam-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span className="icon-tile" style={{ background: 'var(--bg-tint)', color: 'var(--skill-speaking, #D6336C)' }}><Mic size={18} /></span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600 }}>{EXAM_LABEL[e.exam]} Speaking · Mini Test</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', gap: 10 }}><span><Clock size={12} /> {e.minutes} phút</span><span>{e.tasks} phần</span></div>
                    </div>
                    {e.best_estimate != null && <span className="xp-badge"><Trophy size={13} /> {formatSpeakingEstimate(e.exam, e.best_estimate)}</span>}
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '10px 0 12px' }}>{e.description}</p>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{e.attempts ? `${e.attempts} lần thi` : 'Cần micro'}</span>
                    {speaking.can_start
                      ? <Link href={`/exams/speaking/${e.id}`} className="btn btn-primary btn-sm" onClick={() => track('speaking_exam_started', { exam: e.exam })}>{e.attempts ? 'Thi lại' : 'Bắt đầu'} <ArrowRight size={14} /></Link>
                      : <button type="button" className="btn btn-outline btn-sm" disabled><Lock size={13} /> Hết lượt hôm nay</button>}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {history.length > 0 && (
          <section className="card" style={{ marginTop: 24, padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', fontWeight: 600 }}>Lịch sử thi thử</div>
            {history.map(h => (
              <div key={h.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 16px', borderTop: '1px solid var(--border-subtle)', fontSize: '0.88rem' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600 }}>{h.title}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{new Date(h.created_at).toLocaleString('vi-VN')}{h.seconds ? ` · ${Math.round(h.seconds / 60)} phút` : ''}</div>
                </div>
                <span style={{ color: 'var(--text-secondary)' }}>{h.correct}/{h.total}</span>
                <strong>{formatEstimate(h.exam, h.estimate)}</strong>
              </div>
            ))}
          </section>
        )}
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 16 }}>Band / điểm là ước tính quy đổi từ bảng điểm công bố của IELTS và TOEIC cho đề rút gọn, không thay thế kỳ thi chính thức.</p>
      </div>
    </main>
  );
}
