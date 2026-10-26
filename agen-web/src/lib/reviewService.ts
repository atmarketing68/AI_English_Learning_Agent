import api from '@/lib/api';

// ── Types ────────────────────────────────────────────────────────────────────
export type PromptType = 'meaning' | 'word' | 'mistake';
export type NotebookKind = 'vocab' | 'mistake';

export interface ReviewSummary {
  due_count: number;
  vocab_total: number;
  mistake_total: number;
  mastered_count: number;
  next_due_at: string | null;
  xp_today: number;
}

export interface ReviewQuestion {
  item_id: string;
  kind: NotebookKind;
  prompt_type: PromptType;
  prompt: string;
  hint: string | null;
  speak: string | null;
  options: string[];   // empty → type the answer
}

export interface ReviewAnswerResult {
  correct: boolean;
  correct_answer: string;
  explanation: string | null;
  example: string | null;
  interval_days: number;
  strength: number;
  mastered: boolean;
  xp_earned: number;
}

export interface NotebookItem {
  id: string;
  kind: NotebookKind;
  front: string;
  back: string;
  phonetic: string | null;
  example: string | null;
  explanation: string | null;
  last_wrong_answer: string | null;
  strength: number;   // recall probability now, 0–100
  mastery: number;    // progress towards mastered, 0–100
  mastered: boolean;
  reps: number;
  lapses: number;
  due_at: string;
  created_at: string;
}

// ── API ──────────────────────────────────────────────────────────────────────
export async function getReviewSummary(): Promise<ReviewSummary> {
  const { data } = await api.get('/review/summary');
  return data;
}

export async function getReviewSession(opts: { limit?: number; ahead?: boolean } = {}): Promise<{ questions: ReviewQuestion[]; due_count: number }> {
  const { data } = await api.get('/review/session', { params: { limit: opts.limit ?? 15, ahead: opts.ahead ?? false } });
  return data;
}

export async function answerReview(itemId: string, promptType: PromptType, answer: string): Promise<ReviewAnswerResult> {
  const { data } = await api.post(`/review/items/${itemId}/answer`, { prompt_type: promptType, answer });
  return data;
}

export async function getNotebook(kind: NotebookKind, q?: string): Promise<{ items: NotebookItem[]; total: number }> {
  const { data } = await api.get('/review/items', { params: { kind, q: q || undefined, limit: 200 } });
  return data;
}

export async function deleteNotebookItem(itemId: string): Promise<void> {
  await api.delete(`/review/items/${itemId}`);
}

/** API timestamps are naive UTC; parse them as UTC, not local time. */
export function parseUtc(value: string): Date {
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`);
}

/** "4 ngày" style label for a review interval. */
export function intervalLabel(days: number): string {
  if (days < 1) return 'ít phút';
  if (days < 30) return `${Math.round(days)} ngày`;
  if (days < 365) return `${Math.round(days / 30)} tháng`;
  return '1 năm';
}

// ── G2 · tap-a-word in a listening transcript ────────────────────────────────
export interface WordLookup {
  word: string;
  phonetic: string;
  part_of_speech: string;
  meaning_vi: string;
  definition_en: string;
  example: string;
}

export async function lookupWord(word: string, context?: string): Promise<WordLookup> {
  const { data } = await api.get('/review/lookup', { params: { word, context: context ?? '' } });
  return data;
}

export async function addNotebookWord(payload: {
  word: string; meaning: string; phonetic?: string; example?: string; source_lesson_id?: string;
}): Promise<{ item: NotebookItem; created: boolean }> {
  const { data } = await api.post('/review/items', payload);
  return data;
}

// ── G4 · Blitz 60 giây ───────────────────────────────────────────────────────
export interface BlitzQuestion {
  prompt: string;        // English word
  options: string[];     // 4 Vietnamese meanings
  answer: number;        // index of the right option
  phonetic: string | null;
}

export interface BlitzRound {
  questions: BlitzQuestion[];
  seconds: number;
  from_notebook: number;
}

export interface BlitzResult {
  xp_earned: number;
  gems_earned: number;
  total_xp: number;
  gems: number;
  daily_xp_left: number;
}

export async function getBlitzRound(): Promise<BlitzRound> {
  const { data } = await api.get('/review/blitz');
  return data;
}

export async function submitBlitzResult(payload: { correct: number; answered: number; seconds: number }): Promise<BlitzResult> {
  const { data } = await api.post('/review/blitz/result', payload);
  return data;
}
