import api from '@/lib/api';

// ── G8 · Thi thử IELTS / TOEIC ────────────────────────────────────────────────
export type ExamKind = 'ielts' | 'toeic';
export type ExamSkill = 'listening' | 'reading';
export type QuestionType = 'mc' | 'gap' | 'tfng';

export interface ExamSummary {
  id: string;
  exam: ExamKind;
  skill: ExamSkill;
  title: string;
  description: string;
  minutes: number;
  questions: number;
  attempts: number;
  best_pct: number | null;
  best_estimate: number | null;
  last_at: string | null;
}

export interface ExamCatalogue {
  exams: ExamSummary[];
  is_premium: boolean;
  free_daily_attempts: number;
  attempts_today: number;
  can_start: boolean;
}

export interface AudioLine { speaker: string; text: string; voice: 'female' | 'male' }

export interface ExamQuestion {
  id: string;
  type: QuestionType;
  prompt: string;
  options?: string[];
  audio?: AudioLine[];          // TOEIC Part 2: each question has its own audio
}

export interface ExamSection {
  id: string;
  title: string;
  instructions: string;
  audio?: AudioLine[];
  passage?: string;
  per_question_audio?: boolean;
  questions: ExamQuestion[];
}

export interface ExamPaper {
  id: string;
  exam: ExamKind;
  skill: ExamSkill;
  title: string;
  description: string;
  minutes: number;
  sections: ExamSection[];
}

export interface SectionResult { id: string; title: string; correct: number; total: number }
export interface QuestionResult { id: string; section_id: string; correct: boolean; given: string; expected: string; explanation_vi: string }

export interface ExamResult {
  attempt_id: string;
  exam: ExamKind;
  skill: ExamSkill;
  correct: number;
  total: number;
  pct: number;
  estimate: number;
  sections: SectionResult[];
  details: QuestionResult[];
  xp_earned: number;
  gems_earned: number;
  best_estimate: number;
}

export interface ExamAttempt {
  id: string;
  exam_id: string;
  title: string;
  exam: ExamKind;
  skill: ExamSkill;
  correct: number;
  total: number;
  pct: number;
  estimate: number;
  seconds: number | null;
  created_at: string;
}

export const getExamCatalogue = async (): Promise<ExamCatalogue> => (await api.get('/exams')).data;
export const getExamHistory = async (limit = 20): Promise<ExamAttempt[]> => (await api.get(`/exams/history?limit=${limit}`)).data;
export const getExamPaper = async (examId: string): Promise<ExamPaper> => (await api.get(`/exams/${examId}`)).data;
export const submitExam = async (examId: string, answers: Record<string, string | number>, seconds: number): Promise<ExamResult> =>
  (await api.post(`/exams/${examId}/submit`, { answers, seconds })).data;

export const EXAM_LABEL: Record<ExamKind, string> = { ielts: 'IELTS', toeic: 'TOEIC' };
export const SKILL_LABEL: Record<ExamSkill, string> = { listening: 'Listening', reading: 'Reading' };
/** "Band 6.5" or "415/495" for display. */
export const formatEstimate = (exam: ExamKind, estimate: number) => (exam === 'ielts' ? `Band ${estimate.toFixed(1)}` : `${Math.round(estimate)}/495`);
