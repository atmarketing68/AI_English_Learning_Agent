'use client';
import PageBanner from '@/components/ui/PageBanner';

/** G10 · Câu lạc bộ nói: phòng 2–4 người, AI dẫn chuyện và gọi từng người nói. */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, CalendarClock, CircleAlert, DoorOpen, Lock, LoaderCircle, MessagesSquare, Plus, Users } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { createRoom, formatSlot, getClubLobby, joinRoom, type ClubLobby, type RoomCard } from '@/lib/clubService';
import { PageSkeleton } from '@/components/Skeleton';
import Mascot from '@/components/ui/Mascot';
import { track } from '@/lib/analytics';

const errText = (err: unknown, fallback: string) => (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || fallback;

/** "2026-10-27T19:30" for <input type="datetime-local">, in the device's time zone. */
function localInputValue(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
}

function RoomRow({ r, action, onClick, busy }: { r: RoomCard; action: string; onClick: () => void; busy: boolean }) {
  return (
    <div className="club-room-row">
      <span className="club-topic-emoji" aria-hidden>{r.topic.emoji}</span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600 }}>{r.topic.title_vi}</div>
        <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{r.topic.level} · chủ phòng {r.host_name} · <Users size={12} /> {r.members}/4 · mã {r.code}</div>
        {r.scheduled_at && <div className="club-when"><CalendarClock size={12} /> {formatSlot(r.scheduled_at)}{r.group_name && <span className="club-group-badge" style={{ marginLeft: 6 }}>Lớp {r.group_name}</span>}</div>}
      </div>
      <button type="button" className={`btn btn-sm ${r.registered ? 'btn-outline' : 'btn-primary'}`} onClick={onClick} disabled={busy}>{r.registered ? 'Vào phòng' : action} <ArrowRight size={14} /></button>
    </div>
  );
}

