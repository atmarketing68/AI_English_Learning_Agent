'use client';

/** G9 · Dashboard card: exam countdown and this week's progress (or a prompt to set a target). */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { CalendarDays, ChevronRight } from 'lucide-react';
import { EXAM_LABEL } from '@/lib/examsService';
import { STATUS_COLOR, STATUS_LABEL, formatTarget, getStudyPlan, type StudyPlan } from '@/lib/studyPlanService';

export default function ExamPlanCard({ goal }: { goal?: string | null }) {
  const [plan, setPlan] = useState<StudyPlan | null>(null);
  useEffect(() => { getStudyPlan().then(setPlan).catch(() => null); }, []);
  if (!plan) return null;
  if (!plan.configured && goal !== 'luyen_thi' && goal !== 'thi_dau_vao' && goal !== 'ielts' && goal !== 'toeic') return null;
  const color = STATUS_COLOR[plan.status];
  return (
    <Link href="/plan" className="card card-hover" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: 'var(--spacing-lg)', borderRadius: 'var(--radius-xl)', opacity: 1 }}>
      <span className="icon-tile" style={{ flexShrink: 0, width: 48, height: 48, borderRadius: 16, background: `color-mix(in srgb, ${plan.configured ? color : 'var(--agen-primary)'} 14%, transparent)`, color: plan.configured ? color : 'var(--agen-primary)' }}>
        <CalendarDays size={24} strokeWidth={1.8} />
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="eyebrow" style={{ marginBottom: 4 }}>{plan.configured ? `${EXAM_LABEL[plan.exam!]} · mục tiêu ${formatTarget(plan.exam, plan.target_score)}` : 'Kế hoạch ôn thi'}</div>
        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          {plan.configured ? `Còn ${Math.max(0, plan.days_left ?? 0)} ngày · ${STATUS_LABEL[plan.status]}` : 'Đặt ngày thi để có lộ trình theo tuần'}
        </div>
        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
          {plan.configured ? `Tuần này ${plan.this_week.lessons ?? 0}/${plan.weekly_lessons} bài · hiện tại ${formatTarget(plan.exam, plan.current_overall)}` : 'App chia kỹ năng theo tuần và báo khi bạn chậm tiến độ.'}
        </div>
      </div>
      <ChevronRight size={18} color="var(--text-muted)" />
    </Link>
  );
}
