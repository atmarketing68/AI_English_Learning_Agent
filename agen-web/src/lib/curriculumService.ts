import api from '@/lib/api';

// ── Types (mirror backend api/curriculum.py schemas) ──────────────────────────
export interface CurriculumLessonNode {
  id: string;
  code: string;
  order: number;
  title: string;
  skill: string;
  difficulty: number;
  topic: string;
  objective?: string | null;
  grammar_focus?: string | null;
  is_review: boolean;
  is_assessment: boolean;
  status: string;          // not_started | in_progress | completed
  best_score: number;
  mastered: boolean;
  locked: boolean;
}

export interface CurriculumUnitNode {
  id: string;
  code: string;
  order: number;
  title: string;
  theme?: string | null;
  icon?: string | null;
  description?: string | null;
  lessons: CurriculumLessonNode[];
  completed_count: number;
  total_count: number;
}

export interface CurriculumMap {
  level: string;
  units: CurriculumUnitNode[];
  total_lessons: number;
  completed_lessons: number;
  progress_pct: number;
}

export interface NextLesson {
  code: string;
  title: string;
  skill: string;
  topic: string;
  difficulty: number;
  unit_title: string;
  objective?: string | null;
  reason: string;
}

export interface StartCurriculumLessonResult {
  curriculum_lesson_id: string;
  code: string;
  skill: string;
  topic: string;
  status: string;
}

// ── API Calls ────────────────────────────────────────────────────────────────
export async function getCurriculumMap(level = 'A1'): Promise<CurriculumMap> {
  const res = await api.get(`/curriculum/map?level=${encodeURIComponent(level)}`);
  return res.data;
}

/**
 * Roadmap-driven Next Best Lesson.
 * Returns null when the level is fully completed (backend responds 404).
 */
export async function getNextLesson(level = 'A1'): Promise<NextLesson | null> {
  try {
    const res = await api.get(`/curriculum/next?level=${encodeURIComponent(level)}`);
    return res.data;
  } catch (err: unknown) {
    const status = (err as { response?: { status?: number } })?.response?.status;
    if (status === 404) return null;  // whole level finished
    throw err;
  }
}

export async function startCurriculumLesson(code: string): Promise<StartCurriculumLessonResult> {
  const res = await api.post('/curriculum/start', { code });
  return res.data;
}

// ── G3 · Khoá theo mục tiêu ──────────────────────────────────────────────────
export interface TrackLesson {
  code: string;
  title_vi: string;
  skill: string;
  topic: string;
  level: string;
  status: 'not_started' | 'in_progress' | 'completed';
  best_score: number;
  mastered: boolean;
  locked: boolean;
}

export interface TrackModule {
  code: string;
  title_vi: string;
  lessons: TrackLesson[];
  completed_count: number;
  total_count: number;
}

export interface TrackSummary {
  id: string;
  emoji: string;
  title_vi: string;
  title_en: string;
  description_vi: string;
  target_level: string;
  total_lessons: number;
  completed_lessons: number;
  progress_pct: number;
  recommended: boolean;
  next_lesson_code: string | null;
}

export interface TrackDetail extends TrackSummary {
  modules: TrackModule[];
}

export interface StartTrackLessonResult {
  track_id: string;
  code: string;
  skill: string;
  topic: string;
  level: string;
  status: string;
}

export async function getTracks(): Promise<TrackSummary[]> {
  const res = await api.get('/curriculum/tracks');
  return res.data;
}

export async function getTrack(trackId: string): Promise<TrackDetail> {
  const res = await api.get(`/curriculum/tracks/${encodeURIComponent(trackId)}`);
  return res.data;
}

export async function startTrackLesson(trackId: string, code: string): Promise<StartTrackLessonResult> {
  const res = await api.post(`/curriculum/tracks/${encodeURIComponent(trackId)}/start`, { code });
  return res.data;
}
