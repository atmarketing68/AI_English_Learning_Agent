import api from '@/lib/api';
import type { ExamKind } from '@/lib/examsService';

// ── G9 · Thi thử Speaking ────────────────────────────────────────────────────
export type TaskKind = 'question' | 'cue_card' | 'read_aloud' | 'opinion';

export interface SpeakingTask {
  id: string;
  part: string;
  kind: TaskKind;
  prompt: string;
  prep_seconds: number;
  answer_seconds: number;
  tip_vi: string;
  reference: string | null;
  cue: string[];
}

export interface SpeakingPaper {
  id: string;
  exam: ExamKind;
  minutes: number;
  title: string;
  description: string;
  tasks: SpeakingTask[];
}

export interface SpeakingExamSummary {
  id: string;
  exam: ExamKind;
  title: string;
  description: string;
  minutes: number;
  tasks: number;
  attempts: number;
  best_estimate: number | null;
  last_at: string | null;
}

export interface SpeakingCatalogue {
  exams: SpeakingExamSummary[];
  is_premium: boolean;
  free_daily_attempts: number;
  attempts_today: number;
  can_start: boolean;
}

export interface TaskFeedback {
  task_id: string;
  part: string;
  prompt: string;
  transcript: string;
  words: number;
  pronunciation: number | null;
  comment_vi: string;
  corrections: { original: string; corrected: string }[];
}

export interface SpeakingResult {
  attempt_id: string;
  exam_id: string;
  exam: ExamKind;
  title: string;
  overall: number;
  criteria: Record<string, number>;
  tasks: TaskFeedback[];
  strengths: string[];
  improvements: string[];
  next_band_tips: string[];
  fallback: boolean;
  xp_earned: number;
  gems_earned: number;
  finished_at: string | null;
}

export interface SpeakingHistoryItem {
  id: string;
  exam_id: string;
  title: string;
  exam: ExamKind;
  overall: number | null;
  status: 'started' | 'finished';
  created_at: string;
}

export const getSpeakingCatalogue = async (): Promise<SpeakingCatalogue> => (await api.get('/speaking-exams')).data;
export const getSpeakingHistory = async (limit = 10): Promise<SpeakingHistoryItem[]> => (await api.get(`/speaking-exams/history?limit=${limit}`)).data;
export const startSpeakingExam = async (examId: string): Promise<{ attempt_id: string; exam: SpeakingPaper }> => (await api.post(`/speaking-exams/${examId}/start`)).data;
export const answerSpeakingTask = async (attemptId: string, taskId: string, transcript: string, durationSeconds: number): Promise<{ task_id: string; words: number; pronunciation: number | null; answered: number; total: number }> =>
  (await api.post(`/speaking-exams/attempts/${attemptId}/answer`, { task_id: taskId, transcript, duration_seconds: durationSeconds })).data;
export const finishSpeakingExam = async (attemptId: string): Promise<SpeakingResult> => (await api.post(`/speaking-exams/attempts/${attemptId}/finish`)).data;
export const getSpeakingResult = async (attemptId: string): Promise<SpeakingResult> => (await api.get(`/speaking-exams/attempts/${attemptId}`)).data;

export const CRITERIA_VI: Record<string, string> = {
  fluency_coherence: 'Trôi chảy & mạch lạc', lexical_resource: 'Từ vựng', grammatical_range: 'Ngữ pháp', pronunciation: 'Phát âm',
  intonation: 'Ngữ điệu', grammar: 'Ngữ pháp', vocabulary: 'Từ vựng', cohesion: 'Liên kết', content: 'Nội dung',
};
export const formatSpeakingEstimate = (exam: ExamKind, v: number) => (exam === 'ielts' ? `Band ${v.toFixed(1)}` : `${Math.round(v)}/200`);
