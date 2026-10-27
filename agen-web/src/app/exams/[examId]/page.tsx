'use client';

/**
 * G8 · Làm bài thi thử: đồng hồ đếm ngược, nghe một lần (giọng server qua playText),
 * bài đọc + câu hỏi, nộp bài → band / điểm ước tính và lời giải từng câu.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import confetti from 'canvas-confetti';
import { ArrowLeft, ArrowRight, Check, CircleAlert, Clock, Gem, Headphones, LoaderCircle, Play, Send, Star, Volume2, X } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { EXAM_LABEL, SKILL_LABEL, formatEstimate, getExamPaper, submitExam, type AudioLine, type ExamPaper, type ExamResult, type ExamSection } from '@/lib/examsService';
import { playText, stopSpeech } from '@/lib/speechService';
import Mascot from '@/components/ui/Mascot';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';

type Phase = 'intro' | 'test' | 'result';

async function playLines(lines: AudioLine[], isCancelled: () => boolean) {
  for (const line of lines) {
    if (isCancelled()) return;
    await playText(line.text, { voice: line.voice });
    await new Promise(r => setTimeout(r, 450));
  }
}

function fmtClock(s: number) {
  const m = Math.floor(s / 60); const r = s % 60;
  return `${m}:${r.toString().padStart(2, '0')}`;
}

export default function ExamPlayerPage() {
  const { examId } = useParams<{ examId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [paper, setPaper] = useState<ExamPaper | null>(null);
  const [error, setError] = useState('');
  const [phase, setPhase] = useState<Phase>('intro');
  const [sectionIdx, setSectionIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | number>>({});
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [played, setPlayed] = useState<Record<string, 'playing' | 'done'>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ExamResult | null>(null);
  const startedAt = useRef<number>(0);
  const cancelRef = useRef(false);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    // G13 · a class test travels in ?test=<id> (read here, not via useSearchParams, to keep the page shell static)
    const testId = new URLSearchParams(window.location.search).get('test');
    getExamPaper(examId, testId)
      .then(p => { setPaper(p); setSecondsLeft(p.minutes * 60); })
      .catch((err: unknown) => setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không tải được đề thi.'));
    return () => { cancelRef.current = true; stopSpeech(); };
  }, [hydrated, isAuthenticated, router, examId]);

  const answeredCount = useMemo(() => Object.values(answers).filter(v => v !== '' && v != null).length, [answers]);
  const totalQuestions = paper ? paper.sections.reduce((n, s) => n + s.questions.length, 0) : 0;

  const submit = useCallback(async () => {
    if (!paper || submitting) return;
    setSubmitting(true);
    stopSpeech();
    try {
      const seconds = Math.min(paper.minutes * 60, Math.round((Date.now() - startedAt.current) / 1000));
      const r = await submitExam(paper.id, answers, seconds, paper.class_test?.id);
      setResult(r);
      setPhase('result');
      track('exam_completed', { exam: paper.exam, skill: paper.skill, pct: r.pct, estimate: r.estimate });
      if (r.pct >= 70) { playSound('success'); confetti({ particleCount: 80, spread: 70, origin: { y: 0.6 } }); }
      window.scrollTo({ top: 0 });
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không nộp được bài. Thử lại nhé.');
    } finally { setSubmitting(false); }
  }, [paper, answers, submitting]);

  // Countdown — auto-submit at zero.
  useEffect(() => {
    if (phase !== 'test') return;
    const timer = setInterval(() => {
      setSecondsLeft(s => {
        if (s <= 1) { clearInterval(timer); void submit(); return 0; }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [phase, submit]);

  const start = () => { startedAt.current = Date.now(); setPhase('test'); window.scrollTo({ top: 0 }); };

  const playOnce = async (key: string, lines: AudioLine[]) => {
    if (played[key]) return;
    setPlayed(p => ({ ...p, [key]: 'playing' }));
    cancelRef.current = false;
    await playLines(lines, () => cancelRef.current);
    setPlayed(p => ({ ...p, [key]: 'done' }));
  };

  if (error && !paper) {
    return (
      <main className="exam-page"><div className="exam-column">
        <div className="alert-error"><CircleAlert size={16} /> {error}</div>
        <Link href="/exams" className="btn btn-ghost" style={{ marginTop: 12 }}><ArrowLeft size={16} /> Thư viện đề thi</Link>
      </div></main>
    );
  }
  if (!paper) return <main className="exam-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={20} /> Đang mở đề…</main>;

  // ── Intro ──
  if (phase === 'intro') {
    return (
      <main className="exam-page"><div className="exam-column" style={{ maxWidth: 640 }}>
        <Link href="/exams" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Thư viện đề thi</Link>
        <section className="card" style={{ display: 'grid', gap: 14 }}>
          <div className="eyebrow">{EXAM_LABEL[paper.exam]} · {SKILL_LABEL[paper.skill]}</div>
          <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: 0 }}>{paper.title}</h1>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{paper.description}</p>
          {paper.class_test && <div className="class-test-note">Bài kiểm tra lớp: <b>{paper.class_test.title}</b> · hạn {new Date(`${paper.class_test.due_on}T00:00:00`).toLocaleDateString('vi-VN')}. Bài nộp lần này được gửi điểm cho giáo viên và không trừ lượt thi miễn phí.</div>}
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: '0.9rem', display: 'grid', gap: 6 }}>
            <li><b>{paper.minutes} phút</b>, {totalQuestions} câu, {paper.sections.length} phần. Hết giờ bài tự nộp.</li>
            {paper.skill === 'listening' && <li>Mỗi phần nghe chỉ phát <b>một lần</b> như thi thật. Hãy đeo tai nghe và bật âm lượng trước khi bấm Phát.</li>}
            <li>Câu điền từ: viết đúng chính tả, không phân biệt hoa thường.</li>
            <li>Nộp bài xong sẽ có band / điểm ước tính, lời giải từng câu, +XP và đá quý khi đạt ≥ 70%.</li>
          </ul>
          <button type="button" className="btn btn-primary btn-lg" onClick={start}><Play size={18} /> Bắt đầu làm bài</button>
        </section>
        <Mascot size={64} mood="think" say="Bình tĩnh, đọc kỹ câu hỏi trước khi nghe nhé!" className="league-mascot" />
      </div></main>
    );
  }

  // ── Result ──
  if (phase === 'result' && result) {
    const good = result.pct >= 70;
    return (
      <main className="exam-page"><div className="exam-column" style={{ maxWidth: 760 }}>
        <section className="card exam-result-hero">
          <div className="eyebrow">{EXAM_LABEL[paper.exam]} · {SKILL_LABEL[paper.skill]}</div>
          <div className="exam-result-band">{formatEstimate(paper.exam, result.estimate)}</div>
          <div style={{ color: 'var(--text-secondary)' }}>{result.correct}/{result.total} câu đúng · {result.pct}%{result.best_estimate > result.estimate ? ` · tốt nhất của bạn: ${formatEstimate(paper.exam, result.best_estimate)}` : ''}</div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap', marginTop: 10 }}>
            <span className="xp-badge"><Star size={13} /> +{result.xp_earned} XP</span>
            {result.gems_earned > 0 && <span className="xp-badge" style={{ background: 'color-mix(in srgb, #7DD3FC 25%, transparent)', color: '#0369A1' }}><Gem size={13} /> +{result.gems_earned}</span>}
          </div>
          <div className="exam-sections">
            {result.sections.map(s => (
              <div key={s.id}><div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{s.title.split('·')[0].trim()}</div><strong>{s.correct}/{s.total}</strong></div>
            ))}
          </div>
        </section>
        <Mascot size={64} mood={good ? 'cheer' : 'happy'} say={good ? 'Tuyệt vời! Đọc lại lời giải để nhớ lâu hơn nhé.' : 'Không sao, xem lời giải rồi thử lại là lên điểm ngay!'} className="league-mascot" />

        {paper.sections.map((section, si) => {
          const base = paper.sections.slice(0, si).reduce((n, s) => n + s.questions.length, 0);
          return (
          <section key={section.id} className="card" style={{ marginTop: 16, display: 'grid', gap: 10 }}>
            <h3 style={{ margin: 0 }}>{section.title}</h3>
            {section.audio && (
              <details className="exam-transcript"><summary>Transcript</summary>
                {section.audio.map((l, i) => <p key={i}><b>{l.speaker}:</b> {l.text}</p>)}
              </details>
            )}
            {section.questions.map((q, i) => {
              const d = result.details.find(x => x.id === q.id)!;
              return (
                <div key={q.id} className="exam-review" data-ok={d.correct}>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span className="exam-review-mark">{d.correct ? <Check size={14} /> : <X size={14} />}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600 }}>{base + i + 1}. {q.prompt}</div>
                      {q.audio && <details className="exam-transcript" style={{ marginTop: 4 }}><summary>Transcript</summary>{q.audio.map((l, j) => <p key={j}>{l.text}</p>)}</details>}
                      <div style={{ fontSize: '0.85rem', marginTop: 4 }}>
                        {!d.correct && <span style={{ color: 'var(--agen-secondary)' }}>Bạn chọn: {d.given || '—'} · </span>}
                        <span style={{ color: 'var(--agen-success)' }}>Đáp án: {d.expected}</span>
                      </div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 2 }}>{d.explanation_vi}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </section>
          );
        })}
        <div style={{ display: 'flex', gap: 10, marginTop: 20, flexWrap: 'wrap' }}>
          <Link href="/exams" className="btn btn-primary"><ArrowLeft size={16} /> Thư viện đề thi</Link>
          <Link href="/dashboard" className="btn btn-ghost">Trang chủ</Link>
        </div>
      </div></main>
    );
  }

  // ── Test ──
  const section: ExamSection = paper.sections[sectionIdx];
  const last = sectionIdx === paper.sections.length - 1;
  const low = secondsLeft <= 60;
  const offset = paper.sections.slice(0, sectionIdx).reduce((n, s) => n + s.questions.length, 0);

  const renderAudioButton = (key: string, lines: AudioLine[], label: string) => {
    const state = played[key];
    return (
      <button type="button" className={state ? 'btn btn-outline btn-sm' : 'btn btn-primary btn-sm'} disabled={!!state} onClick={() => void playOnce(key, lines)}>
        {state === 'playing' ? <><Volume2 size={14} className="animate-pulse" /> Đang phát…</> : state === 'done' ? <><Check size={14} /> Đã phát</> : <><Headphones size={14} /> {label}</>}
      </button>
    );
  };

  return (
    <main className="exam-page">
      <div className="exam-topbar">
        <div style={{ fontWeight: 600, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{paper.title}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{answeredCount}/{totalQuestions}</span>
          <span className="exam-clock" data-low={low}><Clock size={14} /> {fmtClock(secondsLeft)}</span>
        </div>
      </div>
      <div className="exam-column">
        <div className="segmented" style={{ marginBottom: 14, overflowX: 'auto' }}>
          {paper.sections.map((s, i) => <button key={s.id} type="button" aria-pressed={i === sectionIdx} onClick={() => setSectionIdx(i)}>{s.title.split('·')[0].trim()}</button>)}
        </div>
        {error && <div className="alert-error" style={{ marginBottom: 12 }}><CircleAlert size={16} /> {error}</div>}

        <section className="card" style={{ display: 'grid', gap: 12 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.15rem' }}>{section.title}</h2>
            <p style={{ margin: '4px 0 0', fontSize: '0.88rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>{section.instructions}</p>
          </div>
          {section.audio && (
            <div className="exam-audio">
              <Headphones size={18} />
              <span style={{ flex: 1, fontSize: '0.85rem' }}>Phần nghe chỉ phát một lần.</span>
              {renderAudioButton(section.id, section.audio, 'Phát audio')}
            </div>
          )}
          {section.passage && <div className="exam-passage">{section.passage}</div>}
        </section>

        <div style={{ display: 'grid', gap: 10, marginTop: 12 }}>
          {section.questions.map((q, i) => (
            <div key={q.id} className="card exam-q">
              <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 200, fontWeight: 600 }}>{offset + i + 1}. {q.prompt}</div>
                {q.audio && renderAudioButton(q.id, q.audio, 'Nghe câu hỏi')}
              </div>
              {q.type === 'gap' ? (
                <input className="form-input" style={{ marginTop: 10, maxWidth: 320 }} placeholder="Câu trả lời" value={(answers[q.id] as string) ?? ''} onChange={e => setAnswers(a => ({ ...a, [q.id]: e.target.value }))} autoComplete="off" spellCheck={false} aria-label={`Câu ${offset + i + 1}`} />
              ) : (
                <div className="choice-grid" style={{ marginTop: 10 }}>
                  {q.options!.map((opt, oi) => (
                    <button key={oi} type="button" className="choice" data-state={answers[q.id] === oi ? 'selected' : undefined} onClick={() => setAnswers(a => ({ ...a, [q.id]: oi }))}>
                      <span className="choice-key">{String.fromCharCode(65 + oi)}</span><span>{opt}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, marginTop: 20, flexWrap: 'wrap' }}>
          <button type="button" className="btn btn-ghost" disabled={sectionIdx === 0} onClick={() => { setSectionIdx(i => i - 1); window.scrollTo({ top: 0 }); }}><ArrowLeft size={16} /> Phần trước</button>
          {last
            ? <button type="button" className="btn btn-primary" disabled={submitting} onClick={() => { if (answeredCount < totalQuestions && !confirm(`Bạn còn ${totalQuestions - answeredCount} câu chưa trả lời. Nộp bài?`)) return; void submit(); }}>{submitting ? <LoaderCircle className="animate-spin" size={16} /> : <Send size={16} />} Nộp bài</button>
            : <button type="button" className="btn btn-primary" onClick={() => { setSectionIdx(i => i + 1); window.scrollTo({ top: 0 }); }}>Phần tiếp <ArrowRight size={16} /></button>}
        </div>
      </div>
    </main>
  );
}
