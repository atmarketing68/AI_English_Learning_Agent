'use client';

/**
 * G9 · Thi thử Speaking: giám khảo AI đọc câu hỏi, đếm giờ chuẩn bị, ghi âm qua
 * micro (nhận diện giọng nói của trình duyệt, tự nối lại khi Chrome ngắt vì im
 * lặng), gửi transcript từng phần, nộp bài → band / điểm + nhận xét.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import confetti from 'canvas-confetti';
import { ArrowLeft, ArrowRight, Check, CircleAlert, Gem, LoaderCircle, Mic, Play, Send, SkipForward, Star, Volume2 } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { EXAM_LABEL } from '@/lib/examsService';
import {
  CRITERIA_VI, answerSpeakingTask, finishSpeakingExam, formatSpeakingEstimate, startSpeakingExam,
  type SpeakingPaper, type SpeakingResult, type SpeakingTask,
} from '@/lib/speakingExamsService';
import { SpeechRecognizer, playText, stopSpeech } from '@/lib/speechService';
import MicButton from '@/components/speaking/MicButton';
import Mascot from '@/components/ui/Mascot';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

type Phase = 'intro' | 'listen' | 'prep' | 'answer' | 'saving' | 'between' | 'result';

export default function SpeakingExamPage() {
  const { examId } = useParams<{ examId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [paper, setPaper] = useState<SpeakingPaper | null>(null);
  const [attemptId, setAttemptId] = useState('');
  const [error, setError] = useState('');
  const [phase, setPhase] = useState<Phase>('intro');
  const [idx, setIdx] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const [finalText, setFinalText] = useState('');
  const [interim, setInterim] = useState('');
  const [answered, setAnswered] = useState<Record<string, number>>({});
  const [micError, setMicError] = useState('');
  const [result, setResult] = useState<SpeakingResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const recognizer = useRef<SpeechRecognizer | null>(null);
  const wantListening = useRef(false);
  const finals = useRef<string[]>([]);
  const startedAt = useRef(0);
  const phaseRef = useRef<Phase>('intro');
  useEffect(() => { phaseRef.current = phase; }, [phase]);

  // One recognizer for the whole test; it restarts itself while an answer window is open.
  useEffect(() => {
    const rec = new SpeechRecognizer(
      r => { if (r.isFinal) { finals.current.push(r.transcript.trim()); setFinalText(finals.current.join(' ')); setInterim(''); } else setInterim(r.transcript); },
      err => { if (err !== 'no-speech' && err !== 'aborted') setMicError(err === 'not-allowed' ? 'Hãy cho phép trang web dùng micro.' : `Lỗi micro: ${err}`); },
      () => { if (wantListening.current) { try { rec.start(); } catch { /* ignore */ } } },
    );
    recognizer.current = rec;
    return () => { wantListening.current = false; rec.stop(); stopSpeech(); };
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    startSpeakingExam(examId)
      .then(r => { setPaper(r.exam); setAttemptId(r.attempt_id); })
      .catch((err: unknown) => setError(apiErrorMessage(err, 'Không mở được đề thi.')));
  }, [hydrated, isAuthenticated, router, examId]);

  const task: SpeakingTask | undefined = paper?.tasks[idx];

  const beginAnswer = useCallback(() => {
    if (!task) return;
    finals.current = []; setFinalText(''); setInterim(''); setMicError('');
    wantListening.current = true;
    startedAt.current = Date.now();
    recognizer.current?.start();
    setSeconds(task.answer_seconds);
    setPhase('answer');
  }, [task]);

  const beginPrep = useCallback(() => {
    if (!task) return;
    if (task.prep_seconds > 0) { setSeconds(task.prep_seconds); setPhase('prep'); } else beginAnswer();
  }, [task, beginAnswer]);

  // The examiner reads the prompt (not the reference text), then prep / answer starts.
  const listen = useCallback(async () => {
    if (!task) return;
    phaseRef.current = 'listen';          // read-aloud tasks continue synchronously, before the next render
    setPhase('listen');
    // A voice that never ends (no TTS on this device) must not block the test.
    if (task.kind !== 'read_aloud') await Promise.race([playText(task.prompt, { voice: 'male' }), new Promise<void>(r => setTimeout(r, 20000))]);
    if (phaseRef.current === 'listen') beginPrep();
  }, [task, beginPrep]);

  const stopAnswer = useCallback(async () => {
    if (!task || phaseRef.current !== 'answer') return;
    wantListening.current = false;
    recognizer.current?.stop();
    setPhase('saving');
    const duration = Math.min(task.answer_seconds, Math.round((Date.now() - startedAt.current) / 1000));
    const text = [...finals.current, interim].join(' ').trim();
    try {
      const r = await answerSpeakingTask(attemptId, task.id, text, duration);
      setAnswered(a => ({ ...a, [task.id]: r.words }));
    } catch {
      setError('Không lưu được câu trả lời, thử lại phần này nhé.');
    }
    setPhase('between');
  }, [task, attemptId, interim]);

  // Countdown for prep and answer windows.
  useEffect(() => {
    if (phase !== 'prep' && phase !== 'answer') return;
    const t = setInterval(() => {
      setSeconds(s => {
        if (s <= 1) {
          clearInterval(t);
          if (phaseRef.current === 'prep') beginAnswer(); else void stopAnswer();
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [phase, beginAnswer, stopAnswer]);

  const next = () => {
    if (!paper) return;
    if (idx + 1 < paper.tasks.length) { setIdx(idx + 1); setPhase('intro'); window.scrollTo({ top: 0 }); }
  };

  const submit = async () => {
    if (submitting) return;
    setSubmitting(true); setError('');
    try {
      const r = await finishSpeakingExam(attemptId);
      setResult(r); setPhase('result');
      track('speaking_exam_completed', { exam: r.exam, overall: r.overall, fallback: r.fallback });
      if (r.gems_earned > 0) { playSound('success'); confetti({ particleCount: 80, spread: 70, origin: { y: 0.6 } }); }
      window.scrollTo({ top: 0 });
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Không nộp được bài.'));
    } finally { setSubmitting(false); }
  };

  if (error && !paper) {
    return <main className="exam-page"><div className="exam-column"><div className="alert-error"><CircleAlert size={16} /> {error}</div><Link href="/exams" className="btn btn-ghost" style={{ marginTop: 12 }}><ArrowLeft size={16} /> Thư viện đề thi</Link></div></main>;
  }
  if (!paper || !task) return <main className="exam-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={20} /> Đang mở đề…</main>;

  // ── Result ──
  if (phase === 'result' && result) {
    const good = result.gems_earned > 0;
    return (
      <main className="exam-page"><div className="exam-column" style={{ maxWidth: 760 }}>
        <section className="card exam-result-hero">
          <div className="eyebrow">{EXAM_LABEL[result.exam]} · Speaking{result.fallback ? ' · ước tính nhanh' : ''}</div>
          <div className="exam-result-band">{formatSpeakingEstimate(result.exam, result.overall)}</div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap', marginTop: 6 }}>
            <span className="xp-badge"><Star size={13} /> +{result.xp_earned} XP</span>
            {result.gems_earned > 0 && <span className="xp-badge" style={{ background: 'color-mix(in srgb, #7DD3FC 25%, transparent)', color: '#0369A1' }}><Gem size={13} /> +{result.gems_earned}</span>}
          </div>
          <div className="exam-sections">
            {Object.entries(result.criteria).map(([k, v]) => <div key={k}><div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{CRITERIA_VI[k] ?? k}</div><strong>{result.exam === 'ielts' ? v.toFixed(1) : `${v}/5`}</strong></div>)}
          </div>
        </section>
        <Mascot size={64} mood={good ? 'cheer' : 'happy'} say={good ? 'Nói tốt lắm! Xem lại câu sửa để lần sau còn hay hơn.' : 'Nói được là đã thắng rồi. Xem nhận xét từng phần nhé!'} className="league-mascot" />
        {result.fallback && <div className="alert-error" style={{ marginTop: 12 }}><CircleAlert size={16} /> Giám khảo AI đang bận nên đây là ước tính theo độ dài câu trả lời. Thi lại sau để có nhận xét chi tiết.</div>}

        {(result.strengths.length > 0 || result.improvements.length > 0) && (
          <section className="card" style={{ marginTop: 16, display: 'grid', gap: 10 }}>
            {result.strengths.length > 0 && <div><div className="eyebrow">Điểm mạnh</div><ul style={{ margin: '4px 0 0', paddingLeft: 18 }}>{result.strengths.map(s => <li key={s}>{s}</li>)}</ul></div>}
            {result.improvements.length > 0 && <div><div className="eyebrow">Cần cải thiện</div><ul style={{ margin: '4px 0 0', paddingLeft: 18 }}>{result.improvements.map(s => <li key={s}>{s}</li>)}</ul></div>}
            {result.next_band_tips.length > 0 && <div><div className="eyebrow">Để lên band tiếp theo</div><ul style={{ margin: '4px 0 0', paddingLeft: 18 }}>{result.next_band_tips.map(s => <li key={s}>{s}</li>)}</ul></div>}
          </section>
        )}
        {result.tasks.map(t => (
          <section key={t.task_id} className="card" style={{ marginTop: 12, display: 'grid', gap: 8 }}>
            <div className="eyebrow">{t.part}{t.pronunciation != null && ` · phát âm ${t.pronunciation}%`}</div>
            <div style={{ fontWeight: 600 }}>{t.prompt}</div>
            <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>{t.transcript ? `“${t.transcript}”` : '(không có câu trả lời)'}</div>
            {t.comment_vi && <div style={{ fontSize: '0.88rem' }}>{t.comment_vi}</div>}
            {t.corrections.map((c, i) => (
              <div key={i} className="exam-review" data-ok={false} style={{ fontSize: '0.85rem' }}>
                <span style={{ color: 'var(--agen-secondary)' }}>{c.original}</span> → <b style={{ color: 'var(--agen-success)' }}>{c.corrected}</b>
                <button type="button" className="icon-btn" style={{ marginLeft: 6, verticalAlign: 'middle' }} aria-label="Nghe câu sửa" onClick={() => void playText(c.corrected)}><Volume2 size={14} /></button>
              </div>
            ))}
          </section>
        ))}
        <div style={{ display: 'flex', gap: 10, marginTop: 20, flexWrap: 'wrap' }}>
          <Link href="/exams" className="btn btn-primary"><ArrowLeft size={16} /> Thư viện đề thi</Link>
          <Link href="/dashboard" className="btn btn-ghost">Trang chủ</Link>
        </div>
      </div></main>
    );
  }

  // ── Test ──
  const total = paper.tasks.length;
  const answeredCount = Object.keys(answered).length;
  const last = idx === total - 1;
  const liveText = [finalText, interim].filter(Boolean).join(' ');
  return (
    <main className="exam-page">
      <div className="exam-topbar">
        <div style={{ fontWeight: 600, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{paper.title}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{idx + 1}/{total}</span>
          {(phase === 'prep' || phase === 'answer') && <span className="exam-clock" data-low={seconds <= 10}>{phase === 'prep' ? 'Chuẩn bị' : 'Đang nói'} · {seconds}s</span>}
        </div>
      </div>
      <div className="exam-column" style={{ maxWidth: 680 }}>
        {error && <div className="alert-error" style={{ marginBottom: 12 }}><CircleAlert size={16} /> {error}</div>}
        <section className="card" style={{ display: 'grid', gap: 12 }}>
          <div className="eyebrow">{task.part}</div>
          <h2 style={{ margin: 0, fontSize: '1.15rem' }}>{task.prompt}</h2>
          {task.cue.length > 0 && <ul className="speak-cue">{task.cue.map(c => <li key={c}>{c}</li>)}</ul>}
          {task.reference && (phase !== 'intro') && <div className="exam-passage" style={{ fontSize: '1.05rem', lineHeight: 1.7 }}>{task.reference}</div>}
          {task.tip_vi && phase !== 'answer' && <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>💡 {task.tip_vi}</div>}

          {phase === 'intro' && (
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
              <button type="button" className="btn btn-primary" onClick={() => void listen()}><Play size={16} /> {task.kind === 'read_aloud' ? 'Bắt đầu' : 'Nghe giám khảo hỏi'}</button>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{task.prep_seconds ? `${task.prep_seconds}s chuẩn bị · ` : ''}nói tối đa {task.answer_seconds}s</span>
            </div>
          )}
          {phase === 'listen' && <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: 'var(--agen-primary)' }}><Volume2 size={18} className="animate-pulse" /> Giám khảo đang đọc câu hỏi…</div>}
          {phase === 'prep' && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Thời gian chuẩn bị. Nghĩ ý chính, không cần viết câu hoàn chỉnh.</span>
              <button type="button" className="btn btn-outline btn-sm" onClick={beginAnswer}><SkipForward size={14} /> Nói ngay</button>
            </div>
          )}
          {(phase === 'answer' || phase === 'saving') && (
            <div style={{ display: 'grid', gap: 10, justifyItems: 'center' }}>
              <MicButton listening={phase === 'answer'} onClick={() => void stopAnswer()} disabled={phase === 'saving'} size={76} label="Dừng và lưu câu trả lời" />
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{phase === 'saving' ? 'Đang lưu…' : 'Bấm để dừng khi nói xong'}</div>
              <div className="speak-live">{liveText || <span style={{ color: 'var(--text-muted)' }}>Đang nghe… hãy nói to và rõ.</span>}</div>
              {micError && <div className="alert-error"><CircleAlert size={16} /> {micError}</div>}
            </div>
          )}
          {phase === 'between' && (
            <div style={{ display: 'grid', gap: 10 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', color: answered[task.id] ? 'var(--agen-success)' : 'var(--text-muted)' }}>
                {answered[task.id] ? <><Check size={16} /> Đã lưu · {answered[task.id]} từ</> : <><Mic size={16} /> Chưa nghe thấy gì — bạn có thể nói lại.</>}
              </div>
              {liveText && <div className="speak-live" style={{ fontStyle: 'italic' }}>“{liveText}”</div>}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button type="button" className="btn btn-ghost btn-sm" onClick={() => void listen()}>Nói lại</button>
                {last
                  ? <button type="button" className="btn btn-primary" disabled={submitting || answeredCount === 0} onClick={submit}>{submitting ? <LoaderCircle className="animate-spin" size={16} /> : <Send size={16} />} Nộp bài · chấm</button>
                  : <button type="button" className="btn btn-primary" onClick={next}>Phần tiếp <ArrowRight size={16} /></button>}
              </div>
            </div>
          )}
        </section>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 14, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span>Đã trả lời {answeredCount}/{total}</span>
          {phase === 'intro' && idx > 0 && <button type="button" className="btn btn-ghost btn-sm" onClick={next} disabled={last}>Bỏ qua phần này</button>}
        </div>
      </div>
    </main>
  );
}
