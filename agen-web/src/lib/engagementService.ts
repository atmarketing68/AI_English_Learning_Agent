import api from '@/lib/api';

// ── Types ────────────────────────────────────────────────────────────────────
export interface StreakInfo {
  current: number;
  longest: number;
  studied_today: boolean;
  freezes: number;
  max_freezes: number;
  protected: boolean;          // missed days will be covered by freezes
  missed_days: number;
  freeze_used_today: boolean;
}

export interface Quest {
  id: string;
  code: string;
  title: string;
  icon: 'book' | 'brain' | 'target' | 'star' | 'trophy' | 'mic';
  progress: number;
  target: number;
  xp_reward: number;
  completed: boolean;
  claimed: boolean;
}

export interface WeekDay {
  date: string;
  label: string;
  done: boolean;
  is_today: boolean;
  is_future: boolean;
}

export interface WeeklyGoal {
  goal_days: number;
  options: number[];
  days_done: number;
  days: WeekDay[];
  completed: boolean;
  claimed: boolean;
  reward_xp: number;
}

export interface Engagement {
  total_xp: number;
  streak: StreakInfo;
  quests: Quest[];
  weekly: WeeklyGoal;
}

export interface ClaimResult {
  xp_awarded: number;
  freeze_awarded: boolean;
  state: Engagement;
}

// ── API ──────────────────────────────────────────────────────────────────────
export async function getEngagement(): Promise<Engagement> {
  const { data } = await api.get('/engagement/today');
  return data;
}

export async function claimQuest(questId: string): Promise<ClaimResult> {
  const { data } = await api.post(`/engagement/quests/${questId}/claim`);
  return data;
}

export async function claimWeeklyReward(): Promise<ClaimResult> {
  const { data } = await api.post('/engagement/weekly/claim');
  return data;
}

export async function setWeeklyGoal(days: number): Promise<Engagement> {
  const { data } = await api.put('/engagement/weekly-goal', { days });
  return data;
}

// ── G3 · Giải đấu tuần ───────────────────────────────────────────────────────
export interface LeagueEntry {
  rank: number;
  learner_id: string;
  display_name: string;
  level: string;
  xp: number;
  is_me: boolean;
  tier: string | null;
}

export interface League {
  week: string;
  starts_on: string;
  ends_on: string;
  board_size: number;
  rewards: { up_to_rank: number; xp: number }[];
  entries: LeagueEntry[];
  me: { rank: number | null; xp: number; participants: number };
  last_week: {
    week: string; rank: number | null; xp: number; participants: number;
    reward_xp: number; tier: string | null; claimed: boolean; claimable: boolean;
  };
}

export async function getLeague(): Promise<League> {
  const { data } = await api.get('/engagement/league');
  return data;
}

export async function claimLeagueReward(): Promise<{ xp_awarded: number; total_xp: number }> {
  const { data } = await api.post('/engagement/league/claim');
  return data;
}
