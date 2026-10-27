'use client';
import PageBanner from '@/components/ui/PageBanner';

/** G10 · Thư viện podcast / video ngắn: nghe hội thoại thật, bấm từ để tra, trả lời câu hỏi. */
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowRight, CheckCircle2, CircleAlert, Clock, Headphones, PlayCircle, Trophy } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { listEpisodes, type EpisodeSummary } from '@/lib/mediaService';
import { PageSkeleton } from '@/components/Skeleton';
import Mascot from '@/components/ui/Mascot';

const LEVELS = ['Tất cả', 'A2', 'B1', 'B2'] as const;

export default function ListenLibraryPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [episodes, setEpisodes] = useState<EpisodeSummary[] | null>(null);
  const [level, setLevel] = useState<(typeof LEVELS)[number]>('Tất cả');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    listEpisodes().then(setEpisodes).catch(() => setError('Không tải được thư viện.'));
  }, [hydrated, isAuthenticated, router]);

  const shown = useMemo(() => (episodes ?? []).filter(e => level === 'Tất cả' || e.level === level), [episodes, level]);
  if (!episodes) return <main className="friends-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={3} />}</main>;
  const done = episodes.filter(e => e.completed).length;

  return (
    <main className="friends-page">
      <div className="friends-column" style={{ maxWidth: 820 }}>
        <PageBanner image="banner-listen" priority />
        <section className="card friends-hero">
          <span className="icon-tile" style={{ width: 56, height: 56, borderRadius: 18, background: 'var(--bg-tint)', color: 'var(--skill-listening)' }}><Headphones size={28} strokeWidth={1.7} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow">Podcast & video</div>
            <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>Nghe chuyện thật, học từ thật</h1>
            <p style={{ margin: 0, fontSize: '0.9rem' }}>Mỗi tập 3–5 phút có lời thoại song ngữ: chạm vào bất kỳ từ nào để xem nghĩa và lưu vào sổ từ. Đã nghe {done}/{episodes.length} tập.</p>
          </div>
        </section>
        <Mascot size={64} mood="happy" say="Nghe 1 lần không xem chữ, rồi bật lời thoại nghe lại nhé!" className="league-mascot" />

        <div className="segmented" style={{ margin: '16px 0' }} role="group" aria-label="Lọc theo trình độ">
          {LEVELS.map(l => <button key={l} type="button" aria-pressed={level === l} onClick={() => setLevel(l)}>{l}</button>)}
        </div>

        <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
          {shown.map(e => (
            <Link key={e.id} href={`/listen/${e.id}`} className="card exam-card media-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="icon-tile" style={{ background: 'var(--bg-tint)', color: 'var(--skill-listening)' }}>{e.has_video ? <PlayCircle size={18} /> : <Headphones size={18} />}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600 }}>{e.title}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <span>{e.level}</span><span><Clock size={12} /> {e.minutes} phút</span><span>{e.topic}</span>
                  </div>
                </div>
                {e.completed && (e.best_score === 100 ? <span className="xp-badge"><Trophy size={13} /> 100%</span> : <CheckCircle2 size={18} color="var(--agen-success)" aria-label="Đã nghe" />)}
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '10px 0 12px', flex: 1 }}><b style={{ color: 'var(--text-primary)' }}>{e.title_vi}.</b> {e.description_vi}</p>
              <span className="btn btn-outline btn-sm" style={{ alignSelf: 'flex-start' }}>{e.completed ? `Nghe lại · tốt nhất ${Math.round(e.best_score ?? 0)}%` : 'Nghe ngay'} <ArrowRight size={14} /></span>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
