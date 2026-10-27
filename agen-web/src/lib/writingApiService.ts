import api from './api';

export interface WritingPromptResponse {
  title: string;
  prompt: string;
  genre: string;
  word_target: string;
  guide_steps: string[];
  useful_phrases: string[];
  example_opening: string;
  level: string;
  topic: string;
}

export interface GrammarError {
  original: string;
  corrected: string;
  explanation_vi: string;
}

export interface EvaluationScores {
  grammar: number;
  vocabulary: number;
  coherence: number;
  task_achievement: number;
}

/** G5 · exam-style band: IELTS 0–9 or TOEIC Writing 0–200. */
export interface ExamBand {
  exam: 'ielts' | 'toeic';
  overall: number;
  criteria: Record<string, number>;
  next_band_tips: string[];
}

export type WritingGenre = 'opinion' | 'narrative' | 'descriptive' | 'email' | 'ielts_task2' | 'ielts_task1' | 'toeic_email' | 'toeic_essay';
export const EXAM_GENRES: WritingGenre[] = ['ielts_task2', 'ielts_task1', 'toeic_email', 'toeic_essay'];

export interface WritingEvaluationResponse {
  submission_id: string;
  overall_score: number;
  grade: string;
  word_count: number;
  scores: EvaluationScores;
  grammar_errors: GrammarError[];
  vocabulary_feedback: string;
  coherence_feedback: string;
  strengths: string[];
  improvements: string[];
  corrected_version: string;
  encouragement: string;
  xp_earned: number;
  exam_band?: ExamBand | null;
}

export interface WritingHistoryItem {
  id: string;
  prompt_title: string;
  genre: string;
  level: string;
  overall_score: number | null;
  grade: string | null;
  word_count: number;
  xp_earned: number;
  created_at: string;
  /** G11 · exam band from the AI, and the teacher's re-grade when there is one */
  band?: number | null;
  teacher_score?: number | null;
  teacher_band?: number | null;
  teacher_comment?: string | null;
  teacher_scored_at?: string | null;
  /** G12 · IELTS criteria the teacher scored */
  teacher_rubric?: { task: number; coherence: number; lexical: number; grammar: number } | null;
}

export const getWritingPrompt = async (genre: string = 'opinion'): Promise<WritingPromptResponse> => {
  const res = await api.post('/writing/prompt', { genre });
  return res.data;
};

export const submitWriting = async (
  promptTitle: string,
  promptText: string,
  genre: string,
  userText: string
): Promise<WritingEvaluationResponse> => {
  const res = await api.post('/writing/submit', {
    prompt_title: promptTitle,
    prompt_text: promptText,
    genre,
    user_text: userText,
  });
  return res.data;
};

export const getWritingHistory = async (limit: number = 10): Promise<WritingHistoryItem[]> => {
  const res = await api.get(`/writing/history?limit=${limit}`);
  return res.data;
};
