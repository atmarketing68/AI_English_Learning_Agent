'use client';

/** G8 · Hỏi Bo — chatbot ngữ pháp bằng tiếng Việt, có ví dụ nghe được. */
import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, CircleAlert, LoaderCircle, Lock, MessageCircleQuestion, Send, Sparkles, Trash2, Volume2 } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { askTutor, clearTutorHistory, getTutorHome, type TutorHome, type TutorMessage } from '@/lib/tutorService';
import { playText } from '@/lib/speechService';
import { PageSkeleton } from '@/components/Skeleton';
import Mascot from '@/components/ui/Mascot';
import { track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

function Bubble({ m, onFollowUp }: { m: TutorMessage; onFollowUp: (q: string) => void }) {
  if (m.role === 'user') return <div className="chat-row is-user"><div className="chat-bubble">{m.content}</div></div>;
  return (
    <div className="chat-row">
      <div className="chat-avatar" aria-hidden><Mascot size={36} always /></div>
      <div className="chat-bubble is-bo">
        {m.content.split('\n').map((line, i) => <p key={i} style={{ margin: i ? '6px 0 0' : 0 }}>{line}</p>)}
        {m.rule && <div className="chat-rule">{m.rule}</div>}
        {m.examples.length > 0 && (
          <ul className="chat-examples">
            {m.examples.map((ex, i) => (
              <li key={i}>
                <button type="button" className="icon-btn" aria-label="Nghe ví dụ" onClick={() => void playText(ex.en)}><Volume2 size={14} /></button>
                <span><b>{ex.en}</b>{ex.vi && <span style={{ color: 'var(--text-muted)' }}> — {ex.vi}</span>}</span>
              </li>
            ))}
          </ul>
        )}
        {m.common_mistake && <div className="chat-mistake">⚠️ Lỗi hay gặp: {m.common_mistake}</div>}
        {m.follow_ups.length > 0 && (
          <div className="chat-chips">
            {m.follow_ups.map(q => <button key={q} type="button" className="chat-chip" onClick={() => onFollowUp(q)}>{q}</button>)}
          </div>
        )}
      </div>
    </div>
  );
}

export default function TutorPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [home, setHome] = useState<TutorHome | null>(null);
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getTutorHome().then(h => { setHome(h); setMessages(h.messages); }).catch(() => setError('Không tải được Bo.'));
  }, [hydrated, isAuthenticated, router]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages.length, busy]);

  const ask = async (q: string) => {
    const text = q.trim();
    if (!text || busy) return;
    setBusy(true); setError(''); setQuestion('');
    try {
      const r = await askTutor(text);
      setMessages(m => [...m, r.question, r.answer]);
      setHome(h => (h ? { ...h, asked_today: r.asked_today, remaining_today: r.remaining_today } : h));
      track('tutor_asked', { fallback: r.answer.fallback });
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Bo chưa trả lời được, thử lại nhé.'));
    } finally { setBusy(false); }
  };

  const clear = async () => {
    if (!confirm('Xoá toàn bộ lịch sử hỏi đáp?')) return;
    await clearTutorHistory();
    setMessages([]);
  };

  if (!home) return <main className="friends-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={2} />}</main>;
  const locked = home.remaining_today === 0;

  return (
    <main className="friends-page tutor-page">
      <div className="friends-column" style={{ maxWidth: 720 }}>
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Trang chủ</Link>
        <section className="card friends-hero">
          <span className="icon-tile" style={{ width: 56, height: 56, borderRadius: 18, background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}><MessageCircleQuestion size={28} strokeWidth={1.7} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow">Hỏi Bo</div>
            <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>Thắc mắc ngữ pháp? Hỏi Bo</h1>
            <p style={{ margin: 0, fontSize: '0.9rem' }}>Giải thích bằng tiếng Việt, có ví dụ nghe được và lỗi người Việt hay mắc. {home.remaining_today == null ? 'Premium: hỏi không giới hạn.' : `Hôm nay còn ${home.remaining_today}/${home.free_daily_limit} câu miễn phí.`}</p>
          </div>
          {messages.length > 0 && <button type="button" className="icon-btn" aria-label="Xoá lịch sử" onClick={clear}><Trash2 size={16} /></button>}
        </section>

        <div className="chat-log">
          {messages.length === 0 && (
            <div className="chat-row">
              <div className="chat-avatar" aria-hidden><Mascot size={36} always mood="happy" /></div>
              <div className="chat-bubble is-bo">Chào bạn! Mình là Bo. Bạn đang vướng chỗ nào trong tiếng Anh? Hỏi mình bằng tiếng Việt cũng được nhé.</div>
            </div>
          )}
          {messages.map(m => <Bubble key={m.id} m={m} onFollowUp={ask} />)}
          {busy && <div className="chat-row"><div className="chat-avatar" aria-hidden><Mascot size={36} always mood="think" /></div><div className="chat-bubble is-bo chat-typing"><span /><span /><span /></div></div>}
          <div ref={endRef} />
        </div>

        {messages.length === 0 && (
          <div className="chat-chips" style={{ margin: '8px 0 12px' }}>
            {home.suggested.map(q => <button key={q} type="button" className="chat-chip" onClick={() => ask(q)}><Sparkles size={12} /> {q}</button>)}
          </div>
        )}
        {error && <div className="alert-error" style={{ marginBottom: 10 }}><CircleAlert size={16} /> {error}</div>}

        {locked ? (
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <Lock size={18} color="var(--agen-accent)" />
            <span style={{ flex: 1, fontSize: '0.88rem' }}>Bạn đã hỏi hết {home.free_daily_limit} câu miễn phí hôm nay. Premium hỏi Bo không giới hạn.</span>
            <Link href="/upgrade" className="btn btn-primary btn-sm">Nâng cấp</Link>
          </div>
        ) : (
          <form className="chat-input" onSubmit={e => { e.preventDefault(); void ask(question); }}>
            <input className="form-input" value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ví dụ: Khi nào dùng 'since', khi nào dùng 'for'?" maxLength={600} aria-label="Câu hỏi" disabled={busy} />
            <button type="submit" className="btn btn-primary" disabled={busy || question.trim().length < 2} aria-label="Gửi">{busy ? <LoaderCircle className="animate-spin" size={16} /> : <Send size={16} />}</button>
          </form>
        )}
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 10 }}>Bo trả lời bằng AI nên đôi khi có thể sai; với quy tắc quan trọng hãy đối chiếu thêm trong bài học.</p>
      </div>
    </main>
  );
}
