'use client';

/** G10 · Một phòng câu lạc bộ nói: AI gọi tên từng người, người đến lượt bấm micro để nói. */
import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Bot, CircleAlert, Copy, Crown, LoaderCircle, LogOut, Play, Send, SkipForward, Volume2 } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { getRoom, leaveRoom, skipTurn, speakInRoom, startRoom, type ClubMessage, type RoomState } from '@/lib/clubService';
import { playText, stopSpeech } from '@/lib/speechService';
import { useSpeechRecorder } from '@/lib/useSpeechRecorder';
import MicButton from '@/components/speaking/MicButton';
import Avatar from '@/components/ui/Avatar';
import { PageSkeleton } from '@/components/Skeleton';
import { track } from '@/lib/analytics';

const POLL_MS = 2500;
const errText = (err: unknown, fallback: string) => (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || fallback;

function mergeMessages(old: ClubMessage[], incoming: ClubMessage[]): ClubMessage[] {
  if (!incoming.length) return old;
  const bySeq = new Map(old.map(m => [m.seq, m]));
  incoming.forEach(m => bySeq.set(m.seq, m));
  return Array.from(bySeq.values()).sort((a, b) => a.seq - b.seq);
}

export default function ClubRoomPage() {
  const { roomId } = useParams<{ roomId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [room, setRoom] = useState<RoomState | null>(null);
  const [messages, setMessages] = useState<ClubMessage[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [typed, setTyped] = useState('');
  const [autoRead, setAutoRead] = useState(true);
  const lastSeq = useRef(0);
  const spoken = useRef(0);
  const endRef = useRef<HTMLDivElement>(null);

  const apply = useCallback((s: RoomState, full: boolean) => {
    setRoom(s);
    setMessages(m => (full ? s.messages : mergeMessages(m, s.messages)));
    lastSeq.current = Math.max(lastSeq.current, s.last_seq);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    let stop = false;
    getRoom(roomId).then(s => { apply(s, true); spoken.current = s.last_seq; }).catch(err => setError(errText(err, 'Không vào được phòng.')));
    const t = setInterval(() => {
      if (stop) return;
      getRoom(roomId, lastSeq.current).then(s => { if (!stop) apply(s, false); }).catch(() => { /* keep polling */ });
    }, POLL_MS);
    return () => { stop = true; clearInterval(t); stopSpeech(); };
  }, [hydrated, isAuthenticated, router, roomId, apply]);

  // Read new host lines aloud (only ones that arrived after the page opened).
  useEffect(() => {
    const fresh = messages.filter(m => m.seq > spoken.current && m.role === 'ai');
    if (messages.length) spoken.current = Math.max(spoken.current, messages[messages.length - 1].seq);
    if (autoRead && fresh.length) void playText(fresh[fresh.length - 1].text);
  }, [messages, autoRead]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages.length]);

  const act = async (fn: () => Promise<RoomState>) => {
    setBusy(true); setError('');
    try { apply(await fn(), true); } catch (err) { setError(errText(err, 'Có lỗi, thử lại nhé.')); } finally { setBusy(false); }
  };
  const send = async (text: string, seconds?: number) => {
    const t = text.trim();
    if (!t || busy) return;
    setTyped('');
    await act(() => speakInRoom(roomId, t, seconds));
    track('club_turn_spoken', { words: t.split(/\s+/).length });
  };

  const recorder = useSpeechRecorder({ onFinish: (t, d) => { void send(t, d); } });

  if (!room) return <main className="friends-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error} <Link href="/club">Về sảnh</Link></div> : <PageSkeleton cards={2} />}</main>;

  const names = new Map(room.members.map(m => [m.learner_id, m.name]));
  const speakerName = room.current_speaker_id ? names.get(room.current_speaker_id) : null;
  const progress = room.total_turns ? Math.round((room.turns_taken / room.total_turns) * 100) : 0;
  const leave = async () => {
    if (room.status === 'active' && !confirm('Rời phòng giữa chừng?')) return;
    try { await leaveRoom(roomId); } finally { router.push('/club'); }
  };

  return (
    <main className="friends-page">
      <div className="friends-column club-room" style={{ maxWidth: 760 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <Link href="/club" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', flex: 1 }}><ArrowLeft size={16} /> Sảnh</Link>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.82rem', cursor: 'pointer' }}>
            <input type="checkbox" checked={autoRead} onChange={e => setAutoRead(e.target.checked)} /> <Volume2 size={14} /> Đọc to lời AI
          </label>
          <button type="button" className="btn btn-outline btn-sm" onClick={leave}><LogOut size={14} /> Rời phòng</button>
        </div>

        <section className="card club-head">
          <span className="club-topic-emoji" aria-hidden>{room.topic.emoji}</span>
          <div className="club-head-title">
            <div className="eyebrow">Câu lạc bộ nói · {room.topic.level}</div>
            <h1 style={{ fontSize: 'clamp(1.25rem, 3.5vw, 1.6rem)', margin: '2px 0' }}>{room.topic.title_vi}</h1>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{room.topic.title}</div>
          </div>
          <button type="button" className="club-code" onClick={() => { void navigator.clipboard?.writeText(room.code); }} title="Chép mã phòng">
            <span>Mã phòng</span><strong>{room.code}</strong><Copy size={13} />
          </button>
        </section>

        <div className="club-members">
          {room.members.map(m => (
            <div key={m.learner_id} className="club-member" data-speaking={m.learner_id === room.current_speaker_id}>
              <Avatar avatar={m.avatar} name={m.name} size={40} />
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: 4 }}>{m.name}{m.is_me && ' (bạn)'}{m.is_host && <Crown size={12} color="var(--agen-accent)" aria-label="Chủ phòng" />}</div>
                <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>{m.turns} lượt · {m.words} từ</div>
              </div>
            </div>
          ))}
        </div>
        {room.status === 'active' && <div className="club-progress" aria-label={`Đã nói ${room.turns_taken}/${room.total_turns} lượt`}><span style={{ width: `${progress}%` }} /></div>}

        <div className="chat-log club-log">
          {messages.map(m => {
            if (m.role === 'system') return <div key={m.seq} className="club-system">{m.text}</div>;
            if (m.role === 'ai') return (
              <div key={m.seq} className="chat-row">
                <div className="chat-avatar club-ai" aria-hidden><Bot size={18} /></div>
                <div className="chat-bubble is-bo">
                  {m.text}
                  <button type="button" className="icon-btn" aria-label="Nghe lại" style={{ marginLeft: 6, verticalAlign: 'middle' }} onClick={() => void playText(m.text)}><Volume2 size={13} /></button>
                </div>
              </div>
            );
            const mine = room.members.find(x => x.learner_id === m.learner_id)?.is_me;
            return (
              <div key={m.seq} className={`chat-row${mine ? ' is-user' : ''}`}>
                <div className="chat-bubble">
                  {!mine && <div style={{ fontSize: '0.75rem', fontWeight: 600, marginBottom: 2 }}>{m.name ?? names.get(m.learner_id ?? '')}</div>}
                  {m.text}
                  {(m.feedback_vi || m.corrected) && (
                    <div className="club-tip">
                      {m.corrected && m.corrected !== m.text && <div>✍️ <b>{m.corrected}</b></div>}
                      {m.feedback_vi && <div>{m.feedback_vi}</div>}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {busy && <div className="chat-row"><div className="chat-avatar club-ai" aria-hidden><Bot size={18} /></div><div className="chat-bubble is-bo chat-typing"><span /><span /><span /></div></div>}
          <div ref={endRef} />
        </div>

        {error && <div className="alert-error" style={{ margin: '10px 0' }}><CircleAlert size={16} /> {error}</div>}

        <section className="card club-dock">
          {room.status === 'waiting' && (room.is_host ? (
            <>
              <p style={{ margin: 0, flex: 1, fontSize: '0.88rem' }}>Gửi mã <b>{room.code}</b> cho bạn bè. Bắt đầu khi đủ người (có thể tự luyện một mình).</p>
              <button type="button" className="btn btn-primary" disabled={busy} onClick={() => act(() => startRoom(roomId))}><Play size={15} /> Bắt đầu ({room.members.length} người)</button>
            </>
          ) : <p style={{ margin: 0, fontSize: '0.88rem' }}><LoaderCircle className="animate-spin" size={14} /> Chờ chủ phòng bắt đầu…</p>)}

          {room.status === 'active' && (room.is_my_turn ? (
            <div style={{ width: '100%', display: 'grid', gap: 10, justifyItems: 'center' }}>
              <div style={{ fontWeight: 600 }}>Đến lượt bạn! Trả lời câu hỏi của AI.</div>
              {recorder.supported && (
                <>
                  <MicButton listening={recorder.listening} size={72} disabled={busy} onClick={() => { if (recorder.listening) recorder.stop(); else { stopSpeech(); recorder.start(); } }} />
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', minHeight: 20 }}>{recorder.listening ? (recorder.transcript || 'Đang nghe… nói xong chạm để gửi') : 'Chạm micro để nói, chạm lại để gửi'}</div>
                  {recorder.error && <div className="alert-error">{recorder.error}</div>}
                </>
              )}
              <form className="chat-input" style={{ width: '100%' }} onSubmit={e => { e.preventDefault(); void send(typed); }}>
                <input className="form-input" value={typed} onChange={e => setTyped(e.target.value)} placeholder={recorder.supported ? 'Hoặc gõ câu trả lời…' : 'Gõ câu trả lời bằng tiếng Anh…'} maxLength={600} aria-label="Câu trả lời" disabled={busy} />
                <button type="submit" className="btn btn-primary" disabled={busy || !typed.trim()} aria-label="Gửi"><Send size={16} /></button>
              </form>
              <button type="button" className="btn btn-ghost btn-sm" disabled={busy} onClick={() => act(() => skipTurn(roomId))}><SkipForward size={14} /> Bỏ lượt</button>
            </div>
          ) : (
            <>
              <p style={{ margin: 0, flex: 1, fontSize: '0.88rem' }}>Đang chờ <b>{speakerName ?? '…'}</b> nói. Lắng nghe và chuẩn bị ý của bạn nhé!</p>
              {room.is_host && <button type="button" className="btn btn-outline btn-sm" disabled={busy} onClick={() => act(() => skipTurn(roomId))}><SkipForward size={14} /> Bỏ qua lượt này</button>}
            </>
          ))}

          {room.status === 'finished' && (
            <div style={{ width: '100%', textAlign: 'center', display: 'grid', gap: 10 }}>
              <div style={{ fontWeight: 600 }}>Buổi nói chuyện đã kết thúc 🎉</div>
              <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>Bạn đã nói {room.members.find(m => m.is_me)?.turns ?? 0} lượt, {room.members.find(m => m.is_me)?.words ?? 0} từ. Đọc lại góp ý ở trên để lần sau nói hay hơn.</div>
              <div><Link href="/club" className="btn btn-primary">Phòng mới</Link></div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
