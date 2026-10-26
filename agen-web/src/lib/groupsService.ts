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

/** G8 · Download the group's progress report as CSV (Excel-friendly, UTF-8 BOM). */
export const downloadGroupReport = async (groupId: string, groupName: string): Promise<void> => {
  const res = await api.get(`/groups/${groupId}/report.csv`, { responseType: 'blob' });
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `bao-cao-${groupName.replace(/[^\w-]+/g, '-')}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

export const SKILL_LABELS: Record<AssignmentSkill, string> = { vocabulary: 'Từ vựng', grammar: 'Ngữ pháp', reading: 'Đọc', listening: 'Nghe' };

// ── G10 · Giáo viên xem chi tiết bài làm + nhận xét ──────────────────────────
export type FeedbackTarget = 'general' | 'lesson' | 'writing' | 'exam' | 'speaking_exam';

export interface TeacherFeedback {
  id: string;
  target_type: FeedbackTarget;
  target_id: string | null;
  target_label: string | null;
  text: string;
  created_at: string;
  read_at: string | null;
}

export interface MemberDetail {
  learner_id: string;
  display_name: string;
  level: string;
  avatar: Partial<AvatarData>;
  streak: number;
  total_xp: number;
  weekly_xp: number;
  lessons_completed: number;
  skills: Record<string, number>;
  last_active_at: string | null;
  lessons: { id: string; title: string; skill: string; topic: string; score: number; completed_at: string | null }[];
  writings: { id: string; prompt_title: string; genre: string; score: number | null; grade: string | null; band: number | null; word_count: number; excerpt: string; created_at: string }[];
  exams: { id: string; title: string; exam: string; skill: string; pct: number; estimate: number | null; created_at: string }[];
  speaking_exams: { id: string; title: string; exam: string; estimate: number | null; created_at: string }[];
  assignments: AssignmentInfo[];
  feedback: TeacherFeedback[];
  group: GroupInfo;
  certificates: { code: string; title: string; issued_at: string }[];
}

export interface WritingDetail {
  id: string;
  prompt_title: string;
  prompt_text: string;
  genre: string;
  level: string;
  user_text: string;
  word_count: number;
  overall_score: number | null;
  grade: string | null;
  evaluation: Record<string, unknown>;
  created_at: string;
}

export interface LearnerFeedback {
  id: string;
  group_name: string;
  teacher_name: string;
  target_type: FeedbackTarget;
  target_label: string | null;
  text: string;
  created_at: string;
  read_at: string | null;
}

export const getMemberDetail = async (groupId: string, learnerId: string): Promise<MemberDetail> => (await api.get(`/groups/${groupId}/members/${learnerId}`)).data;
export const getMemberWriting = async (groupId: string, learnerId: string, submissionId: string): Promise<WritingDetail> =>
  (await api.get(`/groups/${groupId}/members/${learnerId}/writing/${submissionId}`)).data;
export const addMemberFeedback = async (groupId: string, learnerId: string, payload: { text: string; target_type: FeedbackTarget; target_id?: string | null; target_label?: string | null }): Promise<TeacherFeedback> =>
  (await api.post(`/groups/${groupId}/members/${learnerId}/feedback`, payload)).data;
export const deleteFeedback = async (groupId: string, feedbackId: string): Promise<void> => { await api.delete(`/groups/${groupId}/feedback/${feedbackId}`); };
export const issueCertificate = async (groupId: string, learnerId: string, title: string, note?: string): Promise<{ code: string; title: string }> =>
  (await api.post(`/groups/${groupId}/members/${learnerId}/certificate`, { title, note: note || null })).data;
export const getMyFeedback = async (): Promise<LearnerFeedback[]> => (await api.get('/groups/learner/feedback')).data;
export const markFeedbackRead = async (): Promise<void> => { await api.post('/groups/learner/feedback/read'); };
