import api from '@/lib/api';
import type { AvatarData } from '@/types';

// ── G6 · Bạn học & thử thách đôi tuần ───────────────────────────────────────
export interface DuoQuest {
  week: string;
  my_xp: number;
  friend_xp: number;
  goal: number;
  min_each: number;
  done: boolean;
  claimed: boolean;
  claimable: boolean;
  reward_xp: number;
  reward_gems: number;
}

export interface Friend {
  learner_id: string;
  display_name: string;
  level: string;
  avatar: Partial<AvatarData>;
  streak: number;
  studied_today: boolean;
  quest: DuoQuest;
}

export interface Friends {
  my_code: string | null;
  goal: number;
  min_each: number;
  reward_xp: number;
  reward_gems: number;
  max_friends: number;
  friends: Friend[];
}

export async function getFriends(): Promise<Friends> {
  const { data } = await api.get('/friends');
  return data;
}

export async function addFriend(code: string): Promise<Friends> {
  const { data } = await api.post('/friends', { code });
  return data;
}

export async function removeFriend(learnerId: string): Promise<Friends> {
  const { data } = await api.delete(`/friends/${learnerId}`);
  return data;
}

export async function claimDuoQuest(learnerId: string): Promise<{ xp: number; gems: number; total_xp: number; gems_total: number }> {
  const { data } = await api.post(`/friends/${learnerId}/claim`);
  return data;
}

// ── G7 · Bảng xếp hạng bạn bè ────────────────────────────────────────────────
export interface LeaderRow {
  rank: number;
  learner_id: string;
  display_name: string;
  avatar: Partial<AvatarData>;
  level: string;
  weekly_xp: number;
  streak: number;
  is_me: boolean;
}

export async function getFriendsLeaderboard(): Promise<LeaderRow[]> {
  const { data } = await api.get('/friends/leaderboard');
  return data;
}
