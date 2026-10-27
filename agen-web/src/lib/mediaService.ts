import api from '@/lib/api';

// ── G10 · Học qua podcast / video ngắn ───────────────────────────────────────
export interface EpisodeSummary {
  id: string;
  kind: 'podcast' | 'video';
  level: string;
  minutes: number;
  topic: string;
  title: string;
  title_vi: string;
  description_vi: string;
  has_video: boolean;
  best_score: number | null;
  completed: boolean;
}

export interface EpisodeLine { speaker: string; text: string; vi: string }
export interface EpisodeQuestion { id: string; prompt: string; options: string[] }

export interface Episode extends Omit<EpisodeSummary, 'best_score' | 'completed' | 'has_video'> {
  youtube_id: string | null;
  start?: number;
  end?: number;
  lines: EpisodeLine[];
  vocab: { word: string; definition: string }[];
  questions: EpisodeQuestion[];
}

export interface MediaResult {
  correct: number;
  total: number;
  pct: number;
  details: { id: string; correct: boolean; expected: string; explanation_vi: string }[];
  xp_earned: number;
  gems_earned: number;
  best_score: number;
}

export const listEpisodes = async (): Promise<EpisodeSummary[]> => (await api.get('/media')).data;
export const getEpisode = async (id: string): Promise<Episode> => (await api.get(`/media/${id}`)).data;
export const submitEpisode = async (id: string, answers: Record<string, number>): Promise<MediaResult> =>
  (await api.post(`/media/${id}/submit`, { answers })).data;
