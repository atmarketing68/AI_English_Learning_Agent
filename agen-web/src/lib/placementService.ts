import api from './api';

// --- Placement Test Service ---
export interface PlacementStartRes {
  session_id: string;
  message: string;
  total_questions: number;
  assessment_type: 'baseline' | 'followup';
}

export interface PlacementQuestion {
  session_id: string;
  question_index: number;
  total_questions: number;
  skill: string;
  level: string;
  passage?: string | null;
  question: string;
  options: Record<string, string>;
  /** Listening item: play this, never show it before answering. */
  audio_text?: string | null;
  /** Speaking item: sentence to read aloud; the answer is the transcript. */
  target_text?: string | null;
  instruction_vi?: string | null;
}

/** Answer value for a speaking item when the learner has no microphone. */
export const PLACEMENT_SKIP = '__skip__';

export interface PlacementAnswerRes {
  is_correct: boolean;
  correct_answer: string;
  explanation: string;
  score_delta: number;
  question_index: number;
  total_questions: number;
  is_finished: boolean;
  skipped?: boolean;
  speaking_score?: number | null;
}

export interface PlacementResult {
  assessment_type: 'baseline' | 'followup';
  overall_level: string;
  skill_scores: Record<string, number>;
  total_correct: number;
  total_questions: number;
  accuracy_percent: number;
  recommendations: string[];
  message: string;
}

export async function startPlacement(assessmentType: 'baseline' | 'followup' = 'baseline'): Promise<PlacementStartRes> {
  const res = await api.post(`/placement/start?assessment_type=${assessmentType}`);
  return res.data;
}

export async function getPlacementQuestion(sessionId: string): Promise<PlacementQuestion> {
  const res = await api.get(`/placement/question?session_id=${sessionId}`);
  return res.data;
}

export async function submitAnswer(sessionId: string, answer: string): Promise<PlacementAnswerRes> {
  const res = await api.post('/placement/answer', { session_id: sessionId, answer });
  return res.data;
}

export async function finishPlacement(sessionId: string): Promise<PlacementResult> {
  const res = await api.post(`/placement/finish?session_id=${sessionId}`);
  return res.data;
}
