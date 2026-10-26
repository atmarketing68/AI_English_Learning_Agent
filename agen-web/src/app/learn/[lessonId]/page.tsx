'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { AnimatePresence, motion } from 'framer-motion';
import {
  getLessonDetail, submitExerciseAnswer, finishLesson, explainMistake,
  type Exercise, type GrammarExplanation, type LessonDetail, type FinishLessonResult,
} from '@/lib/lessonService';
import { notifyActivityCompleted, ActivityUpdateResponse } from '@/lib/services';
import { useAuthStore } from '@/store/authStore';
import { getMyProfile } from '@/lib/services';
import FlipCard from '@/components/ui/FlipCard';
import FillBlank from '@/components/ui/FillBlank';
import { PageSkeleton } from '@/components/Skeleton';
import AudioPlayerTTS from '@/components/AudioPlayerTTS';
import confetti from 'canvas-confetti';
import { playSound } from '@/lib/soundEffects';
import {
  ArrowRight, BookMarked, BookOpen, BookText, ChevronDown, ChevronUp, CircleAlert, CircleCheck, CircleX,
  Flame, Headphones, Lightbulb, PenLine, RotateCcw, Sparkles, Star, Target, Trophy, X, type LucideIcon,
} from 'lucide-react';
import { track } from '@/lib/analytics';
import { RETRYABLE, SKIP_ANSWER, correctAnswerText, isCorrectLocally } from '@/lib/exerciseCheck';
import { DialogueOrder, Dictation, ListenChoose, MatchPairs, SpeakRepeat, WordBank } from '@/components/exercises/InteractiveExercises';
import { getEngagement, type Engagement } from '@/lib/engagementService';
import DailyQuests from '@/components/engagement/DailyQuests';

const tint = (color: string, pct: number) => `color-mix(in srgb, ${color} ${pct}%, transparent)`;

const SKILL_COLORS: Record<string, string> = {
  reading:    'var(--skill-reading)',
  listening:  'var(--skill-listening)',
  grammar:    'var(--agen-primary)',
  vocabulary: 'var(--agen-accent)',
};

const SKILL_ICONS: Record<string, LucideIcon> = {
  reading: BookOpen, listening: Headphones, grammar: PenLine, vocabulary: BookText,
};

const wrongIds = (l: LessonDetail) => l.exercises.filter(e => RETRYABLE.has(e.type) && e.is_correct === false).map(e => e.id);

function vibrate(pattern: number | number[]) {
  try { navigator.vibrate?.(pattern); } catch { /* unsupported */ }
}

// ─── Achievement type (returned from gamification API) ─────────────────────
interface EarnedAchievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  xp_reward: number;
}

// ─── Vocabulary Reference Panel (for vocab lessons) ────────────────────────
interface VocabItem {
  word: string;
  phonetic?: string;
  part_of_speech?: string;
  definition: string;
  translation: string;
  example: string;
  image_hint?: string;
}

