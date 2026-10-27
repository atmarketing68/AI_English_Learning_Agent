'use client';
import PageBanner from '@/components/ui/PageBanner';

/** G7 · Lớp học của tôi: tham gia bằng mã, bài tập được giao. */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, CalendarClock, Check, CircleAlert, ClipboardCheck, LoaderCircle, LogOut, MessageSquareText, MessagesSquare, School } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { SKILL_LABELS, classTestHref, testScoreLabel, getMyFeedback, getMyGroups, joinGroup, leaveGroup, markFeedbackRead, type LearnerFeedback, type LearnerGroup } from '@/lib/groupsService';
import { PageSkeleton } from '@/components/Skeleton';
import { formatSlot, getClubLobby, joinRoom, type RoomCard } from '@/lib/clubService';
import Mascot from '@/components/ui/Mascot';
import { track } from '@/lib/analytics';

export default function ClassesPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [groups, setGroups] = useState<LearnerGroup[] | null>(null);
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [feedback, setFeedback] = useState<LearnerFeedback[]>([]);
  const [classClub, setClassClub] = useState<RoomCard[]>([]);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getMyGroups().then(r => setGroups(r.groups)).catch(() => setError('Không tải được lớp học.'));
    // G10 · teachers' comments; opening this page marks them read
    // G12 · weekly speaking-club sessions of my classes
    getClubLobby().then(l => setClassClub([...l.open_rooms, ...(l.upcoming_rooms ?? []), ...l.my_rooms].filter((r, i, a) => r.group_name && a.findIndex(x => x.id === r.id) === i)))
      .catch(() => undefined);
    getMyFeedback().then(f => { setFeedback(f); if (f.some(x => !x.read_at)) void markFeedbackRead().catch(() => undefined); }).catch(() => undefined);
  }, [hydrated, isAuthenticated, router]);

  const join = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError('');
    try {
      setGroups((await joinGroup(code)).groups);
      setCode('');
      track('group_joined');
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không tham gia được.');
    } finally { setBusy(false); }
  };

  if (!groups) return <main className="friends-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <PageSkeleton cards={2} />}</main>;
  const pending = groups.flatMap(g => g.assignments.filter(a => !a.done).map(a => ({ g, a })));
  // G13 · class tests open now and not taken yet
  const openTests = groups.flatMap(g => (g.tests ?? []).filter(t => t.status === 'open' && !t.mine?.done && t.available));

  return (
    <main className="friends-page">
      <div className="friends-column">
        <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Trang chủ</Link>
        <PageBanner image="banner-classes" priority />
        <section className="card friends-hero">
          <span className="icon-tile" style={{ width: 56, height: 56, borderRadius: 18, background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}><School size={28} strokeWidth={1.7} /></span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="eyebrow">Lớp học & nhóm</div>
            <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>{openTests.length ? `${openTests.length} bài kiểm tra đang mở` : pending.length ? `${pending.length} bài tập đang chờ` : 'Lớp học của tôi'}</h1>
            <p style={{ margin: 0, fontSize: '0.9rem' }}>Nhập mã từ giáo viên hoặc công ty để tham gia. Bài tập được giao sẽ hiện ở đây và trên trang chủ.</p>
          </div>
        </section>
        <Mascot size={64} mood={pending.length ? 'think' : 'happy'} say={pending.length ? 'Có bài cô giao nè, làm ngay cho nhẹ đầu!' : 'Có mã lớp chưa? Nhập vào để cùng học với các bạn.'} className="league-mascot" />

        <form onSubmit={join} className="card" style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <input className="form-input" placeholder="Mã lớp / nhóm (LOP-XXXX, CTY-XXXX)" value={code} onChange={e => setCode(e.target.value.toUpperCase())} style={{ flex: '1 1 200px', textTransform: 'uppercase', letterSpacing: 1 }} maxLength={20} aria-label="Mã nhóm" />
          <button type="submit" className="btn btn-primary" disabled={busy || !code.trim()}>{busy ? <LoaderCircle className="animate-spin" size={16} /> : 'Tham gia'}</button>
          {error && <div className="alert-error" style={{ flexBasis: '100%' }}><CircleAlert size={16} /> {error}</div>}
        </form>

        {classClub.length > 0 && (
          <section className="card" style={{ marginTop: 16 }}>
            <div className="section-head"><h3><MessagesSquare size={16} /> Câu lạc bộ nói của lớp</h3></div>
            {classClub.map(r => (
              <div key={r.id} className="club-room-row">
                <span className="club-topic-emoji" aria-hidden>{r.topic.emoji}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600 }}>{r.topic.title_vi}</div>
                  <div className="club-when"><CalendarClock size={12} /> {r.scheduled_at ? formatSlot(r.scheduled_at) : 'Đang mở'} · Lớp {r.group_name} · {r.members} người đã đăng ký</div>
                </div>
                <button type="button" className={`btn btn-sm ${r.registered ? 'btn-outline' : 'btn-primary'}`} onClick={async () => {
                  try { const st = await joinRoom(r.code); router.push(`/club/${st.id}`); } catch { setError('Không vào được buổi nói này.'); }
                }}>{r.registered ? 'Vào phòng' : 'Đăng ký'} <ArrowRight size={14} /></button>
              </div>
            ))}
          </section>
        )}

        {feedback.length > 0 && (
          <section className="card" style={{ marginTop: 16 }}>
            <div className="section-head"><h3><MessageSquareText size={16} /> Nhận xét của giáo viên</h3></div>
            <div style={{ display: 'grid', gap: 8 }}>
              {feedback.slice(0, 10).map(f => (
                <div key={f.id} className="member-feedback" data-unread={!f.read_at}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {!f.read_at && <span className="plan-chip is-premium" style={{ marginRight: 6 }}>Mới</span>}
                    {f.teacher_name} · {f.group_name}{f.target_label ? ` · về “${f.target_label}”` : ''} · {new Date(f.created_at.endsWith('Z') ? f.created_at : `${f.created_at}Z`).toLocaleDateString('vi-VN')}
                  </div>
                  <div style={{ whiteSpace: 'pre-line', fontSize: '0.92rem' }}>{f.text}</div>
                </div>
              ))}
            </div>
          </section>
        )}

        {groups.length === 0 && <div className="card" style={{ marginTop: 16, textAlign: 'center', color: 'var(--text-muted)', padding: 28 }}>Bạn chưa ở trong lớp hoặc nhóm nào.</div>}
        {groups.map(({ group, owner_name, assignments, tests }) => (
          <section key={group.id} className="card" style={{ marginTop: 16, display: 'grid', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600 }}>{group.name}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{group.kind === 'company' ? 'Doanh nghiệp' : 'Lớp học'} · {owner_name} · {group.member_count} thành viên</div>
              </div>
              <button type="button" className="btn btn-ghost btn-sm" onClick={async () => { if (confirm(`Rời ${group.name}?`)) setGroups((await leaveGroup(group.id)).groups); }}><LogOut size={14} /> Rời nhóm</button>
            </div>
            {(tests ?? []).map(t => (
              <div key={t.id} className="class-test-learner" data-status={t.status}>
                <span className="icon-tile" style={{ flexShrink: 0, width: 40, height: 40, background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}><ClipboardCheck size={20} strokeWidth={1.8} /></span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600 }}>{t.title}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Bài kiểm tra lớp{t.minutes ? ` · ${t.minutes} phút` : ''} · {t.status === 'upcoming' ? `mở ngày ${new Date(`${t.opens_on}T00:00:00`).toLocaleDateString('vi-VN')}` : `hạn ${new Date(`${t.due_on}T00:00:00`).toLocaleDateString('vi-VN')}`}{t.note ? ` · ${t.note}` : ''}
                  </div>
                </div>
                {t.mine?.done
                  ? <span className="xp-badge"><Check size={13} /> {testScoreLabel(t.exam, t.mine)}</span>
                  : t.status === 'open'
                    ? <Link href={classTestHref(t)} className="btn btn-primary btn-sm" onClick={() => track('class_test_started', { kind: t.kind })}>Làm bài <ArrowRight size={14} /></Link>
                    : <span className="plan-chip">{t.status === 'upcoming' ? 'Sắp mở' : 'Đã đóng'}</span>}
              </div>
            ))}
            {assignments.length === 0 && !(tests ?? []).length && <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Chưa có bài tập nào được giao.</div>}
            {assignments.map(a => (
              <div key={a.id} className="assignment-row" data-done={a.done} data-overdue={a.overdue}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    {a.title} <span className="skill-badge" style={{ background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}>{SKILL_LABELS[a.skill]}</span>
                    {a.overdue && <span className="skill-badge" style={{ background: 'color-mix(in srgb, var(--agen-secondary) 12%, transparent)', color: 'var(--agen-secondary)' }}>Quá hạn</span>}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{a.topic}{a.due_on ? ` · hạn ${new Date(a.due_on).toLocaleDateString('vi-VN')}` : ''}{a.note ? ` · ${a.note}` : ''}</div>
                </div>
                {a.done
                  ? <span className="xp-badge"><Check size={13} /> Xong{a.score != null ? ` · ${a.score}%` : ''}</span>
                  : <Link href={`/learn?assignment=${a.id}`} className="btn btn-primary btn-sm" onClick={() => track('assignment_started', { skill: a.skill })}>{a.started ? 'Làm tiếp' : 'Làm bài'} <ArrowRight size={14} /></Link>}
              </div>
            ))}
          </section>
        ))}
      </div>
    </main>
  );
}
