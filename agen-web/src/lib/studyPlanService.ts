import api from '@/lib/api';
import type { ExamKind } from '@/lib/examsService';

// ── G9 · Kế hoạch ôn thi ─────────────────────────────────────────────────────
export type PlanSkill = 'listening' | 'reading' | 'writing' | 'speaking';
export type PlanStatus = 'unset' | 'no_data' | 'on_track' | 'behind' | 'ahead' | 'past';

export interface PlanWeek {
  index: number;
  start: string;
  end: string;
  focus: PlanSkill[];
  lessons: number;
  mock_tests: number;
  writing_tasks: number;
  speaking_sessions: number;
  is_current: boolean;
}

export interface StudyPlan {
  configured: boolean;
  exam: ExamKind | null;
  target_score: number | null;
  exam_date: string | null;
  days_left: number | null;
  weeks_left: number | null;
  current: Partial<Record<PlanSkill, number | null>>;
  current_overall: number | null;
  gap: number | null;
  projected: number | null;
  status: PlanStatus;
  status_vi: string;
  weekly_lessons: number;
  this_week: { lessons: number; mock_tests: number; writing_tasks: number; speaking_sessions: number } | Record<string, number>;
  weeks: PlanWeek[];
  advice_vi: string[];
  skill_labels: Record<string, string>;
}

export const getStudyPlan = async (): Promise<StudyPlan> => (await api.get('/study-plan')).data;
export const setStudyPlan = async (exam: ExamKind, targetScore: number, examDate: string): Promise<StudyPlan> =>
  (await api.put('/study-plan', { exam, target_score: targetScore, exam_date: examDate })).data;
export const clearStudyPlan = async (): Promise<StudyPlan> => (await api.delete('/study-plan')).data;

export const formatTarget = (exam: ExamKind | null, v: number | null | undefined) => (v == null ? '—' : exam === 'ielts' ? v.toFixed(1) : String(Math.round(v)));
export const STATUS_COLOR: Record<PlanStatus, string> = { unset: 'var(--text-muted)', no_data: 'var(--text-muted)', on_track: 'var(--agen-success)', ahead: 'var(--agen-success)', behind: 'var(--agen-secondary)', past: 'var(--text-muted)' };
export const STATUS_LABEL: Record<PlanStatus, string> = { unset: 'Chưa đặt', no_data: 'Chưa có dữ liệu', on_track: 'Đúng tiến độ', ahead: 'Vượt tiến độ', behind: 'Chậm tiến độ', past: 'Đã qua ngày thi' };
