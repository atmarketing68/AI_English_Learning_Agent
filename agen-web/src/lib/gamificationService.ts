import api from './api';

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  category: string;
  xp_reward: number;
  condition_type: string;
  condition_value: number;
  earned: boolean;
  earned_at?: string;
}

export interface DailyChallenge {
  id: string;
  title: string;
  description: string;
  skill: string;
  target_value: number;
  current_value: number;
  xp_reward: number;
  is_completed: boolean;
  progress_pct: number;
}

export const getAchievements = async (): Promise<Achievement[]> => {
  const res = await api.get('/gamification/achievements');
  return res.data;
};

export const getDailyChallenge = async (): Promise<DailyChallenge> => {
  const res = await api.get('/gamification/daily-challenge');
  return res.data;
};

export const triggerAchievementCheck = async (): Promise<Achievement[]> => {
  const res = await api.post('/gamification/check-achievements');
  return res.data; // newly earned achievements
};
