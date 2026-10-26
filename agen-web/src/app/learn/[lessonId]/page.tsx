'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  getLessonDetail, submitExerciseAnswer, finishLesson,
  LessonDetail, SubmitExerciseResult, FinishLessonResult,
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
import { ArrowRight, BookOpen, BookText, ChevronDown, ChevronUp, CircleAlert, CircleCheck, CircleX, Flame, Headphones, PenLine, Sparkles, Star, Trophy, X, type LucideIcon } from 'lucide-react';
import { track } from '@/lib/analytics';

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

// ─── Exercise Panel (declared OUTSIDE parent to avoid "component in render" error)
interface ExercisePanelProps {
  lesson: LessonDetail;
  currentIndex: number;
  feedback: SubmitExerciseResult | null;
  submitting: boolean;
  onAnswer: (answer: string) => void;
  onNext: () => void;
}

function ExercisePanel({ lesson, currentIndex, feedback, submitting, onAnswer, onNext }: ExercisePanelProps) {
  const currentEx = lesson.exercises[currentIndex];

  return (
    <div className="animate-fade-in-up" key={currentEx.id}>
      {/* Flashcard */}
      {currentEx.type === 'flashcard' && (
        <div>
          <FlipCard
            word={currentEx.content.word as string}
            phonetic={currentEx.content.phonetic as string | undefined}
            definition={currentEx.content.definition as string}
            translation={currentEx.content.translation as string}
            example={currentEx.content.example as string}
            imageHint={currentEx.content.image_hint as string | undefined}
          />
          <button
            className="btn btn-primary btn-full btn-lg"
            style={{ marginTop: 32 }}
            onClick={() => onAnswer('viewed')}
          >
            Đã hiểu <ArrowRight size={18} />
          </button>
        </div>
      )}

      {/* Fill-in-the-blank */}
      {currentEx.type === 'fill_blank' && (
        <FillBlank
          sentence={currentEx.content.sentence as string}
          blankWord={currentEx.content.blank_word as string}
          options={currentEx.content.options as string[]}
          hint={currentEx.content.hint as string | undefined}
          onAnswer={onAnswer}
          disabled={!!feedback || submitting}
        />
      )}

      {/* Multiple Choice */}
      {currentEx.type === 'multiple_choice' && (
        <div className="card">
          <h3 style={{ marginBottom: 20 }}>{currentEx.content.question as string}</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {Object.entries(currentEx.content.options as Record<string, string>).map(([k, v]) => (
              <button
                key={k}
                disabled={!!feedback || submitting}
                onClick={() => onAnswer(k)}
                style={{
                  padding: '14px 18px', textAlign: 'left', borderRadius: 12,
                  border: feedback && k === feedback.correct_answer
                    ? '1.5px solid var(--agen-success)'
                    : '1.5px solid var(--border-subtle)',
                  background: feedback && k === feedback.correct_answer
                    ? 'rgba(52,199,89,0.08)'
                    : 'var(--bg-surface)',
                  color: 'var(--text-primary)', fontFamily: 'inherit', fontSize: '0.95rem',
                  cursor: feedback ? 'default' : 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <span style={{ fontWeight: 600, marginRight: 12, color: 'var(--text-muted)' }}>{k}.</span>{v}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Feedback */}
      {feedback && (
        <div className="animate-bounce-in" style={{ marginTop: 20 }}>
          <div style={{
            padding: 16, borderRadius: 14,
            background: feedback.is_correct ? 'rgba(52,199,89,0.08)' : 'rgba(255,59,48,0.06)',
            marginBottom: 16,
          }}>
            <div style={{ fontWeight: 600, color: feedback.is_correct ? 'var(--agen-success)' : 'var(--agen-secondary)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 6 }}>
              {feedback.is_correct ? <><CircleCheck size={17} /> Chính xác</> : <><CircleX size={17} /> Đáp án đúng: {feedback.correct_answer}</>}
            </div>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{feedback.explanation}</div>
          </div>
          <button className="btn btn-primary btn-full btn-lg" onClick={onNext} disabled={submitting}>
            {submitting
              ? 'Đang xử lý…'
              : currentIndex < lesson.exercises.length - 1
              ? 'Tiếp tục'
              : 'Hoàn thành bài học'}
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────────────
export default function LessonPlayerPage() {
  const params = useParams();
  const lessonId = params.lessonId as string;

  const { setLearner } = useAuthStore();
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [feedback, setFeedback] = useState<SubmitExerciseResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [newAchievements, setNewAchievements] = useState<EarnedAchievement[]>([]);
  const [activityResult, setActivityResult] = useState<ActivityUpdateResponse | null>(null);
  const [finishResult, setFinishResult] = useState<FinishLessonResult | null>(null);

  const isSplitScreen = lesson?.skill === 'reading' || lesson?.skill === 'listening';

  useEffect(() => {
    if (lessonId) {
      getLessonDetail(lessonId)
        .then(data => {
          setLesson(data);
          if (data.status !== 'completed') track('lesson_started', { skill: data.skill, level: data.level });
          if (data.status === 'in_progress') {
            const nextIdx = data.exercises.findIndex(e => e.user_answer == null);
            setCurrentIndex(nextIdx !== -1 ? nextIdx : data.exercises.length - 1);
          }
        })
        .catch(() => setError('Không thể tải bài học'))
        .finally(() => setLoading(false));
    }
  }, [lessonId]);

  const handleAnswer = async (answer: string) => {
    if (!lesson) return;
    const currentEx = lesson.exercises[currentIndex];
    if (currentEx.type === 'flashcard') {
      await submitExerciseAnswer(lesson.id, currentEx.id, 'viewed');
      handleNext();
      return;
    }
    setSubmitting(true);
    try {
      const res = await submitExerciseAnswer(lesson.id, currentEx.id, answer);
      setFeedback(res);
      if (res.is_correct) {
        playSound('success');
      } else {
        playSound('error');
      }
      const updatedExercises = [...lesson.exercises];
      updatedExercises[currentIndex] = { ...currentEx, user_answer: answer, is_correct: res.is_correct };
      setLesson({ ...lesson, exercises: updatedExercises });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Lỗi khi nộp bài');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = async () => {
    setFeedback(null);
    if (!lesson) return;
    if (currentIndex < lesson.exercises.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
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

        // Refresh learner profile in store so dashboard shows updated streak/XP
        const freshProfile = await getMyProfile();
        setLearner(freshProfile);
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setError(detail || 'Lỗi khi kết thúc bài học');
      } finally {
        setSubmitting(false);
      }
    }
  };

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
          <div style={{ display: 'flex', justifyContent: 'center', gap: 10, marginBottom: 28 }}>
            <span className="xp-badge"><Star size={13} fill="currentColor" /> +{lesson.xp_earned} XP</span>
            <span className="xp-badge">{lesson.correct_exercises}/{lesson.total_exercises} câu đúng</span>
          </div>

          {/* Streak & Daily Challenge result */}
          {activityResult && (
            <div className="animate-fade-in-up" style={{ marginBottom: 24, display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              <div className="streak-badge" style={{ padding: '8px 14px', fontSize: '0.88rem' }}>
                <Flame size={14} /> Chuỗi {activityResult.current_streak} ngày
                {activityResult.current_streak > 1 && <span style={{ marginLeft: 6, fontSize: '0.75rem', color: 'var(--text-muted)' }}>+1 hôm nay!</span>}
              </div>
              {activityResult.daily_challenge_completed && (
                <div style={{ padding: '8px 14px', borderRadius: 99, background: 'rgba(52,199,89,0.1)', fontWeight: 500, fontSize: '0.88rem', color: 'var(--agen-success)', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                  <CircleCheck size={14} /> Hoàn thành thử thách ngày
                </div>
              )}
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

  // ─── Player View ─────────────────────────────────────────────────────────────
  const progress = (currentIndex / lesson.total_exercises) * 100;
  const skillColor = SKILL_COLORS[lesson.skill] || 'var(--agen-primary)';
  const SkillIcon = SKILL_ICONS[lesson.skill] || BookOpen;

  const exercisePanelProps: ExercisePanelProps = {
    lesson, currentIndex, feedback, submitting,
    onAnswer: handleAnswer,
    onNext: handleNext,
  };

  // ─── Split-Screen Layout (Reading / Listening) ───────────────────────────────
  if (isSplitScreen) {
    return (
      <main style={{ height: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-base)' }}>
        <div style={{ padding: '12px 24px', background: 'var(--bg-nav)', backdropFilter: 'saturate(180%) blur(20px)', WebkitBackdropFilter: 'saturate(180%) blur(20px)', borderBottom: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', gap: 16, flexShrink: 0 }}>
          <Link href="/learn" aria-label="Đóng" style={{ color: 'var(--text-muted)', display: 'flex' }}><X size={20} /></Link>
          <div style={{ flex: 1 }}>
            <div className="progress-bar" style={{ margin: 0 }}>
              <div className="progress-fill" style={{ width: `${progress}%`, background: skillColor }} />
            </div>
          </div>
          <span style={{ color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.9rem', display: 'inline-flex', alignItems: 'center', gap: 6 }}><SkillIcon size={15} color={skillColor} /> {currentIndex + 1}/{lesson.total_exercises}</span>
        </div>

        <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', overflow: 'hidden' }}>
          {/* Left: Passage / Audio */}
          <div style={{ padding: 24, overflowY: 'auto', borderRight: '1px solid var(--border-subtle)' }}>
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

          {/* Right: Questions */}
          <div style={{ padding: 24, overflowY: 'auto' }}>
            <div style={{ marginBottom: 16, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Câu hỏi {currentIndex + 1} / {lesson.total_exercises}
            </div>
            <ExercisePanel {...exercisePanelProps} />
          </div>
        </div>
      </main>
    );
  }

  // ─── Standard Layout (Vocabulary / Grammar) ──────────────────────────────────
  return (
    <main style={{ minHeight: '100vh', padding: 'var(--spacing-lg)' }}>
      <div className="container" style={{ maxWidth: 640 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <Link href="/learn" aria-label="Đóng" style={{ color: 'var(--text-muted)', display: 'flex' }}><X size={20} /></Link>
          <div style={{ fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 8, textAlign: 'center' }}><SkillIcon size={16} color={skillColor} /> {lesson.title}</div>
          <div style={{ color: 'var(--text-secondary)', fontWeight: 500, fontSize: '0.9rem' }}>{currentIndex + 1} / {lesson.total_exercises}</div>
        </div>
        <div className="progress-bar" style={{ marginBottom: 32 }}>
          <div className="progress-fill" style={{ width: `${progress}%`, background: skillColor }} />
        </div>

        {currentIndex === 0 && lesson.summary && (
          <div style={{ marginBottom: 24, padding: '14px 18px', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)', borderRadius: 14, fontSize: '0.92rem', color: 'var(--text-secondary)' }}>
            {lesson.summary}
          </div>
        )}

        {/* Vocabulary reference panel — shown when lesson has vocab content */}
        {lesson.skill === 'vocabulary' && lesson.content?.vocabulary && lesson.content.vocabulary.length > 0 && (
          <VocabReferencePanel items={lesson.content.vocabulary} skillColor={skillColor} />
        )}

        <ExercisePanel {...exercisePanelProps} />
      </div>
    </main>
  );
}
