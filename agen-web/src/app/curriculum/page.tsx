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

const SKILL_ICONS: Record<string, string> = {
  vocabulary: '📚', grammar: '📝', reading: '📖',
  listening: '🎧', speaking: '🗣️', writing: '✍️',
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
    if (lesson.mastered) return <span style={{ color: 'var(--agen-success)', fontSize: '0.8rem', fontWeight: 700 }}>✅ {lesson.best_score}%</span>;
    if (lesson.status === 'completed') return <span style={{ color, fontSize: '0.8rem', fontWeight: 700 }}>{lesson.best_score}%</span>;
    if (lesson.status === 'in_progress') return <span className="streak-badge" style={{ fontSize: '0.7rem' }}>Đang học</span>;
    if (lesson.locked) return <span style={{ fontSize: '1rem' }}>🔒</span>;
    return <span style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>▶️</span>;
  };

  const clickable = !lesson.locked;

  return (
    <div
      onClick={() => clickable && router.push(`/learn?code=${encodeURIComponent(lesson.code)}`)}
      className={clickable ? 'card-hover' : ''}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '12px 16px', borderRadius: 10,
        background: 'var(--bg-elevated)',
        border: `1px solid ${lesson.locked ? 'var(--border-subtle)' : color + '33'}`,
        opacity: lesson.locked ? 0.55 : 1,
        cursor: clickable ? 'pointer' : 'not-allowed',
        transition: 'all 0.15s',
      }}
    >
      <span style={{ fontSize: '1.4rem' }}>
        {lesson.is_assessment ? '🏁' : lesson.is_review ? '🔁' : (SKILL_ICONS[lesson.skill] || '📌')}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{lesson.title}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span style={{ color, fontWeight: 600, textTransform: 'uppercase' }}>{lesson.skill}</span>
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
    <div className="card animate-fade-in-up" style={{ marginBottom: 'var(--spacing-lg)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
        <span style={{ fontSize: '1.8rem' }}>{unit.icon || '📦'}</span>
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

  if (loading) return <PageSkeleton maxWidth={860} cards={4} />;

  if (error || !map) return (
    <main style={{ padding: 40, textAlign: 'center' }}>
      <p style={{ color: 'var(--agen-secondary)' }}>⚠️ {error || 'Không có dữ liệu'}</p>
      <Link href="/dashboard" className="btn btn-outline" style={{ marginTop: 16 }}>← Về Dashboard</Link>
    </main>
  );

  return (
    <main style={{ minHeight: '100vh', padding: 'var(--spacing-lg)' }}>
      <div className="container" style={{ maxWidth: 760 }}>

        {/* Header */}
        <div className="animate-fade-in-up" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <Link
            href="/dashboard"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 20,
              padding: '8px 16px', borderRadius: 99,
              background: 'var(--bg-elevated)', border: '1px solid var(--border-medium)',
              color: 'var(--text-secondary)', fontWeight: 600, fontSize: '0.9rem',
              textDecoration: 'none', transition: 'all 0.2s',
            }}
            onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--agen-primary)')}
            onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border-medium)')}
          >
            🏠 Về Trang chủ
          </Link>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h2 style={{ margin: 0 }}>🗺️ Lộ trình học tập</h2>
              <p style={{ color: 'var(--text-muted)', marginTop: 4 }}>
                Cấp độ <span className="level-badge">{map.level}</span> — học theo thứ tự để mở khóa bài tiếp theo
              </p>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--agen-primary-light)' }}>{map.progress_pct}%</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{map.completed_lessons}/{map.total_lessons} bài</div>
            </div>
          </div>
        </div>

        {/* Overall progress bar */}
        <div className="animate-fade-in-up delay-100" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <div className="progress-bar" style={{ height: 12 }}>
            <div className="progress-fill" style={{
              width: `${map.progress_pct}%`,
              background: 'linear-gradient(90deg, var(--agen-primary), var(--agen-accent))',
            }} />
          </div>
        </div>

        {/* Units */}
        {map.units.map((unit) => <UnitBlock key={unit.id} unit={unit} />)}
      </div>
    </main>
  );
}
