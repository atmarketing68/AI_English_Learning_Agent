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
  /** G13 · class tests, each with the learner's own result in `mine` */
  tests?: ClassTest[];
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
  writings: { id: string; prompt_title: string; genre: string; score: number | null; grade: string | null; band: number | null; word_count: number; excerpt: string; created_at: string; teacher_score?: number | null; teacher_band?: number | null }[];
  exams: { id: string; title: string; exam: string; skill: string; pct: number; estimate: number | null; created_at: string }[];
  speaking_exams: { id: string; title: string; exam: string; estimate: number | null; created_at: string }[];
  assignments: AssignmentInfo[];
  feedback: TeacherFeedback[];
  /** G13 · IELTS writing bands over time (teacher rubric when graded, else AI) */
  rubric_history?: RubricPoint[];
  /** G14 · IELTS Speaking mock bands over time */
  speaking_history?: RubricPoint[];
  tests?: ClassTest[];
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
  /** G11 · 'ielts' | 'toeic' for exam genres */
  exam?: 'ielts' | 'toeic' | null;
  teacher_score?: number | null;
  teacher_band?: number | null;
  teacher_comment?: string | null;
  teacher_scored_at?: string | null;
  /** G12 · IELTS criteria */
  teacher_rubric?: IeltsRubric | null;
}

export type IeltsRubric = { task: number; coherence: number; lexical: number; grammar: number };
export const IELTS_CRITERIA: { key: keyof IeltsRubric; label: string }[] = [
  { key: 'task', label: 'Đáp ứng đề' }, { key: 'coherence', label: 'Mạch lạc & liên kết' },
  { key: 'lexical', label: 'Từ vựng' }, { key: 'grammar', label: 'Ngữ pháp' },
];

/** G11 · Teacher re-grade of a writing piece; score null clears it. */
export const gradeMemberWriting = async (groupId: string, learnerId: string, submissionId: string, payload: { score: number | null; band?: number | null; comment?: string | null; rubric?: IeltsRubric | null }): Promise<WritingDetail> =>
  (await api.post(`/groups/${groupId}/members/${learnerId}/writing/${submissionId}/grade`, payload)).data;

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

// ── G12 · Câu lạc bộ nói hằng tuần của lớp ───────────────────────────────────
export interface ClubSchedule {
  id: string;
  weekday: number;
  time: string;
  label: string;
  topic_id: string | null;
  topic_title: string;
  next: { room_id: string; code: string; scheduled_at: string; status: string; registered: number; topic_title: string } | null;
}

export interface ClubSchedules {
  schedules: ClubSchedule[];
  topics: { id: string; title_vi: string; level: string; emoji: string }[];
  weekdays: string[];
}

export const getClubSchedules = async (groupId: string): Promise<ClubSchedules> => (await api.get(`/groups/${groupId}/club-schedules`)).data;
export const addClubSchedule = async (groupId: string, payload: { weekday: number; time: string; topic_id?: string | null }): Promise<ClubSchedule> =>
  (await api.post(`/groups/${groupId}/club-schedules`, payload)).data;
export const deleteClubSchedule = async (groupId: string, scheduleId: string): Promise<void> => { await api.delete(`/groups/${groupId}/club-schedules/${scheduleId}`); };

// ── G13 · Bài kiểm tra lớp + tiến bộ rubric ──────────────────────────────────
export type ClassTestKind = 'mock' | 'speaking';

export interface TestScore {
  done: boolean;
  pct: number | null;
  estimate: number | null;
  seconds: number | null;
  submitted_at: string | null;
  attempt_id: string | null;
}

export interface ClassTest {
  id: string;
  group_id: string;
  kind: ClassTestKind;
  exam_id: string;
  title: string;
  note: string | null;
  exam: 'ielts' | 'toeic' | null;
  skill: string | null;
  minutes: number | null;
  available: boolean;
  opens_on: string;
  due_on: string;
  status: 'upcoming' | 'open' | 'closed';
  done_count: number;
  member_count: number;
  avg_pct: number | null;
  avg_estimate: number | null;
  created_at: string;
  mine?: TestScore;
  /** G14 · "monthly" → next month's test is created automatically */
  repeat?: 'monthly' | null;
  next_test_id?: string | null;
  group_name?: string;
}

export interface ClassTestResults extends ClassTest {
  results: (TestScore & { learner_id: string; display_name: string; level: string; avatar: Partial<AvatarData> })[];
  min_estimate: number | null;
  max_estimate: number | null;
}

export interface TestCatalogueItem { kind: ClassTestKind; id: string; exam: 'ielts' | 'toeic'; skill: string; title: string; minutes: number }

export interface RubricPoint {
  submission_id: string;
  title: string;
  created_at: string;
  source: 'teacher' | 'ai' | 'estimate';
  overall: number;
  criteria: Record<string, number>;
}

export const getTestCatalogue = async (): Promise<TestCatalogueItem[]> => (await api.get('/groups/tests/catalogue')).data;
export const getGroupTests = async (groupId: string): Promise<ClassTest[]> => (await api.get(`/groups/${groupId}/tests`)).data;
export const createGroupTest = async (groupId: string, payload: { kind: ClassTestKind; exam_id: string; due_on: string; opens_on?: string | null; title?: string | null; note?: string | null; repeat?: 'monthly' | null }): Promise<ClassTest> =>
  (await api.post(`/groups/${groupId}/tests`, payload)).data;
export const getGroupTestResults = async (groupId: string, testId: string): Promise<ClassTestResults> => (await api.get(`/groups/${groupId}/tests/${testId}`)).data;
export const setGroupTestRepeat = async (groupId: string, testId: string, repeat: 'monthly' | null): Promise<ClassTest> =>
  (await api.post(`/groups/${groupId}/tests/${testId}/repeat`, { repeat })).data;
export const getGroupTestSheet = async (groupId: string, testId: string): Promise<ClassTestResults & { group_name: string; group_code: string; teacher_name: string }> =>
  (await api.get(`/groups/${groupId}/tests/${testId}/sheet`)).data;
export const deleteGroupTest = async (groupId: string, testId: string): Promise<void> => { await api.delete(`/groups/${groupId}/tests/${testId}`); };

/** Where a learner takes a class test (the id travels in ?test= so it is counted and does not use the free daily attempt). */
export const classTestHref = (t: Pick<ClassTest, 'kind' | 'exam_id' | 'id'>): string =>
  t.kind === 'speaking' ? `/exams/speaking/${t.exam_id}?test=${t.id}` : `/exams/${t.exam_id}?test=${t.id}`;

/** "9/10" style score label: IELTS band or TOEIC points, plus % for Listening/Reading. */
export function testScoreLabel(exam: string | null, s: Pick<TestScore, 'pct' | 'estimate'>): string {
  if (s.estimate == null) return '—';
  const main = exam === 'ielts' ? `Band ${s.estimate.toFixed(1)}` : `${Math.round(s.estimate)} điểm`;
  return s.pct != null ? `${main} · ${Math.round(s.pct)}%` : main;
}
