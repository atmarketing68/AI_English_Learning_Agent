import api from '@/lib/api';
import type { AvatarData } from '@/types';

// ── G7 · Nhóm học: lớp (giáo viên) / doanh nghiệp (HR) ───────────────────────
export type GroupKind = 'class' | 'company';
export type AssignmentSkill = 'vocabulary' | 'grammar' | 'reading' | 'listening';

export interface GroupInfo {
  id: string;
  name: string;
  kind: GroupKind;
  code: string;
  member_count: number;
  created_at: string;
}

export interface OwnerHome {
  groups: GroupInfo[];
  plan: 'free' | 'team' | string;
  seats: number;
  is_premium: boolean;
  members_total: number;
  team_prices: { months: number; amount_vnd: number }[];
}

export interface GroupMemberInfo {
  learner_id: string;
  display_name: string;
  level: string;
  avatar: Partial<AvatarData>;
  streak: number;
  weekly_xp: number;
  total_xp: number;
  lessons: number;
  active_today: boolean;
  assignments_done: number;
  premium_source: 'own' | 'family' | 'team' | null;
  joined_at: string;
}

export interface AssignmentInfo {
  id: string;
  title: string;
  skill: AssignmentSkill;
  topic: string;
  note: string | null;
  due_on: string | null;
  created_at: string;
  done_count: number;
  member_count: number;
  started: boolean;
  done: boolean;
  score: number | null;
  overdue: boolean;
}

export interface GroupDetail {
  group: GroupInfo;
  members: GroupMemberInfo[];
  assignments: AssignmentInfo[];
  covered_seats: number;
}

export interface LearnerGroup {
  group: GroupInfo;
  owner_name: string;
  assignments: AssignmentInfo[];
}

export const getOwnerHome = async (): Promise<OwnerHome> => (await api.get('/groups/mine')).data;
export const createGroup = async (name: string, kind: GroupKind): Promise<GroupInfo> => (await api.post('/groups', { name, kind })).data;
export const getGroupDetail = async (groupId: string): Promise<GroupDetail> => (await api.get(`/groups/${groupId}`)).data;
export const removeGroupMember = async (groupId: string, learnerId: string): Promise<void> => { await api.delete(`/groups/${groupId}/members/${learnerId}`); };
export const createAssignment = async (groupId: string, payload: { title: string; skill: AssignmentSkill; topic: string; note?: string; due_on?: string | null }): Promise<AssignmentInfo> =>
  (await api.post(`/groups/${groupId}/assignments`, payload)).data;
export const deleteAssignment = async (groupId: string, assignmentId: string): Promise<void> => { await api.delete(`/groups/${groupId}/assignments/${assignmentId}`); };

export const getMyGroups = async (): Promise<{ groups: LearnerGroup[] }> => (await api.get('/groups/learner/mine')).data;
export const joinGroup = async (code: string): Promise<{ groups: LearnerGroup[] }> => (await api.post('/groups/join', { code })).data;
export const leaveGroup = async (groupId: string): Promise<{ groups: LearnerGroup[] }> => (await api.post(`/groups/${groupId}/leave`)).data;
export const startAssignment = async (assignmentId: string): Promise<{ assignment_id: string; skill: AssignmentSkill; topic: string; title: string }> =>
  (await api.post(`/groups/assignments/${assignmentId}/start`)).data;

export const SKILL_LABELS: Record<AssignmentSkill, string> = { vocabulary: 'Từ vựng', grammar: 'Ngữ pháp', reading: 'Đọc', listening: 'Nghe' };
