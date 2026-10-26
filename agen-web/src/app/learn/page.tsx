'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore, useAuthHydrated } from '@/store/authStore';
import { generateLesson, getDailyRecommendations, getMyLessons, LessonQuotaError, DailyRecommendation, LessonSummary } from '@/lib/lessonService';
import { startCurriculumLesson } from '@/lib/curriculumService';
import { PageSkeleton } from '@/components/Skeleton';
import LessonGeneratingOverlay from '@/components/LessonGeneratingOverlay';
import { ArrowLeft, BookOpen, BookText, ChevronRight, CircleAlert, Headphones, LayoutGrid, PenLine, type LucideIcon } from 'lucide-react';

const ALL_SKILLS: { id: string; label: string; icon: LucideIcon; color: string }[] = [
  { id: 'all',        label: 'Tất cả',     icon: LayoutGrid, color: 'var(--text-secondary)' },
  { id: 'vocabulary', label: 'Vocabulary', icon: BookText,   color: 'var(--agen-accent)' },
  { id: 'grammar',    label: 'Grammar',    icon: PenLine,    color: 'var(--agen-primary)' },
  { id: 'reading',    label: 'Reading',    icon: BookOpen,   color: 'var(--skill-reading)' },
  { id: 'listening',  label: 'Listening',  icon: Headphones, color: 'var(--skill-listening)' },
];

const skillIcon = (skill: string): LucideIcon => ALL_SKILLS.find(s => s.id === skill)?.icon || BookOpen;

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
  const hydrated = useAuthHydrated();

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
    if (!hydrated) return;
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
  }, [hydrated, isAuthenticated, curriculumCode]);

  // While preparing a curriculum lesson: show the friendly generating overlay,
  // unless generation failed — then show the error with a way back.
  if (curriculumStarting) {
    if (error) return (
      <main style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 'var(--spacing-lg)' }}>
        <div className="card" style={{ maxWidth: 440, textAlign: 'center', padding: 40 }}>
          <CircleAlert size={32} strokeWidth={1.6} color="var(--agen-secondary)" style={{ marginBottom: 12 }} />
          <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>{error}</p>
          <Link href="/curriculum" className="btn btn-ghost"><ArrowLeft size={16} /> Về lộ trình</Link>
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

  if (loading) return <PageSkeleton cards={3} />;

  return (
    <main style={{ padding: 'clamp(24px, 5vw, 48px) var(--page-gutter)', minHeight: '100vh' }}>
      <div className="container" style={{ padding: 0 }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--spacing-xl)' }}>
          <div className="animate-fade-in-up">
            <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}>
              <ArrowLeft size={16} /> Dashboard
            </Link>
            <h1 style={{ fontSize: 'clamp(1.9rem, 4vw, 2.5rem)' }}>Trung tâm học tập</h1>
            <p style={{ color: 'var(--text-muted)', marginTop: 6 }}>Chọn kỹ năng và bắt đầu bài học hôm nay.</p>
          </div>
          <div className="level-badge">{learner?.overall_level}</div>
        </div>

        {error && <div className="alert-error" style={{ marginBottom: 20 }}><CircleAlert size={16} style={{ flexShrink: 0 }} /> {error}</div>}

        {/* Quick-Start: 4 Skill Buttons */}
        <div className="animate-fade-in-up delay-100" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <h3 style={{ marginBottom: 16 }}>Bắt đầu ngay</h3>
          <div className="grid-4" style={{ gap: 'var(--spacing-md)' }}>
            {ALL_SKILLS.filter(s => s.id !== 'all').map(skill => (
              <button
                key={skill.id}
                className="card card-hover"
                disabled={!!generating}
                onClick={() => handleGenerate(skill.id, '')}
                style={{
                  cursor: 'pointer', textAlign: 'left', fontFamily: 'inherit',
                  padding: 20,
                }}
              >
                <span className="icon-tile" style={{ background: `color-mix(in srgb, ${skill.color} 12%, transparent)`, color: skill.color, width: 40, height: 40, marginBottom: 14 }}>
                  <skill.icon size={20} strokeWidth={1.8} />
                </span>
                <div style={{ fontWeight: 600, fontSize: '0.98rem' }}>{skill.label}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 2 }}>
                  {generating === skill.id ? 'Đang tạo…' : 'Tạo bài mới'}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* AI Daily Recommendations */}
        <div className="animate-fade-in-up delay-200" style={{ marginBottom: 'var(--spacing-xl)' }}>
          <h3 style={{ marginBottom: 16 }}>Gợi ý hôm nay</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 'var(--spacing-md)' }}>
            {recommendations.map((rec, i) => {
              const color = SKILL_COLOR_MAP[rec.skill] || 'var(--agen-primary)';
              const RecIcon = skillIcon(rec.skill);
              return (
                <div key={i} className="card" style={{ display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
                    <span className="icon-tile" style={{ background: `color-mix(in srgb, ${color} 12%, transparent)`, color, width: 40, height: 40 }}>
                      <RecIcon size={20} strokeWidth={1.8} />
                    </span>
                    <div>
                      <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{rec.skill}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{rec.topic}</div>
                    </div>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 16, flex: 1 }}>{rec.reason}</p>
                  <button
                    className="btn btn-ghost btn-sm btn-full"
                    disabled={!!generating}
                    onClick={() => handleGenerate(rec.skill, rec.topic)}
                    style={{ color: 'var(--agen-primary-light)' }}
                  >
                    {generating === rec.skill ? 'Đang tạo…' : 'Học ngay'}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Lessons with Skill Filter */}
        <div className="animate-fade-in-up delay-300">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
            <h3>Lịch sử bài học</h3>
            {/* Skill Filter Tabs */}
            <div className="segmented" style={{ overflowX: 'auto', maxWidth: '100%' }}>
              {ALL_SKILLS.map(s => (
                <button
                  key={s.id}
                  onClick={() => setSkillFilter(s.id)}
                  aria-pressed={skillFilter === s.id}
                >
                  {s.label}
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
                const LessonIcon = skillIcon(lesson.skill);
                return (
                  <Link key={lesson.id} href={`/learn/${lesson.id}`} className="card card-hover" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, padding: '14px 18px', opacity: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14, minWidth: 0 }}>
                      <LessonIcon size={20} strokeWidth={1.8} color={color} style={{ flexShrink: 0 }} />
                      <div style={{ minWidth: 0 }}>
                        <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{lesson.title}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                          <span style={{ textTransform: 'capitalize' }}>{lesson.skill}</span>
                          {' · '}{lesson.topic}{' · '}{new Date(lesson.created_at).toLocaleDateString('vi-VN')}
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                      {lesson.status === 'completed' ? (
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{lesson.score}%</span>
                      ) : (
                        <span className="xp-badge" style={{ fontSize: '0.75rem' }}>Đang học</span>
                      )}
                      <ChevronRight size={16} color="var(--text-muted)" />
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
    <Suspense fallback={<PageSkeleton cards={3} />}>
      <LearnHubContent />
    </Suspense>
  );
}
