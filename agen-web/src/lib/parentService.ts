import api from '@/lib/api';

// ── Types (mirror backend api/parent.py) ──────────────────────────────────────
export interface ChildSummary {
  learner_id: string;
  display_name: string;
  overall_level: string;
  total_xp: number;
  current_streak: number;
  total_lessons_completed: number;
  relationship_label: string | null;
}

export interface SkillImprovement {
  skill: string;
  label: string;
  score: number;
}

export interface ChildReport {
  learner_id: string;
  display_name: string;
  overall_level: string;
  sessions_this_week: number;
  xp_this_week: number;
  study_minutes_estimate: number;
  current_streak: number;
  accuracy_pct: number;
  skills: SkillImprovement[];
  best_skill: string;
  focus_skill: string;
  what_improved: string;
  what_needs_help: string;
  what_to_do: string;
}

// ── API Calls ────────────────────────────────────────────────────────────────
export async function linkChild(inviteCode: string, relationshipLabel?: string): Promise<ChildSummary> {
  const res = await api.post('/parent/link-child', {
    invite_code: inviteCode,
    relationship_label: relationshipLabel || null,
  });
  return res.data;
}

export async function getChildren(): Promise<ChildSummary[]> {
  const res = await api.get('/parent/children');
  return res.data;
}

export async function unlinkChild(learnerId: string): Promise<void> {
  await api.delete(`/parent/children/${learnerId}`);
}

export async function getChildReport(learnerId: string): Promise<ChildReport> {
  const res = await api.get(`/parent/child/${learnerId}/report`);
  return res.data;
}

// ── G3 · proactive e-mails ────────────────────────────────────────────────────
export interface ParentSettings {
  weekly_report_email: boolean;
  email_available: boolean;
  email_address: string;
  last_weekly_report_week: string | null;
}

export async function getParentSettings(): Promise<ParentSettings> {
  const res = await api.get('/parent/settings');
  return res.data;
}

export async function updateParentSettings(payload: { weekly_report_email: boolean }): Promise<ParentSettings> {
  const res = await api.put('/parent/settings', payload);
  return res.data;
}
