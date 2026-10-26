'use client';

/** G3 · Khoá theo mục tiêu — IELTS, TOEIC, phỏng vấn. */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ChevronRight, CircleAlert, Sparkles, Target } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { getTracks, type TrackSummary } from '@/lib/curriculumService';
import { PageSkeleton } from '@/components/Skeleton';

export default function TracksPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [tracks, setTracks] = useState<TrackSummary[] | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getTracks().then(setTracks).catch(() => setError('Không tải được danh sách khoá học.'));
  }, [hydrated, isAuthenticated, router]);

  return (
    <main className="tracks-page">
      <div className="tracks-column">
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Trang chủ</Link>
        <div className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: 6 }}><Target size={14} /> Khoá theo mục tiêu</div>
        <h1 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.4rem)', margin: '4px 0 6px' }}>Học đúng thứ bạn cần</h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>
          Mỗi khoá là một chuỗi bài học theo thứ tự, bám sát dạng đề hoặc tình huống thật. Bài tiếp theo mở khoá khi bạn hoàn thành bài trước.
        </p>
        {error && <div className="alert-error" style={{ marginBottom: 16 }}><CircleAlert size={16} /> {error}</div>}
        {!tracks && !error && <PageSkeleton cards={3} />}
        <div className="tracks-grid">
          {tracks?.map(t => (
            <Link key={t.id} href={`/tracks/${t.id}`} className="card card-hover track-card" style={{ opacity: 1 }}>
              <div className="track-card-head">
                <span className="track-emoji" aria-hidden>{t.emoji}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="track-title">{t.title_vi}</div>
                  <div className="track-sub">{t.title_en} · mục tiêu {t.target_level}</div>
                </div>
                <ChevronRight size={18} color="var(--text-muted)" />
              </div>
              <p className="track-desc">{t.description_vi}</p>
              <div className="track-meta">
                {t.recommended && <span className="scenario-flag"><Sparkles size={12} /> Hợp mục tiêu của bạn</span>}
                <span>{t.completed_lessons}/{t.total_lessons} bài</span>
              </div>
              <div className="progress-bar" style={{ height: 6 }}><div className="progress-fill" style={{ width: `${t.progress_pct}%` }} /></div>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