export default function ClubLobbyPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [lobby, setLobby] = useState<ClubLobby | null>(null);
  const [code, setCode] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  // G11 · book a session for later ("" = start now); value of <input type="datetime-local"> in the device's time zone
  const [scheduleOn, setScheduleOn] = useState(false);
  const [when, setWhen] = useState('');
  const [minWhen, setMinWhen] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    const load = () => getClubLobby().then(setLobby).catch(() => setError('Không tải được câu lạc bộ.'));
    load();
    const t = setInterval(load, 8000);       // open rooms change while the page is open
    return () => clearInterval(t);
  }, [hydrated, isAuthenticated, router]);

  if (!lobby) return <main className="friends-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={3} />}</main>;

  const create = async (topicId: string) => {
    setBusy(topicId); setError('');
    try {
      if (scheduleOn && !when) { setError('Chọn ngày giờ hẹn trước khi chọn chủ đề.'); setBusy(''); return; }
      const scheduledAt = scheduleOn && when ? new Date(when).toISOString() : null;
      const room = await createRoom(topicId, isPublic, scheduledAt);
      track(scheduledAt ? 'club_room_scheduled' : 'club_room_created', { topic: topicId, public: isPublic });
      router.push(`/club/${room.id}`);
    } catch (err) { setError(errText(err, 'Chưa tạo được phòng.')); setBusy(''); }
  };
  const join = async (c: string) => {
    if (c.trim().length < 4) return;
    setBusy(c); setError('');
    try {
      const room = await joinRoom(c.trim());
      track('club_room_joined', { topic: room.topic.id });
      router.push(`/club/${room.id}`);
    } catch (err) { setError(errText(err, 'Không vào được phòng.')); setBusy(''); }
  };

  return (
    <main className="friends-page">
      <div className="friends-column" style={{ maxWidth: 820 }}>
        <PageBanner image="banner-club" priority />
        <section className="card friends-hero">
          <span className="icon-tile" style={{ width: 56, height: 56, borderRadius: 18, background: 'var(--bg-tint)', color: 'var(--skill-speaking, #D6336C)' }}><MessagesSquare size={28} strokeWidth={1.7} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow">Câu lạc bộ nói</div>
            <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>Nói tiếng Anh cùng bạn, AI dẫn chuyện</h1>
            <p style={{ margin: 0, fontSize: '0.9rem' }}>2–4 người một phòng. AI đặt câu hỏi, gọi lần lượt từng người và góp ý nhẹ nhàng sau mỗi lượt nói.</p>
          </div>
        </section>
        <Mascot size={64} mood="cheer" say="Rủ bạn cùng lớp vào bằng mã phòng nhé!" className="league-mascot" />
        {error && <div className="alert-error" style={{ marginTop: 12 }}><CircleAlert size={16} /> {error}</div>}

        {lobby.my_rooms.length > 0 && (
          <section className="card" style={{ marginTop: 16 }}>
            <div className="section-head"><h3>Phòng của bạn</h3></div>
            {lobby.my_rooms.map(r => <RoomRow key={r.id} r={r} action="Vào lại" busy={false} onClick={() => router.push(`/club/${r.id}`)} />)}
          </section>
        )}

        <section className="card" style={{ marginTop: 16 }}>
          <div className="section-head"><h3>Vào phòng bằng mã</h3></div>
          <form style={{ display: 'flex', gap: 8 }} onSubmit={e => { e.preventDefault(); void join(code); }}>
            <input className="form-input" value={code} onChange={e => setCode(e.target.value.toUpperCase())} placeholder="VD: K7PQ2M" maxLength={12} aria-label="Mã phòng" style={{ textTransform: 'uppercase', letterSpacing: '0.1em' }} />
            <button type="submit" className="btn btn-primary" disabled={code.trim().length < 4 || !!busy}><DoorOpen size={16} /> Vào</button>
          </form>
        </section>

        {!!lobby.upcoming_rooms?.length && (
          <section className="card" style={{ marginTop: 16 }}>
            <div className="section-head"><h3><CalendarClock size={16} /> Buổi nói sắp diễn ra</h3></div>
            <p style={{ margin: '0 0 6px', fontSize: '0.82rem', color: 'var(--text-muted)' }}>Đăng ký trước, bạn sẽ được nhắc khoảng 15 phút trước giờ bắt đầu.</p>
            {lobby.upcoming_rooms.map(r => <RoomRow key={r.id} r={r} action="Đăng ký" busy={busy === r.code} onClick={() => join(r.code)} />)}
          </section>
        )}

        <section className="card" style={{ marginTop: 16 }}>
          <div className="section-head"><h3>Phòng đang chờ người</h3></div>
          {lobby.open_rooms.length === 0
            ? <p style={{ margin: 0, fontSize: '0.88rem', color: 'var(--text-muted)' }}>Chưa có phòng nào đang mở. Tạo phòng mới bên dưới rồi gửi mã cho bạn bè.</p>
            : lobby.open_rooms.map(r => <RoomRow key={r.id} r={r} action="Tham gia" busy={busy === r.code} onClick={() => join(r.code)} />)}
        </section>

        <section style={{ marginTop: 20 }}>
          <div className="section-head" style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <h3 style={{ flex: '1 1 220px' }}>Tạo phòng mới · chọn chủ đề</h3>
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.85rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={!isPublic} onChange={e => setIsPublic(!e.target.checked)} /> <Lock size={13} /> Phòng riêng (chỉ vào bằng mã)
            </label>
          </div>
          <div className="club-schedule">
            <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: '0.88rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={scheduleOn} onChange={e => { setScheduleOn(e.target.checked); setMinWhen(localInputValue(new Date(Date.now() + 15 * 60_000))); }} /> <CalendarClock size={14} /> Hẹn giờ cho buổi nói (rủ bạn đăng ký trước)
            </label>
            {scheduleOn && (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                <input type="datetime-local" className="form-input" value={when} min={minWhen} onChange={e => setWhen(e.target.value)} aria-label="Ngày giờ hẹn" style={{ maxWidth: 260 }} />
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Từ 10 phút đến 14 ngày tới. Mọi người được nhắc trước ~15 phút.</span>
              </div>
            )}
          </div>
          <div className="club-topic-grid">
            {lobby.topics.map(t => (
              <button key={t.id} type="button" className="card club-topic" onClick={() => create(t.id)} disabled={!!busy}>
                <span className="club-topic-emoji" aria-hidden>{t.emoji}</span>
                <span style={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
                  <span style={{ display: 'block', fontWeight: 600 }}>{t.title_vi}</span>
                  <span style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-muted)' }}>{t.title} · {t.level}</span>
                </span>
                {busy === t.id ? <LoaderCircle className="animate-spin" size={16} /> : <Plus size={16} />}
              </button>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
