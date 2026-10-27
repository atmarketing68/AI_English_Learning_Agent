/**
 * G13 · Push gốc trong app di động (Capacitor, chế độ remote URL).
 *
 * The native shell injects `window.Capacitor` with its plugins, so the web app
 * talks to `PushNotifications` through that bridge — no npm dependency and
 * nothing runs in a normal browser. The FCM token goes to
 * `POST /notifications/device-tokens` for learners and parents alike.
 */
import api from '@/lib/api';

const TOKEN_KEY = 'agen-native-push-token';

interface PushListenerHandle { remove: () => Promise<void> | void }
interface PushPlugin {
  checkPermissions: () => Promise<{ receive: string }>;
  requestPermissions: () => Promise<{ receive: string }>;
  register: () => Promise<void>;
  addListener: (event: string, cb: (payload: unknown) => void) => Promise<PushListenerHandle> | PushListenerHandle;
}
interface CapacitorBridge {
  isNativePlatform?: () => boolean;
  getPlatform?: () => string;
  Plugins?: { PushNotifications?: PushPlugin };
}

function bridge(): CapacitorBridge | null {
  if (typeof window === 'undefined') return null;
  return (window as unknown as { Capacitor?: CapacitorBridge }).Capacitor ?? null;
}

function plugin(): PushPlugin | null {
  const cap = bridge();
  return cap?.isNativePlatform?.() ? cap.Plugins?.PushNotifications ?? null : null;
}

/** True inside the Android / iOS app (not in a browser or the installed PWA). */
export function isNativeApp(): boolean {
  return plugin() !== null;
}

function platform(): 'ios' | 'android' {
  return bridge()?.getPlatform?.() === 'ios' ? 'ios' : 'android';
}

function storedToken(): string | null {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}

let listening = false;

function listen(p: PushPlugin, onToken: (ok: boolean) => void) {
  if (listening) return;
  listening = true;
  void p.addListener('registration', (payload) => {
    const value = (payload as { value?: string })?.value;
    if (!value) { onToken(false); return; }
    try { localStorage.setItem(TOKEN_KEY, value); } catch { /* private mode */ }
    api.post('/notifications/device-tokens', { token: value, platform: platform() })
      .then(() => onToken(true), () => onToken(false));
  });
  void p.addListener('registrationError', () => onToken(false));
  // Tapping a notification opens the page it points at ("/parent", "/classes", "/review"…).
  void p.addListener('pushNotificationActionPerformed', (payload) => {
    const url = (payload as { notification?: { data?: { url?: string } } })?.notification?.data?.url;
    if (url && url.startsWith('/')) window.location.assign(url);
  });
}

let pending: ((ok: boolean) => void) | null = null;

/**
 * Ask for permission (shows the system prompt the first time) and register this phone.
 * Resolves 'on', 'denied' or 'unavailable' (not in the app).
 */
export async function enableNativePush(): Promise<'on' | 'denied' | 'unavailable'> {
  const p = plugin();
  if (!p) return 'unavailable';
  let perm = await p.checkPermissions();
  if (perm.receive === 'prompt' || perm.receive === 'prompt-with-rationale') perm = await p.requestPermissions();
  if (perm.receive !== 'granted') return 'denied';
  const done = new Promise<boolean>((resolve) => { pending = resolve; });
  listen(p, (ok) => { pending?.(ok); pending = null; });
  await p.register();
  const ok = await Promise.race([done, new Promise<boolean>((r) => setTimeout(() => r(false), 15000))]);
  return ok ? 'on' : 'unavailable';
}

/** Re-register silently after sign-in when permission was already granted (tokens can rotate). */
export async function refreshNativePush(): Promise<void> {
  const p = plugin();
  if (!p) return;
  const perm = await p.checkPermissions();
  if (perm.receive !== 'granted') return;
  listen(p, () => undefined);
  await p.register();
}

/** On sign-out: stop this phone from receiving the old account's notifications. */
export async function forgetNativePush(accessToken: string | null): Promise<void> {
  const token = storedToken();
  if (!token || !accessToken || !isNativeApp()) return;
  try {
    await api.delete('/notifications/device-tokens', {
      data: { token, platform: platform() }, headers: { Authorization: `Bearer ${accessToken}` },
    });
  } catch { /* best effort */ }
  try { localStorage.removeItem(TOKEN_KEY); } catch { /* ignore */ }
}
