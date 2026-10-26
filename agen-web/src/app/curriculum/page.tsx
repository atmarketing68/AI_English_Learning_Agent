'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/authStore';
import {
  getCurriculumMap,
  type CurriculumMap,
  type CurriculumLessonNode,
} from '@/lib/curriculumService';
import { PageSkeleton } from '@/components/Skeleton';
import { ArrowLeft, BookOpen, BookText, CircleAlert, CircleCheck, Flag, Headphones, Lock, Mic, PenLine, Play, RotateCcw, type LucideIcon } from 'lucide-react';

const SKILL_ICONS: Record<string, LucideIcon> = {
  vocabulary: BookText, grammar: PenLine, reading: BookOpen,
  listening: Headphones, speaking: Mic, writing: PenLine,
};

const SKILL_COLORS: Record<string, string> = {
  vocabulary: 'var(--agen-accent)',
  grammar: 'var(--agen-primary)',
  reading: 'var(--skill-reading)',
  listening: 'var(--skill-listening)',
  speaking: 'var(--skill-speaking)',
  writing: 'var(--skill-writing)',
};

// ── Lesson row ────────────────────────────────────────────────────────────────
function LessonRow({ lesson }: { lesson: CurriculumLessonNode }) {
  const router = useRouter();
  const color = SKILL_COLORS[lesson.skill] || 'var(--agen-primary)';

  const statusBadge = () => {
    if (lesson.mastered) return <span style={{ color: 'var(--agen-success)', fontSize: '0.85rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}><CircleCheck size={15} /> {lesson.best_score}%</span>;
    if (lesson.status === 'completed') return <span style={{ color: 'var(--text-primary)', fontSize: '0.85rem', fontWeight: 600 }}>{lesson.best_score}%</span>;
    if (lesson.status === 'in_progress') return <span className="xp-badge" style={{ fontSize: '0.72rem' }}>Đang học</span>;
    if (lesson.locked) return <Lock size={16} color="var(--text-muted)" />;
    return <Play size={16} color="var(--agen-primary)" fill="currentColor" />;
  };

  const clickable = !lesson.locked;
  const RowIcon = lesson.is_assessment ? Flag : lesson.is_review ? RotateCcw : (SKILL_ICONS[lesson.skill] || BookOpen);

  return (
    <div
      onClick={() => clickable && router.push(`/learn?code=${encodeURIComponent(lesson.code)}`)}
      className={clickable ? 'card-hover' : ''}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '12px 16px', borderRadius: 12,
        background: 'var(--bg-elevated)',
        opacity: lesson.locked ? 0.5 : 1,
        cursor: clickable ? 'pointer' : 'not-allowed',
        transition: 'all 0.15s',
      }}
    >
      <RowIcon size={20} strokeWidth={1.8} color={color} style={{ flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 500, fontSize: '0.95rem' }}>{lesson.title}</div>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          <span style={{ textTransform: 'capitalize' }}>{lesson.skill}</span>
          {lesson.grammar_focus ? ` · ${lesson.grammar_focus}` : ''}
          {` · Độ khó ${lesson.difficulty}/5`}
        </div>
      </div>
      <div style={{ flexShrink: 0 }}>{statusBadge()}</div>
    </div>
  );
}

// ── Unit block ────────────────────────────────────────────────────────────────
function UnitBlock({ unit }: { unit: CurriculumMap['units'][number] }) {
  const pct = unit.total_count ? Math.round((unit.completed_count / unit.total_count) * 100) : 0;
  return (
    <div className="card animate-fade-in-up">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
        {unit.icon && <span style={{ fontSize: '1.5rem' }}>{unit.icon}</span>}
        <div style={{ flex: 1 }}>
          <h3 style={{ margin: 0 }}>{unit.title}</h3>
          {unit.theme && <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{unit.theme}</div>}
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
          {unit.completed_count}/{unit.total_count}
        </div>
      </div>
      <div className="progress-bar" style={{ height: 6, marginBottom: 'var(--spacing-md)' }}>
        <div className="progress-fill" style={{ width: `${pct}%`, background: 'var(--agen-primary)' }} />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {unit.lessons.map((l) => <LessonRow key={l.id} lesson={l} />)}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function CurriculumPage() {
  const router = useRouter();
  const { isAuthenticated, learner } = useAuthStore();
  const [map, setMap] = useState<CurriculumMap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }
    const level = learner?.overall_level || 'A1';
    getCurriculumMap(level)
      .then(setMap)
      .catch(() => setError('Không thể tải lộ trình học tập.'))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  if (loading) return <PageSkeleton cards={4} />;

  if (error || !map) return (
    <main style={{ padding: 40, textAlign: 'center' }}>
      <p style={{ color: 'var(--agen-secondary)', display: 'inline-flex', alignItems: 'center', gap: 8 }}><CircleAlert size={16} /> {error || 'Không có dữ liệu'}</p>
      <div><Link href="/dashboard" className="btn btn-outline" style={{ marginTop: 16 }}><ArrowLeft size={16} /> Về Dashboard</Link></div>
    </main>
  );

  return (
    <main style={{ minHeight: '100vh', padding: 'clamp(24px, 5vw, 48px) var(--page-gutter)' }}>
      <div className="container" style={{ padding: 0 }}>

        {/* Header */}
        <div className="animate-fade-in-up" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <Link
            href="/dashboard"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginBottom: 16, fontSize: '0.92rem' }}
          >
            <ArrowLeft size={16} /> Dashboard
          </Link>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h1 style={{ margin: 0, fontSize: 'clamp(1.9rem, 4vw, 2.5rem)' }}>Lộ trình học tập</h1>
              <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                Cấp độ <span className="level-badge">{map.level}</span> — học theo thứ tự để mở khóa bài tiếp theo
              </p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 600, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>{map.progress_pct}%</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{map.completed_lessons}/{map.total_lessons} bài</div>
            </div>
          </div>
        </div>

        {/* Overall progress bar */}
        <div className="animate-fade-in-up delay-100" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div className="progress-bar" style={{ height: 8 }}>
            <div className="progress-fill" style={{ width: `${map.progress_pct}%` }} />
          </div>
        </div>

        {/* Units */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 460px), 1fr))', gap: 'var(--spacing-lg)', alignItems: 'start' }}>
          {map.units.map((unit) => <UnitBlock key={unit.id} unit={unit} />)}
        </div>
      </div>
    </main>
  );
}
