'use client';

/** G3 · One goal track: modules and lessons in order, next lesson highlighted. */
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, BookOpen, BookText, CircleAlert, CircleCheck, Headphones, Lock, PenLine, Play, type LucideIcon } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { getTrack, type TrackDetail, type TrackLesson } from '@/lib/curriculumService';
import { PageSkeleton } from '@/components/Skeleton';
import { track as trackEvent } from '@/lib/analytics';

const SKILL_ICONS: Record<string, LucideIcon> = { vocabulary: BookText, grammar: PenLine, reading: BookOpen, listening: Headphones };
const SKILL_COLORS: Record<string, string> = {
  vocabulary: 'var(--agen-accent)', grammar: 'var(--agen-primary)', reading: 'var(--skill-reading)', listening: 'var(--skill-listening)',
};
const SKILL_VI: Record<string, string> = { vocabulary: 'Từ vựng', grammar: 'Ngữ pháp', reading: 'Đọc', listening: 'Nghe' };

function LessonRow({ trackId, lesson, isNext }: { trackId: string; lesson: TrackLesson; isNext: boolean }) {
  const router = useRouter();
  const Icon = SKILL_ICONS[lesson.skill] || BookOpen;
  const color = SKILL_COLORS[lesson.skill] || 'var(--agen-primary)';
  const open = () => {
    if (lesson.locked) return;
    trackEvent('track_lesson_started', { track: trackId, code: lesson.code });
    router.push(`/learn?track=${encodeURIComponent(trackId)}&lesson=${encodeURIComponent(lesson.code)}`);
  };
  const badge = lesson.mastered
    ? <span style={{ color: 'var(--agen-success)', fontSize: '0.85rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}><CircleCheck size={15} /> {lesson.best_score}%</span>
    : lesson.status === 'completed' ? <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{lesson.best_score}%</span>
    : lesson.status === 'in_progress' ? <span className="xp-badge" style={{ fontSize: '0.72rem' }}>Đang học</span>
    : lesson.locked ? <Lock size={16} color="var(--text-muted)" />
    : <Play size={16} color="var(--agen-primary)" fill="currentColor" />;
  return (
    <button type="button" className="track-lesson" data-locked={lesson.locked} data-next={isNext} onClick={open} disabled={lesson.locked}>
      <Icon size={20} strokeWidth={1.8} color={color} style={{ flexShrink: 0 }} />
      <span style={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
        <span style={{ display: 'block', fontWeight: 500, fontSize: '0.95rem' }}>{lesson.title_vi}</span>
        <span style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)' }}>{SKILL_VI[lesson.skill] || lesson.skill} · {lesson.level}{isNext ? ' · tiếp theo' : ''}</span>
      </span>
      <span style={{ flexShrink: 0 }}>{badge}</span>
    </button>
  );
}

export default function TrackDetailPage() {
  const { trackId } = useParams<{ trackId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [track, setTrack] = useState<TrackDetail | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getTrack(trackId).then(t => { setTrack(t); trackEvent('track_started', { track: trackId, progress: t.progress_pct }); })
      .catch(() => setError('Không tìm thấy khoá học này.'));
  }, [hydrated, isAuthenticated, router, trackId]);

  if (error) {
    return (
      <main className="tracks-page"><div className="tracks-column">
        <div className="alert-error"><CircleAlert size={16} /> {error}</div>
        <Link href="/tracks" className="btn btn-ghost" style={{ marginTop: 16 }}><ArrowLeft size={16} /> Các khoá mục tiêu</Link>
      </div></main>
    );
  }
  if (!track) return <main className="tracks-page"><div className="tracks-column"><PageSkeleton cards={3} /></div></main>;

  return (
    <main className="tracks-page">
      <div className="tracks-column">
        <Link href="/tracks" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Các khoá mục tiêu</Link>
        <div className="card track-hero">
          <span className="track-emoji" style={{ fontSize: '2.2rem' }} aria-hidden>{track.emoji}</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '0 0 4px' }}>{track.title_vi}</h1>
            <p style={{ color: 'var(--text-secondary)', margin: '0 0 10px', fontSize: '0.92rem' }}>{track.description_vi}</p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              <span className="level-badge">{track.target_level}</span>
              <span>{track.completed_lessons}/{track.total_lessons} bài · {track.progress_pct}%</span>
            </div>
          </div>
          {track.next_lesson_code && (
            <button type="button" className="btn btn-primary" onClick={() => router.push(`/learn?track=${encodeURIComponent(track.id)}&lesson=${encodeURIComponent(track.next_lesson_code!)}`)}>
              {track.completed_lessons ? 'Học tiếp' : 'Bắt đầu'} <ArrowRight size={16} />
            </button>
          )}
        </div>
        <div className="progress-bar" style={{ height: 8, margin: '14px 0 20px' }}><div className="progress-fill" style={{ width: `${track.progress_pct}%` }} /></div>

        <div className="track-modules">
          {track.modules.map((m, i) => (
            <div key={m.code} className="card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <span className="track-module-num">{i + 1}</span>
                <h3 style={{ margin: 0, flex: 1 }}>{m.title_vi}</h3>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>{m.completed_count}/{m.total_count}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {m.lessons.map(l => <LessonRow key={l.code} trackId={track.id} lesson={l} isNext={l.code === track.next_lesson_code} />)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