function VocabReferencePanel({ items, skillColor }: { items: VocabItem[]; skillColor: string }) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? items : items.slice(0, 3);

  return (
    <div style={{ marginBottom: 24, borderRadius: 16, border: '1px solid var(--border-subtle)', background: 'var(--bg-surface)', overflow: 'hidden' }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{ width: '100%', padding: '14px 18px', background: 'transparent', border: 'none', borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-primary)', fontFamily: 'inherit' }}
      >
        <span style={{ fontWeight: 600, fontSize: '0.95rem', display: 'inline-flex', alignItems: 'center', gap: 8 }}><BookText size={16} color={skillColor} /> Từ vựng trong bài · {items.length} từ</span>
        <span style={{ fontSize: '0.82rem', color: 'var(--agen-primary-light)', display: 'inline-flex', alignItems: 'center', gap: 2 }}>{expanded ? <>Thu gọn <ChevronUp size={14} /></> : <>Xem tất cả <ChevronDown size={14} /></>}</span>
      </button>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {visible.map((v, i) => (
          <div key={i} style={{ padding: '12px 18px', borderTop: i ? '1px solid var(--border-subtle)' : 'none', display: 'flex', gap: 12, alignItems: 'flex-start' }}>
            {v.image_hint && <div style={{ fontSize: '1.3rem', minWidth: 28, textAlign: 'center' }}>{v.image_hint}</div>}
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'baseline', flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{v.word}</span>
                {v.phonetic && <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{v.phonetic}</span>}
                {v.part_of_speech && <span style={{ fontSize: '0.75rem', padding: '1px 6px', borderRadius: 99, background: tint(skillColor, 12), color: skillColor }}>{v.part_of_speech}</span>}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: 2 }}>{v.definition}</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>{v.translation}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', marginTop: 2 }}>&quot;{v.example}&quot;</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Grammar Rule Panel (the rule is taught before it is tested) ───────────
function GrammarRulePanel({ rule, defaultOpen }: { rule: GrammarExplanation; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rule-panel">
      <button type="button" className="rule-panel-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span><Lightbulb size={16} color="var(--agen-accent)" /> Quy tắc ngữ pháp</span>
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>
      {open && (
        <div className="rule-panel-body">
          {rule.rule_vi && <p>{rule.rule_vi}</p>}
          {rule.structure && <div className="rule-structure">{rule.structure}</div>}
          {!!rule.examples?.length && (
            <ul className="rule-examples">
              {rule.examples.map((ex, i) => (
                <li key={i}><strong>{ex.en}</strong><span>{ex.vi}</span></li>
              ))}
            </ul>
          )}
          {!!rule.common_mistakes?.length && (
            <div className="rule-mistakes">
              <div>Lỗi thường gặp</div>
              <ul>{rule.common_mistakes.map((m, i) => <li key={i}>{m}</li>)}</ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Exercise view (declared OUTSIDE parent to avoid "component in render" error)
interface Feedback {
  correct: boolean;
  answerText: string;
  explanation?: string | null;
  canExplain: boolean;     // a first-attempt mistake the AI can explain
}

interface ExerciseViewProps {
  exercise: Exercise;
  picked: string | null;
  feedback: Feedback | null;
  submitting: boolean;
  onAnswer: (answer: string) => void;
}

function ExerciseView({ exercise, picked, feedback, submitting, onAnswer }: ExerciseViewProps) {
  const locked = !!feedback || submitting;

  if (exercise.type === 'flashcard') {
    return (
      <div>
        <FlipCard
          word={exercise.content.word as string}
          phonetic={exercise.content.phonetic as string | undefined}
          definition={exercise.content.definition as string}
          translation={exercise.content.translation as string}
          example={exercise.content.example as string}
          imageHint={exercise.content.image_hint as string | undefined}
        />
        <button className="btn btn-primary btn-full btn-lg" style={{ marginTop: 32 }} disabled={submitting} onClick={() => onAnswer('viewed')}>
          Đã hiểu <ArrowRight size={18} />
        </button>
      </div>
    );
  }

  if (exercise.type === 'fill_blank') {
    return (
      <>
        <div className="eyebrow lesson-eyebrow"><PenLine size={14} /> Chọn từ đúng điền vào chỗ trống</div>
        <FillBlank
          sentence={exercise.content.sentence as string}
          blankWord={exercise.content.blank_word as string}
          options={(exercise.content.options as string[]) || []}
          hint={exercise.content.hint as string | undefined}
          onAnswer={onAnswer}
          disabled={locked}
          result={feedback ? (feedback.correct ? 'correct' : 'wrong') : undefined}
        />
      </>
    );
  }

  if (exercise.type === 'multiple_choice') {
    const options = Object.entries((exercise.content.options as Record<string, string>) || {});
    const correctKey = String(exercise.content.correct_answer ?? '').toUpperCase();
    return (
      <>
        <div className="eyebrow lesson-eyebrow"><Target size={14} /> Chọn đáp án đúng</div>
        <h3 className="lesson-question">{exercise.content.question as string}</h3>
        <div className="choice-grid">
          {options.map(([k, v]) => {
            const state = !feedback ? undefined : k === correctKey ? 'correct' : k === picked ? 'wrong' : 'muted';
            return (
              <button key={k} type="button" className="choice" data-state={state} disabled={locked} onClick={() => onAnswer(k)}>
                <span className="choice-key">{k}</span>
                <span>{v}</span>
              </button>
            );
          })}
        </div>
      </>
    );
  }

  const props = {
    content: exercise.content,
    locked,
    result: feedback ? (feedback.correct ? 'correct' as const : 'wrong' as const) : undefined,
    onAnswer,
  };
  switch (exercise.type) {
    case 'word_bank': return <WordBank {...props} />;
    case 'match_pairs': return <MatchPairs {...props} />;
    case 'listen_choose': return <ListenChoose {...props} />;
    case 'dictation': return <Dictation {...props} />;
    case 'speak_repeat': return <SpeakRepeat {...props} />;
    case 'dialogue_order': return <DialogueOrder {...props} />;
    default: return <div className="alert-error"><CircleAlert size={16} /> Dạng bài này chưa được hỗ trợ.</div>;
  }
}

// ─── Main Page ──────────────────────────────────────────────────────────────
type Mode = 'main' | 'retry-intro' | 'retry' | 'ready';

export default function LessonPlayerPage() {
  const params = useParams();
  const lessonId = params.lessonId as string;

  const { setLearner } = useAuthStore();
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [mode, setMode] = useState<Mode>('main');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [retryQueue, setRetryQueue] = useState<string[]>([]);
  const [attempt, setAttempt] = useState(0);              // re-keys the view on every new question
  const [picked, setPicked] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [aiExplain, setAiExplain] = useState<{ loading: boolean; text?: string; fromAi?: boolean; error?: string } | null>(null);
  const [combo, setCombo] = useState(0);
  const [bestCombo, setBestCombo] = useState(0);
  const [fixedCount, setFixedCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [newAchievements, setNewAchievements] = useState<EarnedAchievement[]>([]);
  const [activityResult, setActivityResult] = useState<ActivityUpdateResponse | null>(null);
  const [finishResult, setFinishResult] = useState<FinishLessonResult | null>(null);
  const [engagement, setEngagement] = useState<Engagement | null>(null);

  const isSplitScreen = lesson?.skill === 'reading' || lesson?.skill === 'listening';

  useEffect(() => {
    if (!lessonId) return;
    getLessonDetail(lessonId)
      .then(data => {
        setLesson(data);
        if (data.status !== 'completed') track('lesson_started', { skill: data.skill, level: data.level });
        if (data.status === 'in_progress') {
          const nextIdx = data.exercises.findIndex(e => e.user_answer == null);
          if (nextIdx !== -1) {
            setCurrentIndex(nextIdx);
          } else {
            // Everything answered but never finished: go straight to fixing mistakes.
            const wrong = wrongIds(data);
            setRetryQueue(wrong);
            setMode(wrong.length ? 'retry-intro' : 'ready');
          }
        }
      })
      .catch(() => setError('Không thể tải bài học'))
      .finally(() => setLoading(false));
  }, [lessonId]);

  const current: Exercise | undefined = !lesson ? undefined
    : mode === 'retry' ? lesson.exercises.find(e => e.id === retryQueue[0])
    : mode === 'main' ? lesson.exercises[currentIndex]
    : undefined;

  const resetQuestion = () => {
    setPicked(null);
    setFeedback(null);
    setAiExplain(null);
    setError('');
    setAttempt(a => a + 1);
  };

  const scoreAnswer = (correct: boolean) => {
    if (correct) {
      const next = combo + 1;
      setCombo(next);
      setBestCombo(b => Math.max(b, next));
      playSound('success');
      if (next > 0 && next % 5 === 0) {
        confetti({ particleCount: 40, spread: 50, origin: { y: 0.8 }, colors: ['#D97A00', '#FF9F0A'] });
      }
    } else {
      setCombo(0);
      playSound('error');
      vibrate([40, 40, 40]);
    }
  };

  const finish = useCallback(async () => {
    if (!lesson) return;
    setSubmitting(true);
    try {
      const fin = await finishLesson(lesson.id);
      playSound('success');
      confetti({ particleCount: 90, spread: 70, origin: { y: 0.6 }, colors: ['#0071E3', '#1F9D55', '#D97A00', '#8E4EC6'] });
      setFinishResult(fin);
      const updated = await getLessonDetail(lesson.id);
      setLesson(updated);
      track('lesson_completed', { skill: updated.skill, level: updated.level, score: updated.score });

      // Notify backend → streak + daily challenge + achievements in one call
      const result = await notifyActivityCompleted(lesson.skill);
      setActivityResult(result);
      if (result.newly_earned_achievements.length > 0) {
        setNewAchievements(result.newly_earned_achievements as EarnedAchievement[]);
      }

      getEngagement().then(setEngagement).catch(() => undefined);

      // Refresh learner profile in store so dashboard shows updated streak/XP
      const freshProfile = await getMyProfile();
      setLearner(freshProfile);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Lỗi khi kết thúc bài học');
    } finally {
      setSubmitting(false);
    }
  }, [lesson, setLearner]);

  /** Move on from the current main-round question. */
  const advance = (exercises: Exercise[]) => {
    if (!lesson) return;
    resetQuestion();
    if (currentIndex < exercises.length - 1) {
      setCurrentIndex(currentIndex + 1);
      return;
    }
    const wrong = wrongIds({ ...lesson, exercises });
    if (wrong.length) {
      setRetryQueue(wrong);
      setMode('retry-intro');
    } else {
      finish();
    }
  };

  const handleAnswer = useCallback(async (answer: string) => {
    if (!lesson || !current || feedback || submitting) return;

    // Retry round: answers are checked locally, the first attempt already counted.
    if (mode === 'retry') {
      const correct = isCorrectLocally(current, answer);
      setPicked(answer);
      scoreAnswer(correct);
      setFeedback({
        correct,
        answerText: correctAnswerText(current),
        explanation: current.type === 'multiple_choice' ? (current.content.explanation as string) : null,
        canExplain: false,
      });
      return;
    }

    setSubmitting(true);
    try {
      const res = await submitExerciseAnswer(lesson.id, current.id, answer);
      const exercises = lesson.exercises.map(e => (e.id === current.id ? { ...e, user_answer: answer, is_correct: res.is_correct } : e));
      setLesson({ ...lesson, exercises });
      if (current.type === 'flashcard' || answer === SKIP_ANSWER) {
        setSubmitting(false);
        advance(exercises);
        return;
      }
      setPicked(answer);
      scoreAnswer(res.is_correct);
      setFeedback({
        correct: res.is_correct,
        answerText: correctAnswerText(current),
        // fill_blank's server text only repeats the answer; the hint is shown in the card
        explanation: current.type === 'fill_blank' ? null : res.explanation,
        canExplain: !res.is_correct && ['multiple_choice', 'fill_blank', 'word_bank'].includes(current.type),
      });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Lỗi khi nộp bài');
    } finally {
      setSubmitting(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lesson, current, feedback, submitting, mode, combo]);

  const handleNext = useCallback(() => {
    if (!lesson || !feedback) return;
    if (mode === 'main') {
      advance(lesson.exercises);
      return;
    }
    // Retry: fixed → drop it; still wrong → send it to the back of the queue.
    const [head, ...rest] = retryQueue;
    const queue = feedback.correct ? rest : [...rest, head];
    if (feedback.correct) setFixedCount(n => n + 1);
    resetQuestion();
    setRetryQueue(queue);
    if (!queue.length) {
      track('lesson_retry_completed', { skill: lesson.skill, fixed: fixedCount + 1 });
      finish();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lesson, feedback, mode, retryQueue, fixedCount, finish]);

  const askWhy = async () => {
    if (!lesson || !current || aiExplain?.loading) return;
    setAiExplain({ loading: true });
    track('mistake_explained', { skill: lesson.skill, type: current.type });
    try {
      const res = await explainMistake(lesson.id, current.id);
      setAiExplain({ loading: false, text: res.explanation, fromAi: res.source !== 'fallback' });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setAiExplain({ loading: false, error: detail || 'AI đang bận, bạn thử lại sau nhé.' });
    }
  };

  // Keyboard: A–D / 1–4 answer a multiple-choice question, Enter continues.
  useEffect(() => {
    if (!current || (mode !== 'main' && mode !== 'retry')) return;
    const onKey = (e: KeyboardEvent) => {
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) return;
      if (feedback) {
        if (e.key === 'Enter') { e.preventDefault(); handleNext(); }
        return;
      }
      if (current.type === 'flashcard' && e.key === 'Enter') { e.preventDefault(); handleAnswer('viewed'); return; }
      if (current.type !== 'multiple_choice') return;
      const keys = Object.keys((current.content.options as Record<string, string>) || {});
      const byLetter = e.key.toUpperCase();
      const key = keys.includes(byLetter) ? byLetter : keys[Number(e.key) - 1];
      if (key) handleAnswer(key);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [current, mode, feedback, handleNext, handleAnswer]);

  if (loading) return <PageSkeleton maxWidth={720} cards={2} />;
  if (!lesson) return <div style={{ padding: 40, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8, color: 'var(--text-secondary)' }}><CircleAlert size={18} /> {error || 'Bài học không tồn tại'}</div>;

  // ─── Completion Screen ───────────────────────────────────────────────────────
  if (lesson.status === 'completed') {
    const skillColor = SKILL_COLORS[lesson.skill] || 'var(--agen-primary)';
    return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
        <div className="card animate-bounce-in" style={{ maxWidth: 500, width: '100%', textAlign: 'center', padding: 'clamp(24px, 5vw, 40px)', border: 'none', boxShadow: 'var(--shadow-md)' }}>
          <CircleCheck size={44} strokeWidth={1.5} color="var(--agen-success)" style={{ marginBottom: 14 }} />
          <h2 style={{ marginBottom: 6 }}>Hoàn thành bài học</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: 24 }}>{lesson.title}</p>
          <div style={{ fontSize: '4.5rem', fontWeight: 700, letterSpacing: '-0.04em', lineHeight: 1, color: skillColor, marginBottom: 16 }}>
            {lesson.score}%
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 10, marginBottom: 28, flexWrap: 'wrap' }}>
            <span className="xp-badge"><Star size={13} fill="currentColor" /> +{lesson.xp_earned} XP</span>
            <span className="xp-badge">{lesson.correct_exercises}/{lesson.total_exercises} câu đúng</span>
            {bestCombo >= 2 && <span className="xp-badge"><Flame size={13} color="var(--agen-accent)" /> Combo {bestCombo}</span>}
            {fixedCount > 0 && <span className="xp-badge"><RotateCcw size={13} /> Đã sửa {fixedCount} lỗi</span>}
          </div>

          {!!finishResult?.words_saved && (
            <Link href="/vocabulary" className="animate-fade-in-up" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 20, fontSize: '0.9rem', opacity: 1 }}>
              <BookMarked size={16} /> Đã lưu {finishResult.words_saved} từ mới vào Sổ từ vựng
            </Link>
          )}

          {/* Streak & Daily Challenge result */}
          {activityResult && (
            <div className="animate-fade-in-up" style={{ marginBottom: 24, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              <div className="streak-badge" style={{ padding: '8px 14px', fontSize: '0.88rem' }}>
                <Flame size={14} /> Chuỗi {activityResult.current_streak} ngày
                {activityResult.current_streak > 1 && <span style={{ marginLeft: 6, fontSize: '0.75rem', color: 'var(--text-muted)' }}>+1 hôm nay!</span>}
              </div>
            </div>
          )}

          {engagement && (
            <div className="animate-fade-in-up" style={{ marginBottom: 24, textAlign: 'left' }}>
              <DailyQuests state={engagement} onChange={setEngagement} compact />
            </div>
          )}

          {newAchievements.length > 0 && (
            <div className="animate-fade-in-up" style={{ marginBottom: 32, textAlign: 'left', background: 'var(--bg-elevated)', padding: 'var(--spacing-md)', borderRadius: 'var(--radius-lg)' }}>
              <div style={{ fontWeight: 600, marginBottom: 'var(--spacing-sm)', display: 'flex', alignItems: 'center', gap: 6 }}><Trophy size={16} color="var(--agen-accent)" /> Thành tựu mới</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {newAchievements.map(ach => (
                  <div key={ach.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: 10, background: 'var(--bg-surface)', borderRadius: 12 }}>
                    <div style={{ fontSize: '1.6rem' }}>{ach.icon}</div>
                    <div>
                      <div style={{ fontWeight: 600 }}>{ach.name}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{ach.description} (+{ach.xp_reward} XP)</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AGEN Coach adaptive recommendation */}
          {finishResult?.adaptive_reason && (
            <div className="animate-fade-in-up" style={{
              marginBottom: 24, textAlign: 'left', padding: 'var(--spacing-md)',
              borderRadius: 'var(--radius-lg)',
              background: 'var(--bg-tint)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <Sparkles size={16} color="var(--agen-primary)" />
                <span style={{ fontWeight: 600, color: 'var(--agen-primary-light)' }}>AI AGENT ENGLISH Coach</span>
              </div>
              <p style={{ fontSize: '0.9rem', lineHeight: 1.5, margin: 0 }}>{finishResult.adaptive_reason}</p>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <Link href="/curriculum" className="btn btn-primary btn-lg btn-full">
              Bài tiếp theo trong lộ trình
            </Link>
            <Link href="/learn" className="btn btn-ghost btn-full">
              Luyện tập tự do
            </Link>
          </div>
        </div>
      </main>
    );
  }

  // ─── Between rounds: fix mistakes / finish ─────────────────────────────────
  if (mode === 'retry-intro' || mode === 'ready' || (mode === 'retry' && !current)) {
    const n = retryQueue.length;
    return (
      <main className="review-shell">
        <div className="card review-end animate-bounce-in">
          {mode === 'retry-intro' ? (
            <>
              <RotateCcw size={40} strokeWidth={1.5} color="var(--agen-accent)" />
              <h2>Sửa {n} câu sai</h2>
              <p>Làm lại ngay những câu vừa sai giúp nhớ lâu hơn nhiều so với chỉ xem đáp án. Điểm bài học đã được tính, không bị trừ thêm.</p>
              <button className="btn btn-primary btn-lg btn-full" onClick={() => { resetQuestion(); setMode('retry'); }} disabled={submitting}>
                Làm lại câu sai <ArrowRight size={18} />
              </button>
              <button className="btn btn-ghost btn-full" onClick={finish} disabled={submitting}>
                {submitting ? 'Đang xử lý…' : 'Bỏ qua, xem kết quả'}
              </button>
            </>
          ) : (
            <>
              <CircleCheck size={40} strokeWidth={1.5} color="var(--agen-success)" />
              <h2>Sẵn sàng hoàn thành</h2>
              <p>Bạn đã làm xong tất cả câu hỏi của bài này.</p>
              <button className="btn btn-primary btn-lg btn-full" onClick={finish} disabled={submitting}>
                {submitting ? 'Đang xử lý…' : 'Xem kết quả'}
              </button>
            </>
          )}
          {error && <div className="alert-error"><CircleAlert size={16} /> {error}</div>}
        </div>
      </main>
    );
  }

  if (!current) return null;

  // ─── Player View ─────────────────────────────────────────────────────────────
  const total = lesson.exercises.length;
  const answeredMain = currentIndex + (feedback && mode === 'main' ? 1 : 0);
  const progress = mode === 'retry' ? 100 : (answeredMain / total) * 100;
  const skillColor = SKILL_COLORS[lesson.skill] || 'var(--agen-primary)';
  const SkillIcon = SKILL_ICONS[lesson.skill] || BookOpen;

  const topBar = (
    <div className="lesson-topbar">
      <Link href="/learn" aria-label="Thoát bài học" className="review-close"><X size={20} /></Link>
      <div className="progress-bar" style={{ flex: 1 }}>
        <motion.div className="progress-fill" style={{ background: skillColor }} animate={{ width: `${progress}%` }} transition={{ duration: 0.4 }} />
      </div>
      <AnimatePresence>
        {combo >= 2 && (
          <motion.span key={combo} className="combo-chip" initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.6, opacity: 0 }}>
            <Flame size={14} /> {combo}
          </motion.span>
        )}
      </AnimatePresence>
      <span className="lesson-counter">
        {mode === 'retry' ? <><RotateCcw size={14} /> còn {retryQueue.length}</> : <><SkillIcon size={14} color={skillColor} /> {Math.min(currentIndex + 1, total)}/{total}</>}
      </span>
    </div>
  );

  const exercise = (
    <AnimatePresence mode="wait">
      <motion.div
        key={`${current.id}-${attempt}`}
        initial={{ opacity: 0, x: 24 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -24 }}
        transition={{ duration: 0.2 }}
      >
        {mode === 'retry' && <div className="retry-banner"><RotateCcw size={14} /> Sửa lỗi sai</div>}
        <ExerciseView exercise={current} picked={picked} feedback={feedback} submitting={submitting} onAnswer={handleAnswer} />
        {error && <div className="alert-error" style={{ marginTop: 16 }}><CircleAlert size={16} /> {error}</div>}
      </motion.div>
    </AnimatePresence>
  );

  const sheet = (
    <AnimatePresence>
      {feedback && (
        <motion.div
          className="review-feedback"
          data-correct={feedback.correct}
          initial={{ y: '100%' }}
          animate={{ y: 0 }}
          exit={{ y: '100%' }}
          transition={{ type: 'spring', stiffness: 380, damping: 34 }}
        >
          <div className="review-feedback-inner">
            <div className="review-feedback-title">
              {feedback.correct
                ? <><CircleCheck size={20} /> {combo >= 3 ? `Tuyệt vời! Combo ${combo}` : 'Chính xác!'}</>
                : <><CircleX size={20} /> {feedback.answerText ? `Đáp án đúng: ${feedback.answerText}` : 'Chưa đúng'}</>}
            </div>
            {feedback.explanation && <p>{feedback.explanation}</p>}

            {!feedback.correct && feedback.canExplain && (
              aiExplain?.text ? (
                <div className="ai-explain">{aiExplain.fromAi ? <Sparkles size={15} /> : <Lightbulb size={15} />} <span>{aiExplain.text}</span></div>
              ) : (
                <button type="button" className="ai-explain-btn" onClick={askWhy} disabled={aiExplain?.loading}>
                  <Sparkles size={15} /> {aiExplain?.loading ? 'AI đang phân tích…' : 'Vì sao sai?'}
                </button>
              )
            )}
            {aiExplain?.error && <p className="ai-explain-error">{aiExplain.error}</p>}
            {!feedback.correct && mode === 'main' && <div className="review-schedule">Câu này sẽ được làm lại ở cuối bài và lưu vào Sổ lỗi sai.</div>}

            <button className="btn btn-primary btn-lg btn-full" style={{ marginTop: 12 }} onClick={handleNext} disabled={submitting} autoFocus>
              {submitting ? 'Đang xử lý…' : 'Tiếp tục'} <ArrowRight size={18} />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  // ─── Split-Screen Layout (Reading / Listening) ───────────────────────────────
  if (isSplitScreen) {
    return (
      <main className="lesson-split-shell">
        <div className="lesson-split-bar">{topBar}</div>

        <div className="lesson-split">
          {/* Passage / Audio */}
          <div className="lesson-split-passage">
            <div style={{ marginBottom: 16 }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 500, color: skillColor, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <SkillIcon size={14} /> {lesson.skill === 'listening' ? 'Nghe hiểu' : 'Đọc hiểu'}
              </span>
              <h3 style={{ marginTop: 6, marginBottom: 4 }}>{lesson.title}</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{lesson.summary}</p>
            </div>

            {lesson.skill === 'listening' && lesson.content && (
              <AudioPlayerTTS
                text={lesson.content.text}
                scriptLines={lesson.content.script_lines}
                knownWords={lesson.content.vocabulary_highlights}
                lessonId={lesson.id}
              />
            )}

            {lesson.content?.text && (
              <div style={{ padding: 24, background: 'var(--bg-surface)', borderRadius: 16, border: '1px solid var(--border-subtle)', lineHeight: 1.75, fontSize: '1.05rem', color: 'var(--text-primary)', marginBottom: 16 }}>
                {lesson.content.text}
              </div>
            )}

            {lesson.content?.vocabulary_highlights && lesson.content.vocabulary_highlights.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontWeight: 600, marginBottom: 10, fontSize: '0.92rem' }}>Từ vựng nổi bật</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {lesson.content.vocabulary_highlights.map((v, i) => (
                    <div key={i} style={{ padding: '6px 12px', background: 'var(--bg-surface)', borderRadius: 99, border: '1px solid var(--border-subtle)', fontSize: '0.85rem' }}>
                      <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{v.word}</span>
                      <span style={{ color: 'var(--text-muted)', marginLeft: 6 }}>— {v.definition}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Questions */}
          <div className="lesson-split-questions">{exercise}</div>
        </div>
        {sheet}
      </main>
    );
  }

  // ─── Standard Layout (Vocabulary / Grammar) ──────────────────────────────────
  const rule = lesson.content?.explanation;
  return (
    <main className="lesson-shell">
      <div className="lesson-column">
        {topBar}

        {mode === 'main' && currentIndex === 0 && !feedback && lesson.summary && (
          <div className="lesson-intro">{lesson.summary}</div>
        )}

        {mode === 'main' && rule && <GrammarRulePanel key={currentIndex === 0 ? 'intro' : 'later'} rule={rule} defaultOpen={currentIndex === 0} />}

        {/* Vocabulary reference panel — shown when lesson has vocab content */}
        {mode === 'main' && current.type === 'flashcard' && lesson.skill === 'vocabulary' && lesson.content?.vocabulary && lesson.content.vocabulary.length > 0 && (
          <VocabReferencePanel items={lesson.content.vocabulary} skillColor={skillColor} />
        )}

        {exercise}
      </div>
      {sheet}
    </main>
  );
}
