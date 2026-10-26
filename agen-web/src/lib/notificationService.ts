import api from '@/lib/api';

// ── Types (mirror backend api/notifications.py) ───────────────────────────────
export interface AppNotification {
  id: string;
  type: string;
  title: string;
  body: string | null;
  icon: string | null;
  is_read: boolean;
  created_at: string;
}

// ── API Calls ────────────────────────────────────────────────────────────────
export async function listNotifications(unreadOnly = false, limit = 30): Promise<AppNotification[]> {
  const query = new URLSearchParams();
  if (unreadOnly) query.set('unread_only', 'true');
  query.set('limit', String(limit));
  const res = await api.get(`/notifications?${query.toString()}`);
  return res.data;
}

export async function getUnreadCount(): Promise<number> {
  const res = await api.get('/notifications/unread-count');
  return res.data.unread;
}

export async function markNotificationRead(id: string): Promise<AppNotification> {
  const res = await api.post(`/notifications/${id}/read`);
  return res.data;
}

export async function markAllNotificationsRead(): Promise<void> {
  await api.post('/notifications/read-all');
}
