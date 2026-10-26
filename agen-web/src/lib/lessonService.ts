import api from '@/lib/api';
import { track } from '@/lib/analytics';

// ── Types ────────────────────────────────────────────────────────────────────
export interface Exercise {
  id: string;
  order: number;
  type: 'multiple_choice' | 'fill_blank' | 'flashcard' | 'writing_prompt'
    | 'word_bank' | 'match_pairs' | 'listen_choose' | 'dictation' | 'speak_repeat' | 'dialogue_order';
  content: Record<string, unknown>;
  user_answer?: string;
  is_correct?: boolean;
}

export interface LessonDetail {
  id: string;
  skill: string;
  topic: string;
  level: string;
  title: string;
  summary?: string;
  content?: {
    text?: string;
    script_lines?: { speaker: string; text: string }[];
    vocabulary_highlights?: { word: string; definition: string }[];
    // Vocabulary lesson content (stored by backend after BUG#7 fix)
    vocabulary?: {
      word: string;
      phonetic?: string;
      part_of_speech?: string;
      definition: string;
      translation: string;
      example: string;
      image_hint?: string;
    }[];
    // Grammar lessons: the rule taught before the exercises
    explanation?: GrammarExplanation;
  };
  status: string;
  score: number;
  xp_earned: number;
  total_exercises: number;
  correct_exercises: number;
  exercises: Exercise[];
  created_at: string;
  completed_at?: string;
}

export interface GrammarExplanation {
  rule?: string;
  rule_vi?: string;
  structure?: string;
  examples?: { en: string; vi: string }[];
  common_mistakes?: string[];
}

export interface LessonSummary {
  id: string;
  skill: string;
  topic: string;
  level: string;
  title: string;
  status: string;
  score: number;
  xp_earned: number;
  created_at: string;
}

export interface DailyRecommendation {
  skill: string;
  topic: string;
  reason: string;
  icon: string;
}

export interface FinishLessonResult {
  lesson_id: string;
  score: number;
  grade: string;
  correct: number;
  total: number;
  xp_earned: number;
  message: string;
  adaptive_decision?: string | null;
  adaptive_reason?: string | null;
  recommended_difficulty?: number | null;
  words_saved?: number;
}

export interface SubmitExerciseResult {
  exercise_id: string;
  is_correct: boolean;
  correct_answer?: string;
  explanation?: string;
}

export interface LessonGenerationAccepted {
  job_id: string;
  trace_id: string;
  status: 'queued' | 'running';
  poll_url: string;
}

export interface LessonGenerationJob {
  job_id: string;
  trace_id: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed';
  result?: { lesson_id: string } | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
}

// ── API Calls ────────────────────────────────────────────────────────────────
/** Thrown when the learner has hit their daily free-tier lesson limit (HTTP 402). */
export class LessonQuotaError extends Error {}

export async function generateLesson(skill: string, topic?: string, curriculumCode?: string): Promise<LessonDetail> {
  const startedAt = Date.now();
  const waited = (cached: boolean) =>
    track('lesson_generation_waited', { skill, cached, ms: Date.now() - startedAt, from_curriculum: !!curriculumCode });
  let res;
  try {
    res = await api.post<LessonDetail | LessonGenerationAccepted>('/lessons/generate', {
      skill,
      topic: topic || null,
      curriculum_code: curriculumCode || null,
      // Cached curriculum content still returns synchronously (200). Anything the
      // AI has to write runs as a background job we poll, so a 30–120s generation
      // never holds an HTTP request (and a server worker) open.
      background: true,
    });
  } catch (err: unknown) {
    const response = (err as { response?: { status?: number; data?: { detail?: string } } })?.response;
    if (response?.status === 402) {
      track('daily_limit_reached', { skill });
      throw new LessonQuotaError(response.data?.detail || 'Bạn đã hết lượt học miễn phí hôm nay.');
    }
    throw err;
  }

  if (res.status !== 202 || !('job_id' in res.data)) {
    waited(true);
    return res.data as LessonDetail;
  }

  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    const job = await getLessonGenerationJob(res.data.job_id);
    if (job.status === 'succeeded' && job.result?.lesson_id) {
      waited(false);
      return getLessonDetail(job.result.lesson_id);
    }
    if (job.status === 'failed') {
      throw new Error(job.error || 'Không thể tạo bài học.');
    }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  throw new Error('Tạo bài học mất quá nhiều thời gian. Vui lòng thử lại.');
}

export async function getLessonGenerationJob(jobId: string): Promise<LessonGenerationJob> {
  const res = await api.get<LessonGenerationJob>(`/lessons/generation-jobs/${jobId}`);
  return res.data;
}

export async function getMyLessons(skill?: string): Promise<LessonSummary[]> {
  const params = skill ? `?skill=${skill}` : '';
  const res = await api.get(`/lessons/me${params}`);
  return res.data;
}

export async function getDailyRecommendations(): Promise<DailyRecommendation[]> {
  const res = await api.get('/lessons/daily');
  return res.data;
}

export async function getLessonDetail(lessonId: string): Promise<LessonDetail> {
  const res = await api.get(`/lessons/${lessonId}`);
  return res.data;
}

export async function submitExerciseAnswer(
  lessonId: string,
  exerciseId: string,
  answer: string
): Promise<SubmitExerciseResult> {
  const res = await api.post(`/lessons/${lessonId}/submit-exercise`, {
    exercise_id: exerciseId,
    answer,
  });
  return res.data;
}

export async function finishLesson(lessonId: string): Promise<FinishLessonResult> {
  const res = await api.post(`/lessons/${lessonId}/finish`);
  return res.data;
}

/** AI "Vì sao sai?" — a short Vietnamese explanation of a wrong answer. */
export async function explainMistake(lessonId: string, exerciseId: string): Promise<{ explanation: string; source: 'ai' | 'cached' | 'fallback' }> {
  const { data } = await api.post(`/lessons/${lessonId}/exercises/${exerciseId}/explain`);
  return data;
}
