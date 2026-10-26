// AGEN TypeScript Type Definitions
// Central types mirroring backend models

export type SkillLevel = 'PRE_A1' | 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';

export type Skill = 'listening' | 'speaking' | 'reading' | 'writing' | 'vocabulary' | 'grammar';

export interface LearnerProfile {
  id: string;
  display_name: string;
  age: number | null;
  grade: string | null;
  overall_level: SkillLevel;
  listening_score: number;
  speaking_score: number;
  reading_score: number;
  writing_score: number;
  vocabulary_score: number;
  grammar_score: number;
  current_streak: number;
  total_xp: number;
  total_lessons_completed: number;
  strengths: string[];
  weaknesses: string[];
  placement_completed: 'none' | 'partial' | 'done';
  learning_goal: string | null;
  interests: string[];
  daily_study_minutes: number;
  invite_code: string | null;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  refresh_token: string | null;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  display_name: string;
  age?: number;
  grade?: string;
  role?: 'learner' | 'parent';
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: 'learner' | 'parent';
  is_guest?: boolean;
}

export interface LoginPayload {
  username: string; // OAuth2 uses "username" field
  password: string;
}

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
  earned_at: string | null;
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
