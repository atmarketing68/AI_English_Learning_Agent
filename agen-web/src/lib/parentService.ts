import type { ClassTest } from '@/lib/groupsService';
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
  /** G5 · 'own' | 'family' | null */
  premium_source: 'own' | 'family' | null;
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
  /** G14 · class tests the child's teachers assigned, with the child's own result in `mine` */
  class_tests?: ClassTest[];
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
  // G7 · web push to the parent's devices
  push_alerts: boolean;
  push_available: boolean;
  push_public_key: string | null;
  push_devices: number;
  // G13 · native app (FCM) on the parent's phone
  native_push_available?: boolean;
  native_devices?: number;
  // G9 · Zalo OA
  zalo_available?: boolean;
  zalo_oa_link?: string | null;
  zalo_linked?: boolean;
  zalo_link_code?: string | null;
}

export async function unlinkParentZalo(): Promise<ParentSettings> {
  await api.post('/zalo/unlink');
  return getParentSettings();
}

export async function getParentSettings(): Promise<ParentSettings> {
  const res = await api.get('/parent/settings');
  return res.data;
}

export async function updateParentSettings(payload: { weekly_report_email?: boolean; push_alerts?: boolean }): Promise<ParentSettings> {
  const res = await api.put('/parent/settings', payload);
  return res.data;
}

// ── G7 · push on this device (parents) ───────────────────────────────────────
function keyToBytes(base64url: string): Uint8Array<ArrayBuffer> {
  const padded = (base64url + '='.repeat((4 - (base64url.length % 4)) % 4)).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(padded);
  const bytes = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  return bytes;
}

export class ParentPushDeniedError extends Error {}

export function parentPushSupported(): boolean {
  return typeof window !== 'undefined' && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
}

export async function enableParentPush(publicKey: string): Promise<ParentSettings> {
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') throw new ParentPushDeniedError('denied');
  const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
  await navigator.serviceWorker.ready;
  const sub = (await reg.pushManager.getSubscription())
    ?? (await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyToBytes(publicKey) }));
  const json = sub.toJSON();
  const { data } = await api.post('/parent/push-subscriptions', { endpoint: json.endpoint, keys: json.keys });
  return data;
}

export async function disableParentPush(): Promise<ParentSettings | null> {
  const reg = await navigator.serviceWorker.getRegistration('/');
  const sub = await reg?.pushManager.getSubscription();
  if (!sub) return null;
  const { data } = await api.delete('/parent/push-subscriptions', { data: { endpoint: sub.endpoint } });
  await sub.unsubscribe();
  return data;
}
