import api from './api';

// ── Scenarios (G2 · Luyện nói 3 bước) ────────────────────────────────────────
export interface Persona {
  name: string;
  role_en: string;
  role_vi: string;
  style: string;
  voice: 'female' | 'male';
}

export interface Phrase {
  en: string;
  vi: string;
}

export interface ScenarioSummary {
  id: string;
  category: string;
  level: string;
  emoji: string;
  title_vi: string;
  title_en: string;
  persona: Persona;
  learner_role_en: string;
  learner_role_vi: string;
  goal_en: string;
  goal_vi: string;
  first_message: string;
  phrase_count: number;
  recommended: boolean;
}

export interface ScenarioDetail extends ScenarioSummary {
  phrases: Phrase[];
}

export interface ScenarioList {
  categories: Record<string, string>;
  learner_level: string;
  scenarios: ScenarioSummary[];
}

export async function getScenarios(): Promise<ScenarioList> {
  const res = await api.get('/speaking/scenarios');
  return res.data;
}

export async function getScenario(id: string): Promise<ScenarioDetail> {
  const res = await api.get(`/speaking/scenarios/${id}`);
  return res.data;
}

// ── Roleplay ─────────────────────────────────────────────────────────────────
export interface StartRoleplayResponse {
  session_id: string;
  topic: string;
  system_prompt: string;
  ai_first_message: string;
  scenario_id?: string | null;
  persona?: Persona | null;
}

export interface SpeakingTurnResponse {
  ai_reply: string;
  feedback: string;
  is_correct: boolean;
  score: number;
  corrected: string;
  hint_en: string;
}

export interface FinishRoleplayResponse {
  xp_earned: number;
  message: string;
  total_turns: number;
  average_score: number;
}

export const startRoleplay = async (topic: string): Promise<StartRoleplayResponse> => {
  const res = await api.post('/speaking/start', { topic });
  return res.data;
};

export const startScenarioRoleplay = async (scenarioId: string): Promise<StartRoleplayResponse> => {
  const res = await api.post('/speaking/start', { scenario_id: scenarioId });
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
