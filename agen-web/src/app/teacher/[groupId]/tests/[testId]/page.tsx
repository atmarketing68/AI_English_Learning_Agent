'use client';

/** G14 · Bảng điểm bài kiểm tra lớp để in / lưu PDF (cùng cách in với báo cáo nhóm). */
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, CircleAlert, LoaderCircle, Printer } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { getGroupTestSheet, testScoreLabel } from '@/lib/groupsService';
import Logo from '@/components/ui/Logo';
import { track } from '@/lib/analytics';

type Sheet = Awaited<ReturnType<typeof getGroupTestSheet>>;
const day = (iso: string) => new Date(`${iso}T00:00:00`).toLocaleDateString('vi-VN');
const stamp = (s: string | null) => (s ? new Date(s.endsWith('Z') ? s : `${s}Z`).toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—');

export default function ClassTestSheetPage() {
  const { groupId, testId } = useParams<{ groupId: string; testId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [sheet, setSheet] = useState<Sheet | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    getGroupTestSheet(groupId, testId).then(setSheet).catch(() => setError('Không tải được bảng điểm.'));
  }, [hydrated, isAuthenticated, router, groupId, testId]);

  if (error) return <main className="report-page"><div className="alert-error"><CircleAlert size={16} /> {error}</div></main>;
  if (!sheet) return <main className="report-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={20} /> Đang chuẩn bị bảng điểm…</main>;

  const done = sheet.results.filter(r => r.done);
  const kpis: [string, string][] = [
    ['Đã làm', `${sheet.done_count}/${sheet.member_count}`],
    ['Trung bình', sheet.avg_estimate != null ? testScoreLabel(sheet.exam, { estimate: sheet.avg_estimate, pct: sheet.avg_pct }) : '—'],
    ['Cao nhất', sheet.max_estimate != null ? testScoreLabel(sheet.exam, { estimate: sheet.max_estimate, pct: null }) : '—'],
    ['Thấp nhất', sheet.min_estimate != null ? testScoreLabel(sheet.exam, { estimate: sheet.min_estimate, pct: null }) : '—'],
  ];

  return (
    <main className="report-page">
      <div className="report-toolbar no-print">
        <Link href={`/teacher/${groupId}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem' }}><ArrowLeft size={16} /> {sheet.group_name}</Link>
        <button type="button" className="btn btn-primary" onClick={() => { track('class_test_sheet_printed'); window.print(); }}><Printer size={16} /> Tải PDF / In</button>
      </div>
      <article className="report-sheet">
        <header className="report-head">
          <Logo size={28} />
          <div style={{ textAlign: 'right' }}>
            <div className="eyebrow">Bảng điểm bài kiểm tra lớp</div>
            <div style={{ fontSize: '0.85rem', color: '#86868B' }}>In ngày {new Date().toLocaleDateString('vi-VN')}</div>
          </div>
        </header>
        <h1 className="report-title">{sheet.title}</h1>
        <div className="report-sub">
          Lớp {sheet.group_name} (mã {sheet.group_code}) · Giáo viên {sheet.teacher_name} · Mở {day(sheet.opens_on)} – hạn {day(sheet.due_on)}
          {sheet.repeat ? ' · lặp lại hằng tháng' : ''}
        </div>
        <section className="report-kpis" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          {kpis.map(([label, value]) => <div key={label} className="report-kpi"><strong style={{ fontSize: '1.1rem' }}>{value}</strong><span>{label}</span></div>)}
        </section>
        <table className="report-table">
          <thead><tr><th>#</th><th>Học viên</th><th>Trình độ</th><th>Kết quả</th><th>Thời gian làm</th><th>Nộp lúc</th><th>Chữ ký</th></tr></thead>
          <tbody>
            {sheet.results.map((r, i) => (
              <tr key={r.learner_id}>
                <td>{i + 1}</td><td>{r.display_name}</td><td>{r.level.replace('PRE_', 'Pre-')}</td>
                <td><b>{r.done ? testScoreLabel(sheet.exam, r) : 'Chưa làm'}</b></td>
                <td>{r.seconds ? `${Math.round(r.seconds / 60)} phút` : '—'}</td><td>{stamp(r.submitted_at)}</td><td style={{ minWidth: 90 }} />
              </tr>
            ))}
          </tbody>
        </table>
        {sheet.note && <p style={{ fontSize: '0.85rem', color: '#515154', marginTop: 16 }}>Ghi chú: {sheet.note}</p>}
        <p style={{ fontSize: '0.75rem', color: '#86868B', marginTop: 24 }}>
          {done.length ? 'Điểm là lần làm đầu tiên trong thời hạn; band / điểm là ước tính theo thang của kỳ thi. ' : ''}Bảng điểm tạo tự động bởi AI AGENT ENGLISH.
        </p>
      </article>
    </main>
  );
}
