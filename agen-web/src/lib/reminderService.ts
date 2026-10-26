import api from '@/lib/api';

// ── Types ────────────────────────────────────────────────────────────────────
export interface ReminderSettings {
  hour: number | null;           // local hour 0–23, null = off
  email: boolean;
  push_devices: number;
  push_available: boolean;       // server has push keys configured
  push_public_key: string | null;
  email_available: boolean;      // server can send email
  email_address: string;
  // G9 · Zalo OA
  zalo_available?: boolean;
  zalo_oa_link?: string | null;
  zalo_linked?: boolean;
  zalo_link_code?: string | null;
}

export async function unlinkZalo(): Promise<void> {
  await api.post('/zalo/unlink');
}

export type PushState = 'unsupported' | 'denied' | 'on' | 'off';

// ── API ──────────────────────────────────────────────────────────────────────
export async function getReminderSettings(): Promise<ReminderSettings> {
  const { data } = await api.get('/reminders/settings');
  return data;
}

export async function saveReminderSettings(hour: number | null, email: boolean): Promise<ReminderSettings> {
  const { data } = await api.put('/reminders/settings', { hour, email });
  return data;
}

export async function sendTestReminder(): Promise<{ push: number; email: boolean }> {
  const { data } = await api.post('/reminders/test');
  return data;
}

export async function unsubscribeEmail(token: string): Promise<void> {
  await api.post('/reminders/unsubscribe-email', { token });
}

// ── Web push (this browser) ──────────────────────────────────────────────────
export function pushSupported(): boolean {
  return typeof window !== 'undefined'
    && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
}

function keyToBytes(base64url: string): Uint8Array<ArrayBuffer> {
  const padded = (base64url + '='.repeat((4 - (base64url.length % 4)) % 4)).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(padded);
  const bytes = new Uint8Array(new ArrayBuffer(raw.length));
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  return bytes;
}

export async function currentPushState(): Promise<PushState> {
  if (!pushSupported()) return 'unsupported';
  if (Notification.permission === 'denied') return 'denied';
  const reg = await navigator.serviceWorker.getRegistration('/');
  const sub = await reg?.pushManager.getSubscription();
  return sub && Notification.permission === 'granted' ? 'on' : 'off';
}

export class PushDeniedError extends Error {}

/** Ask for permission (call straight from a click) and register this browser. */
export async function enablePush(publicKey: string): Promise<ReminderSettings> {
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') throw new PushDeniedError('denied');
  const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
  await navigator.serviceWorker.ready;
  const sub = (await reg.pushManager.getSubscription())
    ?? (await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyToBytes(publicKey) }));
  const json = sub.toJSON();
  const { data } = await api.post('/reminders/push-subscriptions', { endpoint: json.endpoint, keys: json.keys });
  return data;
}

export async function disablePush(): Promise<ReminderSettings | null> {
  const reg = await navigator.serviceWorker.getRegistration('/');
  const sub = await reg?.pushManager.getSubscription();
  if (!sub) return null;
  const { data } = await api.delete('/reminders/push-subscriptions', { data: { endpoint: sub.endpoint } });
  await sub.unsubscribe();
  return data;
}
