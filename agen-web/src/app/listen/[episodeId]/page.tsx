'use client';

/** G10 · Một tập podcast/video: nghe theo giọng từng nhân vật, bấm từ để tra, xem bản dịch, trả lời câu hỏi. */
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Check, CircleAlert, Gem, Languages, LoaderCircle, RotateCcw, Sparkles, X } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { getEpisode, submitEpisode, type Episode, type MediaResult } from '@/lib/mediaService';
import AudioPlayerTTS from '@/components/AudioPlayerTTS';
import { PageSkeleton } from '@/components/Skeleton';
import { track } from '@/lib/analytics';

export default function EpisodePage() {
  const { episodeId } = useParams<{ episodeId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [ep, setEp] = useState<Episode | null>(null);
  const [error, setError] = useState('');
  const [showVi, setShowVi] = useState(false);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<MediaResult | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getEpisode(episodeId).then(e => { setEp(e); track('media_opened', { episode: e.id, level: e.level }); })
      .catch(() => setError('Không tìm thấy tập này.'));
  }, [hydrated, isAuthenticated, router, episodeId]);

  if (!ep) return <main className="friends-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={2} />}</main>;

  const submit = async () => {
    setBusy(true); setError('');
    try {
      const r = await submitEpisode(ep.id, answers);
      setResult(r);
      track('media_submitted', { episode: ep.id, pct: r.pct });
    } catch {
      setError('Chưa nộp được, thử lại nhé.');
    } finally { setBusy(false); }
  };
  const retry = () => { setResult(null); setAnswers({}); };
  const detail = (id: string) => result?.details.find(d => d.id === id);
  const videoSrc = ep.youtube_id
    ? `https://www.youtube-nocookie.com/embed/${ep.youtube_id}?rel=0${ep.start ? `&start=${ep.start}` : ''}${ep.end ? `&end=${ep.end}` : ''}`
    : null;

  return (
    <main className="friends-page">
      <div className="friends-column" style={{ maxWidth: 760 }}>
        <Link href="/listen" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Thư viện</Link>
        <div className="eyebrow">{ep.kind === 'video' ? 'Video' : 'Podcast'} · {ep.level} · {ep.minutes} phút · {ep.topic}</div>
        <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>{ep.title}</h1>
        <p style={{ margin: '0 0 16px', color: 'var(--text-secondary)' }}>{ep.title_vi} — {ep.description_vi}</p>

        {videoSrc && (
          <div className="media-video">
            <iframe src={videoSrc} title={ep.title} allow="accelerometer; encrypted-media; picture-in-picture" allowFullScreen loading="lazy" />
          </div>
        )}

        <AudioPlayerTTS scriptLines={ep.lines.map(l => ({ speaker: l.speaker, text: l.text }))} knownWords={ep.vocab} />

        <section className="card" style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <Languages size={18} color="var(--agen-primary)" />
            <strong style={{ flex: 1 }}>Bản dịch song ngữ</strong>
            <button type="button" className="btn btn-outline btn-sm" onClick={() => setShowVi(v => !v)} aria-expanded={showVi}>{showVi ? 'Ẩn' : 'Hiện'}</button>
          </div>
          {showVi ? (
            <ol className="media-bilingual">
              {ep.lines.map((l, i) => (
                <li key={i}><span className="media-speaker">{l.speaker}</span><div><div>{l.text}</div><div className="media-vi">{l.vi}</div></div></li>
              ))}
            </ol>
          ) : <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>Thử nghe hiểu trước, cần thì mới mở bản dịch.</p>}
          {ep.vocab.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
              {ep.vocab.map(v => <span key={v.word} className="chat-chip" style={{ cursor: 'default' }}><b>{v.word}</b>&nbsp;· {v.definition}</span>)}
            </div>
          )}
        </section>

        <section className="card exam-q" style={{ marginTop: 16 }}>
          <div className="section-head"><h3>Câu hỏi nghe hiểu</h3></div>
          <div style={{ display: 'grid', gap: 18 }}>
            {ep.questions.map((q, qi) => {
              const d = detail(q.id);
              return (
                <div key={q.id}>
                  <div style={{ fontWeight: 600, marginBottom: 8 }}>{qi + 1}. {q.prompt}</div>
                  <div className="choice-grid">
                    {q.options.map((opt, oi) => {
                      const picked = answers[q.id] === oi;
                      const state = result
                        ? (d && opt === d.expected ? 'correct' : picked ? 'wrong' : 'muted')
                        : picked ? 'selected' : undefined;
                      return (
                        <button key={oi} type="button" className="choice" data-state={state} disabled={!!result} onClick={() => setAnswers(a => ({ ...a, [q.id]: oi }))}>
                          <span className="choice-key">{String.fromCharCode(65 + oi)}</span><span>{opt}</span>
                        </button>
                      );
                    })}
                  </div>
                  {d && <div className="exam-review" data-ok={d.correct} style={{ marginTop: 8, fontSize: '0.85rem', display: 'flex', gap: 8 }}><span className="exam-review-mark">{d.correct ? <Check size={13} /> : <X size={13} />}</span><span>{d.explanation_vi}</span></div>}
                </div>
              );
            })}
          </div>
          {error && <div className="alert-error" style={{ marginTop: 12 }}><CircleAlert size={16} /> {error}</div>}
          {result ? (
            <div className="media-result">
              <div className="exam-result-band">{result.correct}/{result.total}</div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', justifyContent: 'center' }}>
                {result.xp_earned > 0 && <span className="xp-badge"><Sparkles size={13} /> +{result.xp_earned} XP</span>}
                {result.gems_earned > 0 && <span className="xp-badge"><Gem size={13} /> +{result.gems_earned}</span>}
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Tốt nhất: {Math.round(result.best_score)}%</span>
              </div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center' }}>
                <button type="button" className="btn btn-outline" onClick={retry}><RotateCcw size={15} /> Làm lại</button>
                <Link href="/listen" className="btn btn-primary">Tập khác</Link>
              </div>
            </div>
          ) : (
            <button type="button" className="btn btn-primary btn-full" style={{ marginTop: 16 }} disabled={busy || Object.keys(answers).length < ep.questions.length} onClick={submit}>
              {busy ? <LoaderCircle className="animate-spin" size={16} /> : null} Nộp bài ({Object.keys(answers).length}/{ep.questions.length})
            </button>
          )}
        </section>
      </div>
    </main>
  );
}
