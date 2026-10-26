'use client';

/** G7 · Bảng giáo viên / doanh nghiệp: nhóm của tôi, tạo nhóm, gói theo ghế. */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Briefcase, ChevronRight, CircleAlert, Crown, LoaderCircle, Plus, School, Users } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { createGroup, getOwnerHome, type GroupKind, type OwnerHome } from '@/lib/groupsService';
import { track } from '@/lib/analytics';
import { apiErrorMessage } from '@/lib/apiError';

export default function TeacherPage() {
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated, userRole, logout } = useAuthStore();
  const [home, setHome] = useState<OwnerHome | null>(null);
  const [name, setName] = useState('');
  const [kind, setKind] = useState<GroupKind>('class');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = () => getOwnerHome().then(setHome).catch(() => setError('Không tải được danh sách nhóm.'));
  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    if (userRole && userRole !== 'teacher') { router.push(userRole === 'parent' ? '/parent' : '/dashboard'); return; }
    load();
  }, [hydrated, isAuthenticated, userRole, router]);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError('');
    try {
      const g = await createGroup(name, kind);
      track('group_created', { kind });
      setName('');
      await load();
      router.push(`/teacher/${g.id}`);
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Không tạo được nhóm.'));
    } finally { setBusy(false); }
  };

  if (!home) return <main className="teacher-page">{error ? <div className="alert-error"><CircleAlert size={16} /> {error}</div> : <div style={{ display: 'flex', gap: 10, alignItems: 'center', color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={20} /> Đang tải…</div>}</main>;

  return (
    <main className="teacher-page">
      <div className="teacher-column">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 'var(--spacing-xl)' }}>
          <div>
            <div className="eyebrow" style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}><School size={14} /> Giáo viên / Doanh nghiệp</div>
            <h1 style={{ margin: 0, fontSize: 'clamp(1.9rem, 4vw, 2.5rem)' }}>Nhóm của tôi</h1>
            <p style={{ color: 'var(--text-muted)', marginTop: 4, fontSize: '0.9rem' }}>Tạo lớp hoặc nhóm công ty, chia sẻ mã để học viên tham gia, giao bài theo tuần và theo dõi tiến độ.</p>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => { logout(); router.push('/'); }}>Đăng xuất</button>
        </div>

        <Link href="/upgrade" className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap', marginBottom: 'var(--spacing-lg)', opacity: 1, borderColor: home.is_premium ? 'color-mix(in srgb, var(--agen-success) 40%, var(--border-subtle))' : undefined }}>
          <span className="icon-tile" style={{ background: 'color-mix(in srgb, var(--agen-accent) 14%, transparent)', color: 'var(--agen-accent)' }}><Crown size={20} strokeWidth={1.8} /></span>
          <div style={{ flex: 1, minWidth: 220 }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{home.is_premium ? `Gói theo ghế đang hoạt động · ${home.seats} ghế` : 'Gói lớp học / doanh nghiệp theo ghế'}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {home.is_premium ? `${Math.min(home.members_total, home.seats)}/${home.seats} ghế đang dùng · ${home.members_total} thành viên` : `Từ ${Math.round(home.team_prices[0]?.amount_vnd / 1000)}K/ghế/tháng · thành viên nhóm học không giới hạn, báo cáo tiến độ cho người quản lý.`}
            </div>
          </div>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2, color: 'var(--agen-primary-light)', fontSize: '0.9rem', fontWeight: 600 }}>{home.is_premium ? 'Quản lý' : 'Xem gói'} <ChevronRight size={16} /></span>
        </Link>

        <form onSubmit={create} className="card" style={{ marginBottom: 'var(--spacing-lg)', display: 'grid', gap: 10 }}>
          <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}><Plus size={16} /> Tạo nhóm mới</div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <input className="form-input" placeholder="Tên nhóm (Lớp 7A, Phòng Kinh doanh…)" value={name} onChange={e => setName(e.target.value)} required maxLength={100} style={{ flex: '1 1 240px' }} />
            <div className="segmented" role="group" aria-label="Loại nhóm">
              <button type="button" aria-pressed={kind === 'class'} onClick={() => setKind('class')}><School size={14} /> Lớp học</button>
              <button type="button" aria-pressed={kind === 'company'} onClick={() => setKind('company')}><Briefcase size={14} /> Doanh nghiệp</button>
            </div>
            <button type="submit" className="btn btn-primary" disabled={busy || !name.trim()}>{busy ? <LoaderCircle className="animate-spin" size={16} /> : 'Tạo nhóm'}</button>
          </div>
          {error && <div className="alert-error"><CircleAlert size={16} /> {error}</div>}
        </form>

        {home.groups.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px 24px', color: 'var(--text-muted)' }}>
            <Users size={36} strokeWidth={1.4} style={{ marginBottom: 10 }} />
            <div>Chưa có nhóm nào. Tạo nhóm đầu tiên ở trên rồi gửi mã cho học viên.</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 12 }}>
            {home.groups.map(g => (
              <Link key={g.id} href={`/teacher/${g.id}`} className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: 14, opacity: 1 }}>
                <span className="icon-tile">{g.kind === 'company' ? <Briefcase size={20} strokeWidth={1.8} /> : <School size={20} strokeWidth={1.8} />}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{g.name}</div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{g.member_count} thành viên · mã <span className="code-chip" style={{ padding: '1px 8px', fontSize: '0.8rem' }}>{g.code}</span></div>
                </div>
                <ChevronRight size={18} color="var(--text-muted)" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
