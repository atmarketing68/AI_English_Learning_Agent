import api from '@/lib/api';

// ── G8 · Hỏi Bo: chatbot ngữ pháp bằng tiếng Việt ────────────────────────────
export interface TutorExample { en: string; vi: string }

export interface TutorMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  rule: string;
  examples: TutorExample[];
  common_mistake: string;
  follow_ups: string[];
  fallback: boolean;
  created_at: string;
}

export interface TutorHome {
  messages: TutorMessage[];
  suggested: string[];
  is_premium: boolean;
  free_daily_limit: number;
  asked_today: number;
  remaining_today: number | null;
}

export interface AskResult {
  question: TutorMessage;
  answer: TutorMessage;
  asked_today: number;
  remaining_today: number | null;
}

export const getTutorHome = async (): Promise<TutorHome> => (await api.get('/tutor')).data;
export const askTutor = async (question: string): Promise<AskResult> => (await api.post('/tutor/ask', { question })).data;
export const clearTutorHistory = async (): Promise<void> => { await api.delete('/tutor'); };
