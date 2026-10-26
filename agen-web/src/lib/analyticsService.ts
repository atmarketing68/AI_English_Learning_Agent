import api from './api';

export interface SkillScores {
  vocabulary: number;
  grammar: number;
  reading: number;
  speaking: number;
  listening: number;
  writing: number;
}

export interface OverviewData {
  overall_level: string;
  total_xp: number;
  current_streak: number;
  total_lessons_completed: number;
  skill_scores: SkillScores;
  xp_to_next_level: number;
  progress_pct: number;
}

export interface ActivityDay {
  date: string;
  xp: number;
  sessions: number;
}

export interface ActivityData {
  days: ActivityDay[];
  total_xp_30d: number;
  total_sessions_30d: number;
}

export interface RecommendedTopic {
  skill: string;
  topic: string;
  reason: string;
}

export interface CoachAdvice {
  weak_skills: string[];
  strong_skills: string[];
  focus_area: string;
  recommended_topics: RecommendedTopic[];
  study_plan_today: string;
  motivational_message: string;
}

export interface WeeklyReport {
  sessions_count: number;
  xp_earned_this_week: number;
  best_skill: string;
  most_practiced_skill: string;
  highlight: string;
  areas_to_improve: string[];
  next_week_goal: string;
  encouragement: string;
}

export interface AssessmentSnapshot {
  assessment_type: string;
  completed_at: string;
  overall_level: string;
  accuracy_percent: number;
  skill_scores: Record<string, number>;
}

export interface AssessmentOutcome {
  baseline: AssessmentSnapshot | null;
  latest_followup: AssessmentSnapshot | null;
  accuracy_delta: number | null;
  skill_deltas: Record<string, number>;
}

export const getOverview = async (): Promise<OverviewData> => {
  const res = await api.get('/analytics/overview');
  return res.data;
};

export const getActivity = async (days = 30): Promise<ActivityData> => {
  const res = await api.get(`/analytics/events?days=${days}`);
  return res.data;
};

export const getCoachAdvice = async (): Promise<CoachAdvice> => {
  const res = await api.get('/analytics/coach-advice');
  return res.data;
};

export const getWeeklyReport = async (): Promise<WeeklyReport> => {
  const res = await api.get('/analytics/weekly-report');
  return res.data;
};

export const getAssessmentOutcomes = async (): Promise<AssessmentOutcome> => {
  const res = await api.get('/analytics/assessment-outcomes');
  return res.data;
};

export interface LeaderboardEntry {
  learner_id: string;
  display_name: string;
  avatar: string;
  level: string;
  xp: number;
  is_current_user: boolean;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
}

export const getLeaderboard = async (): Promise<LeaderboardResponse> => {
  const res = await api.get('/analytics/leaderboard');
  return res.data;
};
