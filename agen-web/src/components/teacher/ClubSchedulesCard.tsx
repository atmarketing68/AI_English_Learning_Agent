'use client';

/** G12 · Giáo viên đặt lịch câu lạc bộ nói hằng tuần cho lớp; phòng của buổi kế tiếp tự mở và cả lớp được báo. */
import { useCallback, useEffect, useState } from 'react';
import { CalendarClock, CircleAlert, LoaderCircle, MessagesSquare, Plus, Trash2, Users } from 'lucide-react';
import { addClubSchedule, deleteClubSchedule, getClubSchedules, type ClubSchedules } from '@/lib/groupsService';
import { formatSlot } from '@/lib/clubService';
import { track } from '@/lib/analytics';

export default function ClubSchedulesCard({ groupId }: { groupId: string }) {
  const [data, setData] = useState<ClubSchedules | null>(null);
  const [form, setForm] = useState({ weekday: 2, time: '19:30', topic: '' });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = useCallback(() => getClubSchedules(groupId).then(setData).catch(() => setError('Không tải được lịch câu lạc bộ nói.')), [groupId]);
  useEffect(() => { void load(); }, [load]);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError('');
    try {
      await addClubSchedule(groupId, { weekday: form.weekday, time: form.time, topic_id: form.topic || null });
      track('club_schedule_created', { weekday: form.weekday });
      await load();
    } catch (err) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không thêm được lịch.');
    } finally { setBusy(false); }
  };
  const remove = async (id: string, label: string) => {
    if (!confirm(`Huỷ lịch ${label}? Buổi sắp tới chưa bắt đầu cũng sẽ bị huỷ.`)) return;
    await deleteClubSchedule(groupId, id);
    await load();
  };

  return (
    <section className="card" style={{ marginBottom: 'var(--spacing-lg)' }}>
      <div className="section-head"><h3><MessagesSquare size={16} /> Câu lạc bộ nói hằng tuần</h3></div>
      <p style={{ margin: '0 0 12px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
        Chọn giờ cố định mỗi tuần (giờ Việt Nam). Phòng của buổi kế tiếp tự mở, cả lớp nhận thông báo để đăng ký và được nhắc trước 15 phút; AI dẫn chuyện như câu lạc bộ thường.
      </p>
      {!data ? <div style={{ color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={16} /></div> : (
        <>
          {data.schedules.length === 0 && <p style={{ margin: '0 0 10px', fontSize: '0.88rem' }}>Chưa có lịch nào.</p>}
          {data.schedules.map(s => (
            <div key={s.id} className="club-room-row">
              <span className="club-topic-emoji" aria-hidden><CalendarClock size={18} /></span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600 }}>{s.label} · {s.topic_title}</div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  {s.next ? <>Buổi tới {formatSlot(s.next.scheduled_at)} · {s.next.topic_title} · <Users size={12} /> {s.next.registered} đã đăng ký · mã {s.next.code}</> : 'Đang chuẩn bị buổi tới…'}
                </div>
              </div>
              <button type="button" className="icon-btn" aria-label="Huỷ lịch" onClick={() => remove(s.id, s.label)}><Trash2 size={15} /></button>
            </div>
          ))}
          <form onSubmit={add} className="club-schedule-form">
            <select className="form-input" value={form.weekday} onChange={e => setForm(f => ({ ...f, weekday: Number(e.target.value) }))} aria-label="Thứ">
              {data.weekdays.map((d, i) => <option key={d} value={i}>{d}</option>)}
            </select>
            <input className="form-input" type="time" value={form.time} onChange={e => setForm(f => ({ ...f, time: e.target.value }))} required aria-label="Giờ" />
            <select className="form-input" value={form.topic} onChange={e => setForm(f => ({ ...f, topic: e.target.value }))} aria-label="Chủ đề">
              <option value="">Luân phiên các chủ đề</option>
              {data.topics.map(t => <option key={t.id} value={t.id}>{t.emoji} {t.title_vi} · {t.level}</option>)}
            </select>
            <button type="submit" className="btn btn-primary btn-sm" disabled={busy}>{busy ? <LoaderCircle className="animate-spin" size={14} /> : <Plus size={14} />} Thêm lịch</button>
          </form>
        </>
      )}
      {error && <div className="alert-error" style={{ marginTop: 10 }}><CircleAlert size={16} /> {error}</div>}
    </section>
  );
}
