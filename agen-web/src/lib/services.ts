import api from './api';
import type { AuthToken, RegisterPayload, LoginPayload, LearnerProfile, User } from '@/types';

// --- Auth ---
export async function register(payload: RegisterPayload): Promise<{ id: string; email: string; role: string }> {
  const res = await api.post('/auth/register', payload);
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await api.get('/auth/me');
  return res.data;
}

export async function login(payload: LoginPayload): Promise<AuthToken> {
  const formData = new URLSearchParams();
  formData.append('username', payload.username);
  formData.append('password', payload.password);
  const res = await api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return res.data;
}

// --- Learner ---
export async function getMyProfile(): Promise<LearnerProfile> {
  const res = await api.get('/learner/me');
  return res.data;
}

export async function updateMyProfile(payload: Partial<LearnerProfile>): Promise<LearnerProfile> {
  const res = await api.patch('/learner/me', payload);
  return res.data;
}

// --- Gamification ---
export async function getAchievements(): Promise<import('@/types').Achievement[]> {
  const res = await api.get('/gamification/achievements');
  return res.data;
}

export async function getDailyChallenge(): Promise<import('@/types').DailyChallenge> {
  const res = await api.get('/gamification/daily-challenge');
  return res.data;
}

export async function checkAchievements(): Promise<Record<string, unknown>[]> {
  const res = await api.post('/gamification/check-achievements');
  return res.data;
}

// --- Streak & Daily Challenge ---
export interface ActivityUpdateResponse {
  current_streak: number;
  longest_streak: number;
  daily_challenge_completed: boolean;
  newly_earned_achievements: {
    id: string;
    name: string;
    description: string;
    icon: string;
    xp_reward: number;
  }[];
}

export async function notifyActivityCompleted(skill: string): Promise<ActivityUpdateResponse> {
  const res = await api.post('/gamification/activity-completed', { skill });
  return res.data;
}
