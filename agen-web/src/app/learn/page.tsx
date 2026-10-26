'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/authStore';
import { generateLesson, getDailyRecommendations, getMyLessons, LessonQuotaError, DailyRecommendation, LessonSummary } from '@/lib/lessonService';
import { startCurriculumLesson } from '@/lib/curriculumService';
import { PageSkeleton } from '@/components/Skeleton';
import LessonGeneratingOverlay from '@/components/LessonGeneratingOverlay';

const ALL_SKILLS = [
  { id: 'all',        label: 'Tất cả',    icon: '📌', color: 'var(--text-secondary)' },
  { id: 'vocabulary', label: 'Vocabulary', icon: '📚', color: 'var(--agen-accent)' },
  { id: 'grammar',    label: 'Grammar',    icon: '📝', color: 'var(--agen-primary)' },
  { id: 'reading',    label: 'Reading',    icon: '📖', color: 'var(--skill-reading)' },
  { id: 'listening',  label: 'Listening',  icon: '🎧', color: 'var(--skill-listening)' },
];

const SKILL_COLOR_MAP: Record<string, string> = {
  vocabulary: 'var(--agen-accent)',
  grammar:    'var(--agen-primary)',
  reading:    'var(--skill-reading)',
  listening:  'var(--skill-listening)',
};

function LearnHubContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const curriculumCode = searchParams.get('code');
  const { isAuthenticated, learner } = useAuthStore();

  const [recommendations, setRecommendations] = useState<DailyRecommendation[]>([]);
  const [recentLessons, setRecentLessons] = useState<LessonSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string>(''); // skill being generated
  // Initialize to true when arriving with a curriculum code so we don't setState in the effect body
  const [curriculumStarting, setCurriculumStarting] = useState(!!curriculumCode);
  const [error, setError] = useState('');
  const [skillFilter, setSkillFilter] = useState<string>('all');

  const handleGenerate = async (skill: string, topic: string) => {
    setGenerating(skill);
    setError('');
    try {
      const lesson = await generateLesson(skill, topic);
      router.push(`/learn/${lesson.id}`);
    } catch (err: unknown) {
      if (err instanceof LessonQuotaError) {
        setError(err.message);
      } else {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setError(detail || 'Lỗi khi tạo bài học.');
      }
      setGenerating('');
    }
  };

  useEffect(() => {
    if (!isAuthenticated) { router.push('/login'); return; }

    // If arriving with a curriculum code, start that node then generate its lesson
    if (curriculumCode) {
      startCurriculumLesson(curriculumCode)
        .then((node) => generateLesson(node.skill, node.topic, curriculumCode))
        .then((lesson) => router.push(`/learn/${lesson.id}`))
        .catch((err: unknown) => {
          if (err instanceof LessonQuotaError) {
            setError(err.message);
          } else {
            const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setError(detail || 'Không thể bắt đầu bài học trong lộ trình.');
          }
          setCurriculumStarting(false);
        });
      return;
    }

    Promise.all([getDailyRecommendations(), getMyLessons()])
      .then(([recs, lessons]) => { setRecommendations(recs); setRecentLessons(lessons); })
      .catch((err) => setError((err as Error).message))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, curriculumCode]);

  // While preparing a curriculum lesson: show the friendly generating overlay,
  // unless generation failed — then show the error with a way back.
  if (curriculumStarting) {
    if (error) return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
        <div className="card" style={{ maxWidth: 440, textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: 12 }}>😕</div>
          <p style={{ color: 'var(--agen-secondary)', marginBottom: 16 }}>⚠️ {error}</p>
          <Link href="/curriculum" className="btn btn-ghost">← Về lộ trình</Link>
        </div>
      </main>
    );
    return <LessonGeneratingOverlay />;
  }

  // Quick-start / recommendation generation in progress.
  if (generating) return <LessonGeneratingOverlay skillLabel={ALL_SKILLS.find(s => s.id === generating)?.label} />;

  const filteredLessons = skillFilter === 'all'
    ? recentLessons
    : recentLessons.filter(l => l.skill === skillFilter);

  if (loading) return <PageSkeleton maxWidth={900} cards={3} />;

  return (
    <main style={{ padding: 'var(--spacing-lg)', minHeight: '100vh' }}>
      <div className="container" style={{ maxWidth: 900 }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-xl)' }}>
          <div className="animate-fade-in-up">
            <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', marginBottom: 12 }}>
              ← Dashboard
            </Link>
            <h2>📚 Trung tâm Học tập</h2>
            <p style={{ color: 'var(--text-muted)' }}>Chọn kỹ năng và bắt đầu bài học hôm nay!</p>
          </div>
          <div className="level-badge">{learner?.overall_level}</div>
        </div>

        {error && <div style={{ padding: 12, background: 'rgba(255,107,107,0.1)', color: 'var(--agen-secondary)', marginBottom: 20, borderRadius: 8 }}>⚠️ {error}</div>}

        {/* Quick-Start: 4 Skill Buttons */}
        <div className="animate-fade-in-up delay-100" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <h3 style={{ marginBottom: 16 }}>⚡ Bắt đầu ngay</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--spacing-md)' }}>
            {ALL_SKILLS.filter(s => s.id !== 'all').map(skill => (
              <button
                key={skill.id}
                className="card card-hover"
                disabled={!!generating}
                onClick={() => handleGenerate(skill.id, '')}
                style={{
                  cursor: 'pointer', textAlign: 'center',
                  border: `1px solid ${skill.color}33`,
                  background: generating === skill.id ? `${skill.color}11` : 'transparent',
                  padding: 20,
                }}
              >
                <div style={{ fontSize: '2.2rem', marginBottom: 8 }}>
                  {generating === skill.id ? '⏳' : skill.icon}
                </div>
                <div style={{ fontWeight: 700, color: skill.color, fontSize: '0.9rem' }}>{skill.label}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  {generating === skill.id ? 'AI đang tạo...' : 'Tạo bài mới'}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* AI Daily Recommendations */}
        <div className="animate-fade-in-up delay-200" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <h3 style={{ marginBottom: 16 }}>🎯 Gợi ý của AI Coach hôm nay</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 'var(--spacing-md)' }}>
            {recommendations.map((rec, i) => {
              const color = SKILL_COLOR_MAP[rec.skill] || 'var(--agen-primary)';
              return (
                <div key={i} className="card card-hover" style={{ display: 'flex', flexDirection: 'column', border: `1px solid ${color}22` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                    <div style={{ fontSize: '2rem' }}>{rec.icon}</div>
                    <div>
                      <div style={{ fontWeight: 700, textTransform: 'capitalize', color }}>{rec.skill}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{rec.topic}</div>
                    </div>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16, flex: 1 }}>{rec.reason}</p>
                  <button
                    className="btn btn-primary btn-sm btn-full"
                    disabled={!!generating}
                    onClick={() => handleGenerate(rec.skill, rec.topic)}
                    style={{ background: color, borderColor: color }}
                  >
                    {generating === rec.skill ? '⏳ Đang tạo AI...' : 'Học ngay'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Lessons with Skill Filter */}
        <div className="animate-fade-in-up delay-300">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3>🕒 Lịch sử bài học</h3>
            {/* Skill Filter Tabs */}
            <div style={{ display: 'flex', gap: 6, background: 'var(--bg-elevated)', padding: 4, borderRadius: 99 }}>
              {ALL_SKILLS.map(s => (
                <button
                  key={s.id}
                  onClick={() => setSkillFilter(s.id)}
                  style={{
                    padding: '5px 14px', borderRadius: 99, border: 'none', cursor: 'pointer',
                    fontWeight: skillFilter === s.id ? 700 : 400,
                    fontSize: '0.8rem',
                    background: skillFilter === s.id ? s.color : 'transparent',
                    color: skillFilter === s.id ? 'white' : 'var(--text-muted)',
                    transition: 'all 0.15s',
                  }}
                >
                  {s.icon} {s.label}
                </button>
              ))}
            </div>
          </div>

          {filteredLessons.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>
              Chưa có bài học {skillFilter !== 'all' ? `"${skillFilter}"` : ''} nào.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {filteredLessons.map(lesson => {
                const color = SKILL_COLOR_MAP[lesson.skill] || 'var(--agen-primary)';
                return (
                  <Link key={lesson.id} href={`/learn/${lesson.id}`} className="card card-hover" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <span style={{ fontSize: '1.4rem' }}>{ALL_SKILLS.find(s => s.id === lesson.skill)?.icon || '📌'}</span>
                      <div>
                        <div style={{ fontWeight: 600 }}>{lesson.title}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          <span style={{ color, fontWeight: 600, textTransform: 'uppercase', fontSize: '0.75rem' }}>{lesson.skill}</span>
                          {' · '}{lesson.topic}{' · '}{new Date(lesson.created_at).toLocaleDateString('vi-VN')}
                        </div>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      {lesson.status === 'completed' ? (
                        <span style={{ fontWeight: 700, fontSize: '1rem', color }}>{lesson.score}%</span>
                      ) : (
                        <span className="streak-badge" style={{ fontSize: '0.75rem' }}>Đang học</span>
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

// useSearchParams requires a Suspense boundary in the App Router
export default function LearnHubPage() {
  return (
    <Suspense fallback={<PageSkeleton maxWidth={900} cards={3} />}>
      <LearnHubContent />
    </Suspense>
  );
}
