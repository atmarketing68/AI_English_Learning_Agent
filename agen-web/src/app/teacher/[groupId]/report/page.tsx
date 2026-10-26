'use client';

/**
 * G8 · Báo cáo nhóm in được (PDF) + xuất CSV cho giáo viên / HR.
 * Same print approach as the parent report: the browser's "Save as PDF".
 */
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, CircleAlert, Download, LoaderCircle, Printer } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { SKILL_LABELS, downloadGroupReport, getGroupDetail, type GroupDetail } from '@/lib/groupsService';
import Logo from '@/components/ui/Logo';
import { track } from '@/lib/analytics';

export default function GroupReportPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [detail, setDetail] = useState<GroupDetail | null>(null);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getGroupDetail(groupId).then(setDetail).catch(() => setError('Không tải được nhóm.'));
  }, [hydrated, isAuthenticated, router, groupId]);

  if (error) return <main className="report-page"><div className="alert-error"><CircleAlert size={16} /> {error}</div></main>;
  if (!detail) return <main className="report-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={20} /> Đang chuẩn bị báo cáo…</main>;

  const { group, members, assignments } = detail;
  const today = new Date();
  const activeToday = members.filter(m => m.active_today).length;
  const avgXp = members.length ? Math.round(members.reduce((n, m) => n + m.weekly_xp, 0) / members.length) : 0;
  const avgStreak = members.length ? Math.round(members.reduce((n, m) => n + m.streak, 0) / members.length) : 0;
  const doneRate = assignments.length && members.length ? Math.round(assignments.reduce((n, a) => n + a.done_count, 0) / (assignments.length * members.length) * 100) : 0;
  const sorted = [...members].sort((a, b) => b.weekly_xp - a.weekly_xp);

  const csv = async () => {
    setDownloading(true);
    try { await downloadGroupReport(group.id, group.name); track('group_report_exported', { format: 'csv' }); }
    catch { setError('Không tải được CSV.'); }
    finally { setDownloading(false); }
  };

  return (
    <main className="report-page">
      <div className="report-toolbar no-print">
        <Link href={`/teacher/${group.id}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem' }}><ArrowLeft size={16} /> {group.name}</Link>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" className="btn btn-outline" onClick={csv} disabled={downloading}>{downloading ? <LoaderCircle className="animate-spin" size={16} /> : <Download size={16} />} Tải CSV (Excel)</button>
          <button type="button" className="btn btn-primary" onClick={() => { track('group_report_exported', { format: 'pdf' }); window.print(); }}><Printer size={16} /> Tải PDF / In</button>
        </div>
      </div>

      <article className="report-sheet" style={{ maxWidth: 900 }}>
        <header className="report-head">
          <Logo size={28} />
          <div style={{ textAlign: 'right' }}>
            <div className="eyebrow">Báo cáo {group.kind === 'company' ? 'nhóm doanh nghiệp' : 'lớp học'}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{today.toLocaleDateString('vi-VN')} · tuần hiện tại</div>
          </div>
        </header>
        <h1 className="report-title">{group.name}</h1>
        <div className="report-sub">Mã {group.code} · {members.length} thành viên · {assignments.length} bài tập đã giao</div>

        <section className="report-kpis">
          {[['Thành viên', members.length], ['Học hôm nay', `${activeToday}/${members.length}`], ['XP tuần TB', avgXp], ['Chuỗi TB', `${avgStreak} ngày`], ['Hoàn thành bài tập', `${doneRate}%`]].map(([label, value]) => (
            <div key={label as string} className="report-kpi"><strong>{value}</strong><span>{label}</span></div>
          ))}
        </section>

        <h2 className="report-h2">Tiến độ từng thành viên</h2>
        <table className="report-table">
          <thead><tr><th>#</th><th>Học viên</th><th>Trình độ</th><th>XP tuần</th><th>Tổng XP</th><th>Chuỗi</th><th>Bài học</th><th>Bài tập</th><th>Hôm nay</th></tr></thead>
          <tbody>
            {sorted.map((m, i) => (
              <tr key={m.learner_id}>
                <td>{i + 1}</td><td>{m.display_name}</td><td>{m.level}</td><td>{m.weekly_xp}</td><td>{m.total_xp}</td><td>{m.streak}</td><td>{m.lessons}</td><td>{m.assignments_done}/{assignments.length}</td><td>{m.active_today ? '✓' : '—'}</td>
              </tr>
            ))}
            {members.length === 0 && <tr><td colSpan={9} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Chưa có thành viên.</td></tr>}
          </tbody>
        </table>

        {assignments.length > 0 && (
          <>
            <h2 className="report-h2">Bài tập đã giao</h2>
            <table className="report-table">
              <thead><tr><th>Bài tập</th><th>Kỹ năng</th><th>Chủ đề</th><th>Hạn</th><th>Đã xong</th></tr></thead>
              <tbody>
                {assignments.map(a => (
                  <tr key={a.id}><td>{a.title}</td><td>{SKILL_LABELS[a.skill]}</td><td>{a.topic}</td><td>{a.due_on ? new Date(a.due_on).toLocaleDateString('vi-VN') : '—'}</td><td>{a.done_count}/{a.member_count}</td></tr>
                ))}
              </tbody>
            </table>
          </>
        )}
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 24 }}>XP tuần tính từ thứ Hai theo giờ Việt Nam. Báo cáo tạo tự động bởi AI AGENT ENGLISH.</p>
      </article>
    </main>
  );
}
