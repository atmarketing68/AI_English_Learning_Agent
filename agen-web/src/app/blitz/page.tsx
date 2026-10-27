'use client';
import PageBanner from '@/components/ui/PageBanner';

/**
 * G4 · Blitz 60 giây — pick the meaning of as many words as you can in a minute.
 * Questions come from the learner's notebook first, then the curriculum.
 * Answers are checked locally (speed!) and the summary is posted once at the end.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import confetti from 'canvas-confetti';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeft, CircleAlert, Flame, Gem, LoaderCircle, RotateCcw, Star, Timer, Volume2, Zap } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { getBlitzRound, submitBlitzResult, type BlitzQuestion, type BlitzResult, type BlitzRound } from '@/lib/reviewService';
import { getMyProfile } from '@/lib/services';
import { playText } from '@/lib/speechService';
import { PageSkeleton } from '@/components/Skeleton';
import Mascot, { type MascotMood } from '@/components/ui/Mascot';
import { playSound } from '@/lib/soundEffects';
import { track } from '@/lib/analytics';

type Phase = 'intro' | 'play' | 'done';

function vibrate(pattern: number | number[]) {
  try { navigator.vibrate?.(pattern); } catch { /* unsupported */ }
}

export default function BlitzPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, setLearner } = useAuthStore();
  const [round, setRound] = useState<BlitzRound | null>(null);
  const [phase, setPhase] = useState<Phase>('intro');
  const [idx, setIdx] = useState(0);
  const [left, setLeft] = useState(60);
  const [correct, setCorrect] = useState(0);
  const [answered, setAnswered] = useState(0);
  const [combo, setCombo] = useState(0);
  const [bestCombo, setBestCombo] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [flash, setFlash] = useState<{ ok: boolean; key: number } | null>(null);
  const [result, setResult] = useState<BlitzResult | null>(null);
  const [error, setError] = useState('');
  const startedAt = useRef(0);
  const stats = useRef({ correct: 0, answered: 0 });

  const load = useCallback(() => {
    getBlitzRound().then(setRound).catch(() => setError('Chưa đủ từ để chơi. Học thêm một bài rồi quay lại nhé!'));
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    load();
  }, [hydrated, isAuthenticated, router, load]);

  const finish = useCallback(async () => {
    setPhase('done');
    const seconds = Math.min(60, Math.round((Date.now() - startedAt.current) / 1000));
    const { correct: c, answered: a } = stats.current;
    try {
      const res = await submitBlitzResult({ correct: c, answered: a, seconds });
      setResult(res);
      track('blitz_completed', { correct: c, answered: a, xp: res.xp_earned, gems: res.gems_earned });
      if (c >= 8) confetti({ particleCount: 90, spread: 70, origin: { y: 0.5 }, colors: ['#0EA5E9', '#6C5CE7', '#F59E0B', '#22C55E'] });
      playSound('success');
      getMyProfile().then(setLearner).catch(() => undefined);
    } catch {
      setError('Không lưu được kết quả, nhưng bạn vẫn chơi rất tốt!');
    }
  }, [setLearner]);

  // Countdown driven by the wall clock, so a background tab can't stretch the minute.
  useEffect(() => {
    if (phase !== 'play' || !round) return;
    const t = setInterval(() => {
      const remaining = Math.max(0, round.seconds - Math.round((Date.now() - startedAt.current) / 1000));
      setLeft(remaining);
      if (remaining <= 0) { clearInterval(t); finish(); }
    }, 250);
    return () => clearInterval(t);
  }, [phase, round, finish]);

  const start = () => {
    if (!round) return;
    stats.current = { correct: 0, answered: 0 };
    setIdx(0); setCorrect(0); setAnswered(0); setCombo(0); setBestCombo(0); setPicked(null); setResult(null);
    setLeft(round.seconds);
    startedAt.current = Date.now();
    setPhase('play');
    track('blitz_started', { from_notebook: round.from_notebook });
    playSound('pop');
  };

  const q: BlitzQuestion | undefined = round?.questions[idx];

  const answer = (i: number) => {
    if (!q || picked !== null || phase !== 'play') return;
    const ok = i === q.answer;
    setPicked(i);
    setFlash({ ok, key: Date.now() });
    stats.current.answered += 1;
    setAnswered(stats.current.answered);
    if (ok) {
      stats.current.correct += 1;
      setCorrect(stats.current.correct);
      setCombo(c => { const n = c + 1; setBestCombo(b => Math.max(b, n)); return n; });
      playSound('success');
    } else {
      setCombo(0);
      playSound('error');
      vibrate([40, 40, 40]);
    }
    setTimeout(() => {
      setPicked(null);
      if (!round || idx + 1 >= round.questions.length) finish();
      else setIdx(idx + 1);
    }, ok ? 350 : 800);
  };

  // Keyboard 1–4
  useEffect(() => {
    if (phase !== 'play') return;
    const onKey = (e: KeyboardEvent) => { const n = Number(e.key); if (n >= 1 && n <= 4) answer(n - 1); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  if (!round && !error) return <PageSkeleton maxWidth={640} cards={1} />;

  const urgent = phase === 'play' && left <= 10;
  const mood: MascotMood = phase === 'done' ? (correct >= 10 ? 'cheer' : correct >= 5 ? 'happy' : 'think') : urgent ? 'wow' : 'happy';

  return (
    <main className="blitz-page">
      <div className="blitz-column">
        <div className="blitz-top">
          <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem' }}><ArrowLeft size={16} /> Trang chủ</Link>
          {phase === 'play' && (
            <>
              <div className="blitz-score">
                <span style={{ color: 'var(--agen-success)' }}>✓ {correct}</span>
                {combo >= 2 && <span className="combo-chip"><Flame size={13} /> x{combo}</span>}
              </div>
              <span className="blitz-timer" data-urgent={urgent}><Timer size={20} /> {left}s</span>
            </>
          )}
        </div>

        {error && <div className="alert-error" style={{ marginBottom: 16 }}><CircleAlert size={16} /> {error}</div>}

        {phase === 'intro' && round && (
          <>
            <PageBanner image="banner-blitz" priority />
          <div className="card blitz-intro">
            <Mascot mood="cheer" size={110} say="60 giây, 15 từ. Sẵn sàng chưa?" bubble="top" />
            <span className="icon-tile" style={{ width: 64, height: 64, borderRadius: 20, margin: '12px auto', background: 'color-mix(in srgb, var(--skill-listening) 14%, transparent)', color: 'var(--skill-listening)' }}><Zap size={32} /></span>
            <h1 style={{ fontSize: 'clamp(1.7rem, 5vw, 2.4rem)', marginBottom: 8 }}>Blitz 60 giây</h1>
            <p style={{ color: 'var(--text-secondary)', maxWidth: 420, margin: '0 auto 8px' }}>
              Chọn nghĩa đúng của từ thật nhanh. Mỗi câu đúng +2 XP (tối đa 40 XP/ngày) và +1 đá quý (tối đa 10).
            </p>
            {round.from_notebook > 0 && <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: 20 }}>{round.from_notebook} từ lấy từ Sổ từ vựng của bạn.</p>}
            <button type="button" className="btn btn-primary btn-lg blitz-big-btn" onClick={start}><Zap size={20} /> Bắt đầu</button>
          </div>
          </>
        )}

        {phase === 'play' && q && (
          <>
            <div className="blitz-track" data-urgent={urgent}><div style={{ width: `${(left / round!.seconds) * 100}%` }} /></div>
            <AnimatePresence mode="wait">
              <motion.div key={idx} initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.18 }}>
                <div className="blitz-word">
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Câu {idx + 1}/{round!.questions.length} · nghĩa của từ</div>
                  <h2>
                    {q.prompt}
                    <button type="button" className="icon-btn" aria-label="Nghe" style={{ marginLeft: 8, verticalAlign: 'middle' }} onClick={() => playText(q.prompt)}><Volume2 size={22} /></button>
                  </h2>
                  {q.phonetic && <small>{q.phonetic}</small>}
                </div>
                <div className="blitz-grid">
                  {q.options.map((opt, i) => (
                    <button
                      key={i} type="button" className="blitz-choice"
                      data-state={picked === null ? undefined : i === q.answer ? 'correct' : i === picked ? 'wrong' : undefined}
                      disabled={picked !== null}
                      onClick={() => answer(i)}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </motion.div>
            </AnimatePresence>
            {flash && <div key={flash.key} className="blitz-flash" data-ok={flash.ok} aria-hidden="true" />}
          </>
        )}

        {phase === 'done' && (
          <div className="card blitz-result animate-bounce-in">
            <Mascot mood={mood} size={100} bubble="top"
              say={correct >= 12 ? 'Siêu tốc độ! Bo chịu thua!' : correct >= 8 ? 'Giỏi lắm! Lần sau phá kỷ lục nhé.' : correct >= 4 ? 'Tốt rồi! Ôn thêm sổ từ là lên ngay.' : 'Không sao, chơi lại là nhớ ngay thôi!'} />
            <div className="eyebrow" style={{ marginTop: 12 }}>Kết quả</div>
            <div className="blitz-result-score">{correct}<span style={{ fontSize: '0.4em', color: 'var(--text-muted)' }}>/{answered}</span></div>
            <div className="blitz-result-badges">
              {result ? (
                <>
                  <span className="xp-badge"><Star size={13} fill="currentColor" /> +{result.xp_earned} XP</span>
                  <span className="gems-badge"><Gem size={13} /> +{result.gems_earned}</span>
                  {bestCombo >= 3 && <span className="xp-badge"><Flame size={13} color="var(--agen-accent)" /> Combo {bestCombo}</span>}
                </>
              ) : !error && <span className="xp-badge"><LoaderCircle className="animate-spin" size={13} /> Đang tính thưởng…</span>}
            </div>
            {result && result.daily_xp_left === 0 && <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: 16 }}>Hết XP Blitz hôm nay — vẫn nhận đá quý khi chơi tiếp.</p>}
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
              <button type="button" className="btn btn-primary btn-lg" onClick={() => { setPhase('intro'); setRound(null); setError(''); load(); }}><RotateCcw size={18} /> Chơi lại</button>
              <Link href="/review" className="btn btn-ghost btn-lg">Ôn tập</Link>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
