import api from './api';

export interface StartRoleplayResponse {
  session_id: string;
  topic: string;
  system_prompt: string;
  ai_first_message: string;
}

export interface SpeakingTurnResponse {
  ai_reply: string;
  feedback: string;
  is_correct: boolean;
  score: number;
}

export interface FinishRoleplayResponse {
  xp_earned: number;
  message: string;
}

export const startRoleplay = async (topic: string): Promise<StartRoleplayResponse> => {
  const res = await api.post('/speaking/start', { topic });
  return res.data;
};

export const handleSpeakingTurn = async (
  sessionId: string,
  systemPrompt: string,
  history: { role: 'ai' | 'user'; content: string }[],
  userMessage: string
): Promise<SpeakingTurnResponse> => {
  const res = await api.post('/speaking/reply', {
    session_id: sessionId,
    system_prompt: systemPrompt,
    history,
    user_message: userMessage
  });
  return res.data;
};

export const finishRoleplay = async (
  sessionId: string,
  topic: string,
  totalTurns: number,
  averageScore: number
): Promise<FinishRoleplayResponse> => {
  const res = await api.post('/speaking/finish', {
    session_id: sessionId,
    topic,
    total_turns: totalTurns,
    average_score: averageScore
  });
  return res.data;
};
