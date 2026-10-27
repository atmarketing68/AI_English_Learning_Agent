'use client';
import PageBanner from '@/components/ui/PageBanner';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { AnimatePresence, motion } from 'framer-motion';
import {
  ArrowRight, BookMarked, Brain, CircleAlert, CircleCheck, CircleX, Flame, PartyPopper,
  RotateCcw, Star, Target, Volume2, X, Zap,
} from 'lucide-react';
import { useAuthStore, useAuthHydrated } from '@/store/authStore';
import { PageSkeleton } from '@/components/Skeleton';
import { playSound } from '@/lib/soundEffects';
import { speakText } from '@/lib/speechService';
import { track } from '@/lib/analytics';
import { getEngagement, type Engagement } from '@/lib/engagementService';
import DailyQuests from '@/components/engagement/DailyQuests';
import {
  answerReview, getReviewSession, getReviewSummary, intervalLabel, parseUtc,
  type ReviewAnswerResult, type ReviewQuestion, type ReviewSummary,
} from '@/lib/reviewService';

const PROMPT_LABEL: Record<ReviewQuestion['prompt_type'], string> = {
  meaning: 'Chọn nghĩa đúng của từ',
  word: 'Từ tiếng Anh nào có nghĩa là',
  mistake: 'Sửa lỗi sai lần trước',
};

interface Stats { answered: number; correct: number; xp: number; combo: number; bestCombo: number }
const EMPTY_STATS: Stats = { answered: 0, correct: 0, xp: 0, combo: 0, bestCombo: 0 };

function vibrate(pattern: number | number[]) {
  try { navigator.vibrate?.(pattern); } catch { /* unsupported */ }
}

