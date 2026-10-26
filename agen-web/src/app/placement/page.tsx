'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useAuthHydrated } from '@/store/authStore';
import {
  startPlacement, getPlacementQuestion, submitAnswer, finishPlacement,
  PlacementQuestion, PlacementAnswerRes, PlacementResult,
} from '@/lib/placementService';
import Logo from '@/components/ui/Logo';
import { ArrowRight, BookOpen, BookText, Check, CircleAlert, CircleCheck, CircleX, Gauge, Headphones, Lightbulb, ListChecks, LoaderCircle, PenLine, X, Zap, type LucideIcon } from 'lucide-react';
import { track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

// ──── Sub Components ────────────────────────────────────────────────────────

const SKILL_LABELS: Record<string, { icon: LucideIcon; label: string; color: string }> = {
  vocabulary: { icon: BookText,   label: 'Vocabulary', color: 'var(--skill-writing)' },
  grammar:    { icon: PenLine,    label: 'Grammar',    color: 'var(--agen-primary-light)' },
  reading:    { icon: BookOpen,   label: 'Reading',    color: 'var(--skill-reading)' },
  listening:  { icon: Headphones, label: 'Listening',  color: 'var(--skill-listening)' },
};

function IntroScreen({ onStart, loading }: { onStart: () => void; loading: boolean }) {
  return (
    <div className="card animate-fade-in-up" style={{ maxWidth: 560, width: '100%', textAlign: 'center', padding: 'clamp(24px, 5vw, 44px)', border: 'none', boxShadow: 'var(--shadow-md)' }}>
      <h2 style={{ marginBottom: 12 }}>Bài kiểm tra đầu vào</h2>
      <p style={{ marginBottom: 28, lineHeight: 1.6 }}>
        AI AGENT ENGLISH sẽ đặt <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>10 câu hỏi</strong> về Vocabulary,
        Grammar và Reading để xác định chính xác trình độ của bạn. Kết quả được dùng để tạo{' '}
        <strong style={{ color: 'var(--text-primary)', fontWeight: 600 }}>lộ trình học cá nhân hóa</strong>.
      </p>
      
      <div style={{ display: 'flex', justifyContent: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 28 }}>
        {[
          { icon: ListChecks, text: '10 câu hỏi' },
          { icon: Zap, text: 'Thích ứng' },
          { icon: Gauge, text: 'Kết quả ngay' },
        ].map(item => (
          <div key={item.text} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 14px', fontSize: '0.88rem', borderRadius: 99, background: 'var(--bg-elevated)' }}>
            <item.icon size={15} color="var(--text-secondary)" />
            <span style={{ color: 'var(--text-secondary)' }}>{item.text}</span>
          </div>
        ))}
      </div>

      <button className="btn btn-primary btn-lg btn-full" onClick={onStart} disabled={loading}>
        {loading ? 'Đang chuẩn bị…' : 'Bắt đầu kiểm tra'}
      </button>
      <p style={{ marginTop: 14, fontSize: '0.8rem', color: 'var(--text-muted)' }}>Thời gian hoàn thành: khoảng 5–8 phút</p>
    </div>
  );
}

function QuestionCard({
  question, questionIndex, totalQuestions, onAnswer, submitting, feedback,
}: {
  question: PlacementQuestion;
  questionIndex: number;
  totalQuestions: number;
  onAnswer: (ans: string) => void;
  submitting: boolean;
  feedback: PlacementAnswerRes | null;
}) {
  const [selected, setSelected] = useState<string | null>(null);
  const skill = SKILL_LABELS[question.skill] || { icon: BookOpen, label: question.skill, color: 'var(--text-muted)' };
  const progress = ((questionIndex) / totalQuestions) * 100;

  const handleSelect = (key: string) => {
    if (feedback || submitting) return;
    setSelected(key);
  };

  const handleSubmit = () => {
    if (!selected || submitting || feedback) return;
    onAnswer(selected);
  };

  // Reset selected when question changes — handled by key prop on parent component
  // (key={question.question_index} triggers unmount/remount, clearing local state)

  const getOptionStyle = (key: string) => {
    const base: React.CSSProperties = {
      padding: '14px 18px',
      borderRadius: 'var(--radius-md)',
      cursor: feedback ? 'default' : 'pointer',
      border: '1.5px solid var(--border-subtle)',
      background: 'var(--bg-surface)',
      display: 'flex',
      alignItems: 'flex-start',
      gap: 12,
      transition: 'all 0.2s ease',
      textAlign: 'left' as const,
      width: '100%',
      color: 'var(--text-primary)',
      fontFamily: 'inherit',
      fontSize: '0.95rem',
    };
    if (feedback) {
      if (key === feedback.correct_answer) {
        return { ...base, border: '1.5px solid var(--agen-success)', background: 'rgba(52,199,89,0.08)' };
      }
      if (key === selected && !feedback.is_correct) {
        return { ...base, border: '1.5px solid var(--agen-secondary)', background: 'rgba(255,59,48,0.06)' };
      }
    } else if (selected === key) {
      return { ...base, border: '1.5px solid var(--agen-primary)', background: 'var(--bg-tint)' };
    }
    return base;
  };

  return (
    <div className="animate-fade-in-up" style={{ maxWidth: 620, width: '100%' }}>
      {/* Progress */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          <span style={{ color: skill.color, fontWeight: 500, display: 'inline-flex', alignItems: 'center', gap: 6 }}><skill.icon size={15} /> {skill.label}</span>
          <span>Câu {questionIndex + 1} / {totalQuestions}</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      <div className="card">
        {/* Level badge */}
        <div style={{ marginBottom: 14 }}>
          <span className="level-badge">{question.level}</span>
        </div>

        {/* Passage (reading) */}
        {question.passage && (
          <div style={{ padding: '12px 16px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-elevated)', marginBottom: 16, borderLeft: '3px solid var(--skill-reading)', fontSize: '0.92rem', lineHeight: 1.7, color: 'var(--text-secondary)' }}>
            {question.passage}
          </div>
        )}

        {/* Question */}
        <h3 style={{ marginBottom: 20, fontWeight: 600, lineHeight: 1.5 }}>{question.question}</h3>

        {/* Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
          {Object.entries(question.options).map(([key, value]) => (
            <button key={key} onClick={() => handleSelect(key)} style={getOptionStyle(key)}>
              <span style={{ fontWeight: 700, minWidth: 24, color: selected === key && !feedback ? 'var(--agen-primary-light)' : 'var(--text-muted)' }}>{key}.</span>
              <span>{value}</span>
              {feedback && key === feedback.correct_answer && <Check size={18} style={{ marginLeft: 'auto', color: 'var(--agen-success)', flexShrink: 0 }} />}
              {feedback && key === selected && !feedback.is_correct && key !== feedback.correct_answer && <X size={18} style={{ marginLeft: 'auto', color: 'var(--agen-secondary)', flexShrink: 0 }} />}
            </button>
          ))}
        </div>

        {/* Feedback */}
        {feedback && (
          <div
            className="animate-bounce-in"
            style={{
              padding: '12px 16px',
              borderRadius: 'var(--radius-sm)',
              background: feedback.is_correct ? 'rgba(52,199,89,0.08)' : 'rgba(255,59,48,0.06)',
              marginBottom: 16,
              fontSize: '0.875rem',
              lineHeight: 1.6,
            }}
          >
            <div style={{ fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 6, color: feedback.is_correct ? 'var(--agen-success)' : 'var(--agen-secondary)' }}>
              {feedback.is_correct ? <><CircleCheck size={16} /> Chính xác</> : <><CircleX size={16} /> Chưa đúng</>}
              {feedback.score_delta > 0 && <span style={{ marginLeft: 8, color: 'var(--agen-accent)', fontSize: '0.8rem' }}>+{feedback.score_delta} XP</span>}
            </div>
            <div style={{ color: 'var(--text-secondary)' }}>{feedback.explanation}</div>
          </div>
        )}

        {/* Action Button */}
        {!feedback ? (
          <button className="btn btn-primary btn-full" onClick={handleSubmit} disabled={!selected || submitting}>
            {submitting ? 'Đang chấm…' : 'Xác nhận'}
          </button>
        ) : (
          <button className="btn btn-ghost btn-full" onClick={() => onAnswer('__next__')}>
            {feedback.is_finished ? 'Xem kết quả' : <>Câu tiếp theo <ArrowRight size={16} /></>}
          </button>
        )}
      </div>
    </div>
  );
}

function ResultScreen({ result, onGoToDashboard }: { result: PlacementResult; onGoToDashboard: () => void }) {
  const levelColors: Record<string, string> = {
    PRE_A1: 'var(--text-muted)', A1: 'var(--skill-listening)', A2: 'var(--skill-reading)',
    B1: 'var(--agen-primary)', B2: 'var(--skill-writing)', C1: 'var(--agen-accent)', C2: 'var(--agen-secondary)',
  };
  const color = levelColors[result.overall_level] || 'var(--agen-primary-light)';

  return (
    <div className="animate-bounce-in" style={{ maxWidth: 580, width: '100%', textAlign: 'center' }}>
      {/* Level Hero */}
      <div className="card" style={{ marginBottom: 20, padding: 'var(--spacing-xl)' }}>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: 8 }}>Trình độ của bạn</p>
        <div style={{ fontSize: '4.5rem', fontWeight: 700, letterSpacing: '-0.04em', color, marginBottom: 8, lineHeight: 1 }}>
          {result.overall_level.replace('_', '-')}
        </div>
        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{result.message}</div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginTop: 16 }}>
          <span className="xp-badge">{result.total_correct}/{result.total_questions} câu đúng</span>
          <span className="xp-badge">{result.accuracy_percent}% chính xác</span>
        </div>
      </div>

      {/* Skill breakdown */}
      {Object.keys(result.skill_scores).length > 0 && (
        <div className="card" style={{ marginBottom: 20, textAlign: 'left' }}>
          <h3 style={{ marginBottom: 16 }}>Chi tiết kỹ năng</h3>
          {Object.entries(result.skill_scores).map(([skill, score]) => {
            const meta = SKILL_LABELS[skill] || { icon: BookOpen, label: skill, color: 'var(--text-muted)' };
            return (
              <div key={skill} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 6 }}>
                  <span style={{ color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: 6 }}><meta.icon size={15} color={meta.color} /> {meta.label}</span>
                  <span style={{ fontWeight: 600 }}>{score}%</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${score}%`, background: meta.color }} />
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Recommendations */}
      {result.recommendations.length > 0 && (
        <div className="card" style={{ marginBottom: 20, textAlign: 'left' }}>
          <h3 style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}><Lightbulb size={18} color="var(--agen-accent)" /> Gợi ý của AI AGENT ENGLISH</h3>
          {result.recommendations.map((rec, i) => (
            <div key={i} style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-elevated)', marginBottom: 8, fontSize: '0.875rem', color: 'var(--text-secondary)', display: 'flex', gap: 8 }}>
              <span>•</span><span>{rec}</span>
            </div>
          ))}
        </div>
      )}

      <button className="btn btn-primary btn-lg btn-full" onClick={onGoToDashboard}>
        Bắt đầu lộ trình học của tôi
      </button>
    </div>
  );
}

// ──── Main Page ─────────────────────────────────────────────────────────────
type Phase = 'intro' | 'testing' | 'result';

export default function PlacementPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const hydrated = useAuthHydrated();

  const [phase, setPhase] = useState<Phase>('intro');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<PlacementQuestion | null>(null);
  const [feedback, setFeedback] = useState<PlacementAnswerRes | null>(null);
  const [result, setResult] = useState<PlacementResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [assessmentType] = useState<'baseline' | 'followup'>(() => {
    if (typeof window === 'undefined') return 'baseline';
    return new URLSearchParams(window.location.search).get('type') === 'followup' ? 'followup' : 'baseline';
  });

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) router.push('/login');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, isAuthenticated]);

  const handleStart = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await startPlacement(assessmentType);
      setSessionId(res.session_id);
      track('placement_started', { type: assessmentType });
      const q = await getPlacementQuestion(res.session_id);
      setCurrentQuestion(q);
      setPhase('testing');
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Không thể bắt đầu bài test. Vui lòng thử lại.'));
    } finally {
      setLoading(false);
    }
  };

  const handleAnswer = useCallback(async (answer: string) => {
    if (!sessionId || !currentQuestion) return;

    // "Next" button after feedback
    if (answer === '__next__') {
      if (feedback?.is_finished) {
        // Finish the test
        try {
          const res = await finishPlacement(sessionId);
          setResult(res);
          track('placement_completed', { type: assessmentType, level: res.overall_level, accuracy: res.accuracy_percent });
          setPhase('result');
        } catch (err: unknown) {
          setError(apiErrorMessage(err, 'Lỗi khi tổng hợp kết quả.'));
        }
      } else {
        // Load next question — clear feedback first to avoid stale state
        setFeedback(null);
        setCurrentQuestion(null); // clear current to show loading
        try {
          const q = await getPlacementQuestion(sessionId);
          setCurrentQuestion(q);
        } catch {
          setError('Không thể tải câu hỏi tiếp theo.');
        }
      }
      return;
    }

    // Submit answer
    setSubmitting(true);
    try {
      const res = await submitAnswer(sessionId, answer);
      setFeedback(res);
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Lỗi khi nộp câu trả lời.'));
    } finally {
      setSubmitting(false);
    }
  }, [sessionId, currentQuestion, feedback, assessmentType]);

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
      {/* Logo bar */}
      <div style={{ position: 'absolute', top: 20, left: '50%', transform: 'translateX(-50%)', display: 'flex', alignItems: 'center', gap: 8 }}>
        <Logo size={24} />
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          {assessmentType === 'followup' ? 'Progress Check' : 'Placement Test'}
        </span>
      </div>

      {error && (
        <div className="animate-fade-in-up" style={{ position: 'fixed', top: 20, right: 20, padding: '12px 18px', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', boxShadow: 'var(--shadow-lg)', color: 'var(--agen-secondary)', maxWidth: 340, zIndex: 100, display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.9rem' }}>
          <CircleAlert size={16} style={{ flexShrink: 0 }} /> {error}
          <button onClick={() => setError('')} aria-label="Đóng" style={{ marginLeft: 8, background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex' }}><X size={16} /></button>
        </div>
      )}

      {phase === 'intro' && <IntroScreen onStart={handleStart} loading={loading} />}
      {phase === 'testing' && currentQuestion && (
        <QuestionCard
          key={currentQuestion.question_index}
          question={currentQuestion}
          questionIndex={currentQuestion.question_index}
          totalQuestions={currentQuestion.total_questions}
          onAnswer={handleAnswer}
          submitting={submitting}
          feedback={feedback}
        />
      )}
      {phase === 'testing' && !currentQuestion && (
        <div style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 8 }}><LoaderCircle className="animate-spin" size={18} /> Đang tải câu hỏi…</div>
      )}
      {phase === 'result' && result && (
        <ResultScreen result={result} onGoToDashboard={() => router.push('/dashboard')} />
      )}
    </main>
  );
}
