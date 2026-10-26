'use client';

/** G7 · Chi tiết nhóm: mã tham gia, bảng thành viên, bài tập tuần. */
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Check, CircleAlert, Copy, FileText, Flame, LoaderCircle, Plus, Star, Trash2, X } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import {
  SKILL_LABELS, createAssignment, deleteAssignment, getGroupDetail, removeGroupMember,
  type AssignmentSkill, type GroupDetail,
} from '@/lib/groupsService';
import Avatar from '@/components/ui/Avatar';
import ClubSchedulesCard from '@/components/teacher/ClubSchedulesCard';
import { track } from '@/lib/analytics';

const SKILLS: AssignmentSkill[] = ['vocabulary', 'grammar', 'reading', 'listening'];

export default function TeacherGroupPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [detail, setDetail] = useState<GroupDetail | null>(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ title: '', skill: 'vocabulary' as AssignmentSkill, topic: '', due_on: '', note: '' });

  const load = () => getGroupDetail(groupId).then(setDetail).catch(() => setError('Không tải được nhóm.'));
  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, isAuthenticated, groupId]);

  const addAssignment = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError('');
    try {
      await createAssignment(groupId, { title: form.title, skill: form.skill, topic: form.topic, due_on: form.due_on || null, note: form.note || undefined });
      track('assignment_created', { skill: form.skill });
      setForm({ title: '', skill: 'vocabulary', topic: '', due_on: '', note: '' });
      await load();
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Không giao được bài.');
    } finally { setBusy(false); }
  };

  const copy = () => {
    if (!detail) return;
    navigator.clipboard?.writeText(detail.group.code);
    setCopied(true); setTimeout(() => setCopied(false), 1500);
  };

  if (!detail) return <main className="teacher-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <div style={{ display: 'flex', gap: 10, alignItems: 'center', color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={20} /> Đang tải…</div>}</main>;

  const { group, members, assignments } = detail;
  return (
    <main className="teacher-page">
      <div className="teacher-column">
        <Link href="/teacher" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem', marginBottom: 12 }}><ArrowLeft size={16} /> Nhóm của tôi</Link>
        <section className="card" style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap', marginBottom: 'var(--spacing-lg)' }}>
          <div style={{ flex: 1, minWidth: 220 }}>
            <div className="eyebrow">{group.kind === 'company' ? 'Doanh nghiệp' : 'Lớp học'}</div>
            <h1 style={{ fontSize: 'clamp(1.5rem, 4vw, 2rem)', margin: '2px 0 4px' }}>{group.name}</h1>
            <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>{members.length} thành viên{detail.covered_seats ? ` · ${Math.min(members.length, detail.covered_seats)} ghế Premium` : ''}. Học viên vào mục <b>Lớp học</b> trong ứng dụng và nhập mã này.</div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
            <Link href={`/teacher/${group.id}/report`} className="btn btn-outline btn-sm"><FileText size={14} /> Báo cáo · PDF / CSV</Link>
            <button type="button" className="code-chip" onClick={copy} aria-label="Sao chép mã nhóm">{group.code} {copied ? <Check size={15} /> : <Copy size={15} />}</button>
          </div>
        </section>

        {error && <div className="alert-error" style={{ marginBottom: 12 }}><CircleAlert size={16} /> {error}</div>}

        <h3 style={{ margin: '0 0 10px' }}>Giao bài tuần</h3>
        <form onSubmit={addAssignment} className="card" style={{ display: 'grid', gap: 10, marginBottom: 'var(--spacing-lg)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 8 }}>
            <input className="form-input" placeholder="Tiêu đề (Tuần 1: Food)" value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} required maxLength={140} />
            <select className="form-input" value={form.skill} onChange={e => setForm(f => ({ ...f, skill: e.target.value as AssignmentSkill }))} aria-label="Kỹ năng">
              {SKILLS.map(s => <option key={s} value={s}>{SKILL_LABELS[s]}</option>)}
            </select>
            <input className="form-input" placeholder="Chủ đề (food and drinks)" value={form.topic} onChange={e => setForm(f => ({ ...f, topic: e.target.value }))} required maxLength={100} />
            <input className="form-input" type="date" value={form.due_on} onChange={e => setForm(f => ({ ...f, due_on: e.target.value }))} aria-label="Hạn nộp" />
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input className="form-input" placeholder="Ghi chú cho học viên (tuỳ chọn)" value={form.note} onChange={e => setForm(f => ({ ...f, note: e.target.value }))} maxLength={500} style={{ flex: '1 1 240px' }} />
            <button type="submit" className="btn btn-primary" disabled={busy || !form.title.trim() || !form.topic.trim()}>{busy ? <LoaderCircle className="animate-spin" size={16} /> : <Plus size={16} />} Giao bài</button>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>AI tạo bài học theo kỹ năng và chủ đề này ở đúng trình độ của từng học viên; học xong là bài tập được tính hoàn thành.</div>
        </form>

        {assignments.length > 0 && (
          <div className="card" style={{ padding: 0, marginBottom: 'var(--spacing-lg)', overflow: 'hidden' }}>
            {assignments.map((a, i) => (
              <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', borderTop: i ? '1px solid var(--border-subtle)' : 'none' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600 }}>{a.title} <span className="skill-badge" style={{ background: 'var(--bg-tint)', color: 'var(--agen-primary)' }}>{SKILL_LABELS[a.skill]}</span></div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{a.topic}{a.due_on ? ` · hạn ${new Date(a.due_on).toLocaleDateString('vi-VN')}` : ''}</div>
                </div>
                <div style={{ textAlign: 'right', fontSize: '0.85rem' }}>
                  <strong>{a.done_count}/{a.member_count}</strong><div style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>đã xong</div>
                </div>
                <div className="progress-bar" style={{ width: 90 }}><div className="progress-fill" style={{ width: `${a.member_count ? (a.done_count / a.member_count) * 100 : 0}%`, background: 'var(--agen-success)' }} /></div>
                <button type="button" className="icon-btn" aria-label="Xoá bài tập" onClick={async () => { if (confirm('Xoá bài tập này?')) { await deleteAssignment(groupId, a.id); await load(); } }}><Trash2 size={15} /></button>
              </div>
            ))}
          </div>
        )}

        <ClubSchedulesCard groupId={groupId} />

        <h3 style={{ margin: '0 0 10px' }}>Thành viên ({members.length})</h3>
        {members.length === 0 ? (
          <div className="card" style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 28 }}>Chưa có ai. Gửi mã <b>{group.code}</b> cho học viên.</div>
        ) : (
          <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
            <table className="teacher-table">
              <thead><tr><th>Học viên</th><th>Trình độ</th><th>XP tuần</th><th>Chuỗi</th><th>Bài tập</th><th>Hôm nay</th><th>Gói</th><th /></tr></thead>
              <tbody>
                {members.map(m => (
                  <tr key={m.learner_id}>
                    <td><Link href={`/teacher/${groupId}/member/${m.learner_id}`} className="teacher-member-link" title="Xem bài làm & nhận xét"><Avatar avatar={m.avatar} name={m.display_name} size={28} /> {m.display_name}</Link></td>
                    <td><span className="level-badge">{m.level}</span></td>
                    <td><span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontWeight: 600 }}><Star size={13} color="var(--agen-accent)" fill="var(--agen-accent)" /> {m.weekly_xp}</span></td>
                    <td><span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><Flame size={13} color="var(--agen-secondary)" /> {m.streak}</span></td>
                    <td>{m.assignments_done}/{assignments.length}</td>
                    <td>{m.active_today ? <Check size={16} color="var(--agen-success)" /> : <X size={16} color="var(--text-muted)" />}</td>
                    <td>{m.premium_source ? <span className="plan-chip is-premium">Premium</span> : <span className="plan-chip">Miễn phí</span>}</td>
                    <td><button type="button" className="icon-btn" aria-label="Xoá khỏi nhóm" onClick={async () => { if (confirm(`Xoá ${m.display_name} khỏi nhóm?`)) { await removeGroupMember(groupId, m.learner_id); await load(); } }}><X size={15} /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