export default function ReviewPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const hydrated = useAuthHydrated();

  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [queue, setQueue] = useState<ReviewQuestion[]>([]);
  const [total, setTotal] = useState(0);
  const [phase, setPhase] = useState<'loading' | 'empty' | 'playing' | 'done'>('loading');
  const [picked, setPicked] = useState<string | null>(null);
  const [typed, setTyped] = useState('');
  const [result, setResult] = useState<ReviewAnswerResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState<Stats>(EMPTY_STATS);
  const [engagement, setEngagement] = useState<Engagement | null>(null);
  // Items answered wrong get one more try at the end of the session.
  const retried = useRef<Set<string>>(new Set());

  const current = queue[0];

  // Fetches a session; state is only set from promise callbacks, so it can run in an effect.
  const load = useCallback((ahead = false) => {
    getReviewSession({ ahead })
      .then(async (session) => {
        retried.current = new Set();
        const empty = session.questions.length === 0;
        const nextSummary = empty ? await getReviewSummary() : null;
        setError('');
        setStats(EMPTY_STATS);
        setQueue(session.questions);
        setTotal(session.questions.length);
        if (nextSummary) setSummary(nextSummary);
        setPhase(empty ? 'empty' : 'playing');
        if (!empty) track('review_started', { count: session.questions.length, ahead });
      })
      .catch(() => {
        setError('Không tải được phiên ôn tập. Vui lòng thử lại.');
        setPhase('empty');
      });
  }, []);

  const start = (ahead = false) => {
    setPhase('loading');
    load(ahead);
  };

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    load();
  }, [hydrated, isAuthenticated, router, load]);

  const submit = useCallback(async (answer: string) => {
    if (!current || result || submitting || !answer.trim()) return;
    setPicked(answer);
    setSubmitting(true);
    try {
      const res = await answerReview(current.item_id, current.prompt_type, answer);
      setResult(res);
      setStats((s) => {
        const combo = res.correct ? s.combo + 1 : 0;
        return {
          answered: s.answered + 1,
          correct: s.correct + (res.correct ? 1 : 0),
          xp: s.xp + res.xp_earned,
          combo,
          bestCombo: Math.max(s.bestCombo, combo),
        };
      });
      if (res.correct) {
        playSound('success');
      } else {
        playSound('error');
        vibrate([40, 40, 40]);
      }
      if (current.speak && res.correct) speakText(current.speak);
    } catch {
      setError('Không gửi được câu trả lời. Kiểm tra kết nối rồi thử lại.');
      setPicked(null);
    } finally {
      setSubmitting(false);
    }
  }, [current, result, submitting]);

  const next = useCallback(() => {
    if (!current || !result) return;
    const rest = queue.slice(1);
    if (!result.correct && !retried.current.has(current.item_id)) {
      retried.current.add(current.item_id);
      rest.push(current);
      setTotal((t) => t + 1);
    }
    setQueue(rest);
    setPicked(null);
    setTyped('');
    setResult(null);
    setError('');
    if (!rest.length) {
      setPhase('done');
      track('review_completed', { answered: stats.answered, correct: stats.correct, xp: stats.xp });
      getReviewSummary().then(setSummary).catch(() => undefined);
      getEngagement().then(setEngagement).catch(() => undefined);
    }
  }, [current, queue, result, stats]);

  // Keyboard: 1–4 pick an option, Enter continues.
  useEffect(() => {
    if (phase !== 'playing') return;
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement)?.tagName === 'INPUT') return;
      if (result && e.key === 'Enter') { e.preventDefault(); next(); return; }
      const idx = Number(e.key) - 1;
      if (!result && current?.options[idx]) submit(current.options[idx]);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [phase, result, current, next, submit]);

  if (phase === 'loading') return <PageSkeleton maxWidth={640} cards={2} />;

  // ── Nothing due ─────────────────────────────────────────────────────────────
  if (phase === 'empty') {
    const hasItems = summary && summary.vocab_total + summary.mistake_total > 0;
    return (
      <main className="review-shell" style={{ flexDirection: 'column' }}>
        <div style={{ width: '100%', maxWidth: 880 }}>
          <PageBanner image="banner-review" priority title="Ôn tập" sub="Ôn lại từ và câu đã học đúng lúc bạn sắp quên." />
        </div>
        <div className="card review-end animate-bounce-in">
          {error ? (
            <>
              <CircleAlert size={40} strokeWidth={1.5} color="var(--agen-secondary)" />
              <h2>Có lỗi xảy ra</h2>
              <p>{error}</p>
              <button className="btn btn-primary btn-lg btn-full" onClick={() => start()}>Thử lại</button>
            </>
          ) : hasItems ? (
            <>
              <PartyPopper size={44} strokeWidth={1.5} color="var(--agen-success)" />
              <h2>Bạn đã ôn hết hôm nay</h2>
              <p>
                Trí nhớ cần thời gian để “ngấm”. Lượt ôn tiếp theo
                {summary?.next_due_at ? ` vào ${parseUtc(summary.next_due_at).toLocaleDateString('vi-VN', { weekday: 'long', day: 'numeric', month: 'numeric' })}` : ' sẽ sớm có'}.
              </p>
              <div className="review-stat-row">
                <div><strong>{summary?.vocab_total}</strong><span>từ vựng</span></div>
                <div><strong>{summary?.mistake_total}</strong><span>lỗi sai</span></div>
                <div><strong>{summary?.mastered_count}</strong><span>đã thuộc</span></div>
              </div>
              <button className="btn btn-primary btn-lg btn-full" onClick={() => start(true)}>
                <Zap size={18} /> Luyện thêm (ôn trước)
              </button>
              <Link href="/vocabulary" className="btn btn-ghost btn-full">Mở sổ từ vựng</Link>
            </>
          ) : (
            <>
              <BookMarked size={44} strokeWidth={1.5} color="var(--agen-primary)" />
              <h2>Chưa có gì để ôn</h2>
              <p>Học một bài để AI lưu từ mới và câu làm sai vào sổ. Chúng sẽ tự quay lại đúng lúc bạn sắp quên.</p>
              <Link href="/learn" className="btn btn-primary btn-lg btn-full">Học bài đầu tiên <ArrowRight size={18} /></Link>
            </>
          )}
          <Link href="/dashboard" className="btn btn-ghost btn-full">Về trang chủ</Link>
        </div>
      </main>
    );
  }

  // ── Session finished ───────────────────────────────────────────────────────
  if (phase === 'done') {
    const accuracy = stats.answered ? Math.round((stats.correct / stats.answered) * 100) : 0;
    return (
      <main className="review-shell">
        <div className="card review-end animate-bounce-in">
          <CircleCheck size={44} strokeWidth={1.5} color="var(--agen-success)" />
          <h2>Hoàn thành ôn tập</h2>
          <p>Mỗi lần nhớ lại đúng, khoảng cách tới lần ôn sau sẽ dài hơn.</p>
          <div className="review-stat-row">
            <div><strong>{accuracy}%</strong><span>chính xác</span></div>
            <div><strong>{stats.bestCombo}</strong><span>combo dài nhất</span></div>
            <div><strong>+{stats.xp}</strong><span>XP</span></div>
          </div>
          {engagement && (
            <div style={{ width: '100%', textAlign: 'left', marginBottom: 8 }}>
              <DailyQuests state={engagement} onChange={setEngagement} compact />
            </div>
          )}
          {summary && summary.due_count > 0 ? (
            <button className="btn btn-primary btn-lg btn-full" onClick={() => start()}>
              <RotateCcw size={18} /> Ôn tiếp {summary.due_count} mục
            </button>
          ) : (
            <Link href="/dashboard" className="btn btn-primary btn-lg btn-full">Về trang chủ <ArrowRight size={18} /></Link>
          )}
          <Link href="/vocabulary" className="btn btn-ghost btn-full">Xem sổ từ vựng</Link>
        </div>
      </main>
    );
  }

  // ── Player ───────────────────────────────────────────────────────────────
  const done = total - queue.length;
  const progress = total ? (done / total) * 100 : 0;
  const isVocab = current.kind === 'vocab';

  return (
    <main className="review-shell" style={{ alignItems: 'stretch' }}>
      <div className="review-player">
        <div className="review-topbar">
          <Link href="/dashboard" aria-label="Thoát ôn tập" className="review-close"><X size={20} /></Link>
          <div className="progress-bar" style={{ flex: 1 }}>
            <motion.div className="progress-fill" animate={{ width: `${progress}%` }} transition={{ duration: 0.4 }} />
          </div>
          <AnimatePresence>
            {stats.combo >= 2 && (
              <motion.span
                key={stats.combo}
                className="combo-chip"
                initial={{ scale: 0.6, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.6, opacity: 0 }}
              >
                <Flame size={14} /> {stats.combo}
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        <AnimatePresence mode="wait">
          <motion.section
            key={`${current.item_id}-${done}`}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.22 }}
            className="review-question"
          >
            <div className="eyebrow review-eyebrow">
              {isVocab ? <Brain size={14} /> : <Target size={14} />} {PROMPT_LABEL[current.prompt_type]}
            </div>

            <div className={`review-prompt ${current.prompt_type === 'mistake' ? 'is-sentence' : ''}`}>
              <span>{current.prompt}</span>
              {current.speak && (
                <button type="button" className="review-speak" aria-label="Nghe phát âm" onClick={() => speakText(current.speak!)}>
                  <Volume2 size={20} />
                </button>
              )}
            </div>
            {current.hint && <div className="review-hint">{current.hint}</div>}

            {current.options.length ? (
              <div className={`choice-grid ${isVocab ? 'is-2col' : ''}`}>
                {current.options.map((opt, i) => {
                  const isAnswer = result && opt.trim().toLowerCase() === result.correct_answer.trim().toLowerCase();
                  const state = !result ? undefined : isAnswer ? 'correct' : opt === picked ? 'wrong' : 'muted';
                  return (
                    <button
                      key={opt}
                      type="button"
                      className="choice"
                      data-state={state}
                      disabled={!!result || submitting}
                      onClick={() => submit(opt)}
                    >
                      <span className="choice-key">{i + 1}</span>
                      <span>{opt}</span>
                    </button>
                  );
                })}
              </div>
            ) : (
              <form
                className="review-typed"
                onSubmit={(e) => { e.preventDefault(); submit(typed); }}
              >
                <input
                  className="form-input"
                  value={typed}
                  onChange={(e) => setTyped(e.target.value)}
                  placeholder="Nhập đáp án…"
                  disabled={!!result || submitting}
                  autoFocus
                  autoComplete="off"
                  autoCapitalize="off"
                />
                {!result && <button className="btn btn-primary" disabled={!typed.trim() || submitting}>Kiểm tra</button>}
              </form>
            )}

            {error && <div className="alert-error" style={{ marginTop: 16 }}><CircleAlert size={16} /> {error}</div>}
          </motion.section>
        </AnimatePresence>
      </div>

      <AnimatePresence>
        {result && (
          <motion.div
            className="review-feedback"
            data-correct={result.correct}
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', stiffness: 380, damping: 34 }}
          >
            <div className="review-feedback-inner">
              <div className="review-feedback-title">
                {result.correct
                  ? <><CircleCheck size={20} /> {stats.combo >= 3 ? `Tuyệt! Combo ${stats.combo}` : 'Chính xác'}</>
                  : <><CircleX size={20} /> Đáp án đúng: {result.correct_answer}</>}
                {result.xp_earned > 0 && <span className="xp-badge" style={{ marginLeft: 'auto' }}><Star size={12} fill="currentColor" /> +{result.xp_earned}</span>}
              </div>
              {result.explanation && <p>{result.explanation}</p>}
              {result.example && <p className="review-example">“{result.example}”</p>}
              <div className="review-schedule">
                {result.correct
                  ? <>Ôn lại sau <strong>{intervalLabel(result.interval_days)}</strong>{result.mastered && ' · Đã thuộc'}</>
                  : <>Không sao — câu này sẽ quay lại để bạn thử lại</>}
              </div>
              <button className="btn btn-primary btn-lg btn-full" onClick={next} autoFocus>
                Tiếp tục <ArrowRight size={18} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
