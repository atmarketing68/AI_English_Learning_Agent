'use client';

/**
 * G6 · Báo cáo tuần in được (PDF) cho phụ huynh.
 * A print-styled page: "Tải PDF" opens the browser's print dialog, where
 * "Save as PDF" is available on every platform — no server-side PDF library.
 */
import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, BookOpen, CircleAlert, CircleCheck, Clock, Flame, Lightbulb, LoaderCircle, Printer, Star, Target, TriangleAlert } from 'lucide-react';
import { useAuthHydrated, useAuthStore } from '@/store/authStore';
import { getChildReport, getChildren, type ChildReport, type ChildSummary } from '@/lib/parentService';
import Logo from '@/components/ui/Logo';
import { track } from '@/lib/analytics';

const SKILL_COLORS: Record<string, string> = {
  vocabulary: '#D97A00', grammar: '#0071E3', reading: '#1F9D55', listening: '#0A84C6', speaking: '#D6336C', writing: '#8E4EC6',
};

export default function ParentReportPage() {
  const { learnerId } = useParams<{ learnerId: string }>();
  const router = useRouter();
  const hydrated = useAuthHydrated();
  const { isAuthenticated } = useAuthStore();
  const [child, setChild] = useState<ChildSummary | null>(null);
  const [report, setReport] = useState<ChildReport | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hydrated) return;
    if (!isAuthenticated) { router.push('/login'); return; }
    Promise.all([getChildren(), getChildReport(learnerId)])
      .then(([kids, r]) => { setChild(kids.find(k => k.learner_id === learnerId) || null); setReport(r); })
      .catch(() => setError('Không tải được báo cáo.'));
  }, [hydrated, isAuthenticated, learnerId, router]);

  const print = () => { track('parent_report_printed'); window.print(); };

  if (error) return <main className="report-page"><div className="alert-error"><CircleAlert size={16} /> {error}</div></main>;
  if (!report) return <main className="report-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, color: 'var(--text-muted)' }}><LoaderCircle className="animate-spin" size={20} /> Đang chuẩn bị báo cáo…</main>;

  const today = new Date();
  const weekAgo = new Date(today.getTime() - 6 * 86_400_000);
  const fmt = (d: Date) => d.toLocaleDateString('vi-VN');
  const kpis = [
    { label: 'Buổi học', value: report.sessions_this_week, icon: BookOpen, color: '#0071E3' },
    { label: 'XP tuần', value: report.xp_this_week, icon: Star, color: '#D97A00' },
    { label: 'Phút học (ước tính)', value: report.study_minutes_estimate, icon: Clock, color: '#0A84C6' },
    { label: 'Chuỗi ngày', value: report.current_streak, icon: Flame, color: '#E0352B' },
    { label: 'Độ chính xác', value: `${report.accuracy_pct}%`, icon: Target, color: '#1F9D55' },
  ];

  return (
    <main className="report-page">
      <div className="report-toolbar no-print">
        <Link href="/parent" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.92rem' }}><ArrowLeft size={16} /> Bảng phụ huynh</Link>
        <button type="button" className="btn btn-primary" onClick={print}><Printer size={16} /> Tải PDF / In</button>
      </div>

      <article className="report-sheet">
        <header className="report-head">
          <Logo size={28} />
          <div style={{ textAlign: 'right' }}>
            <div className="eyebrow">Báo cáo tuần</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>{fmt(weekAgo)} – {fmt(today)}</div>
          </div>
        </header>

        <h1 className="report-title">{report.display_name}</h1>
        <div className="report-sub">Trình độ {report.overall_level}{child?.total_lessons_completed != null && ` · ${child.total_lessons_completed} bài đã hoàn thành`}{child?.relationship_label && ` · ${child.relationship_label}`}</div>

        <section className="report-kpis">
          {kpis.map(k => (
            <div key={k.label} className="report-kpi">
              <k.icon size={16} color={k.color} />
              <strong>{k.value}</strong>
              <span>{k.label}</span>
            </div>
          ))}
        </section>

        <section className="report-section">
          <h2>Hồ sơ kỹ năng</h2>
          <div className="report-skills">
            {report.skills.map(sk => (
              <div key={sk.skill} className="report-skill">
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', marginBottom: 4 }}>
                  <span>{sk.label}</span><strong>{sk.score.toFixed(0)}%</strong>
                </div>
                <div className="report-bar"><span style={{ width: `${sk.score}%`, background: SKILL_COLORS[sk.skill] || '#0071E3' }} /></div>
              </div>
            ))}
          </div>
          <p style={{ fontSize: '0.85rem', marginTop: 10 }}>Mạnh nhất: <strong>{report.best_skill}</strong> · Cần tập trung: <strong>{report.focus_skill}</strong></p>
        </section>

        <section className="report-section">
          <h2>Nhận xét từ AI Coach</h2>
          <div className="report-notes">
            <div><h3><CircleCheck size={15} color="#1F9D55" /> Con đã tiến bộ gì?</h3><p>{report.what_improved}</p></div>
            <div><h3><TriangleAlert size={15} color="#D97A00" /> Con cần hỗ trợ gì?</h3><p>{report.what_needs_help}</p></div>
            <div><h3><Lightbulb size={15} color="#0071E3" /> Phụ huynh nên làm gì?</h3><p>{report.what_to_do}</p></div>
          </div>
        </section>

        <footer className="report-foot">
          AI AGENT ENGLISH · Báo cáo tạo ngày {fmt(today)} · Số liệu tính trong 7 ngày gần nhất theo giờ Việt Nam.
        </footer>
      </article>
    </main>
  );
}
