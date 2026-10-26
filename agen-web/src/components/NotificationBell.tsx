'use client';

import { useEffect, useRef, useState } from 'react';
import {
  listNotifications, getUnreadCount, markNotificationRead, markAllNotificationsRead,
  type AppNotification,
} from '@/lib/notificationService';
import { Bell } from 'lucide-react';

/**
 * Bell icon with an unread badge and a dropdown of recent notifications.
 * Polls the unread count periodically; loads the list when opened.
 */
export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [items, setItems] = useState<AppNotification[]>([]);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Poll unread count (initial + every 60s).
  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const n = await getUnreadCount();
        if (active) setUnread(n);
      } catch { /* ignore — non-critical */ }
    };
    refresh();
    const id = setInterval(refresh, 60_000);
    return () => { active = false; clearInterval(id); };
  }, []);

  // Close on outside click.
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const toggle = async () => {
    const next = !open;
    setOpen(next);
    if (next) {
      setLoading(true);
      try {
        const list = await listNotifications(false, 20);
        setItems(list);
      } catch { /* ignore */ } finally {
        setLoading(false);
      }
    }
  };

  const handleItemClick = async (n: AppNotification) => {
    if (n.is_read) return;
    try {
      await markNotificationRead(n.id);
      setItems((prev) => prev.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
      setUnread((u) => Math.max(0, u - 1));
    } catch { /* ignore */ }
  };

  const handleReadAll = async () => {
    try {
      await markAllNotificationsRead();
      setItems((prev) => prev.map((x) => ({ ...x, is_read: true })));
      setUnread(0);
    } catch { /* ignore */ }
  };

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={toggle}
        className="btn btn-ghost btn-sm"
        aria-label="Thông báo"
        style={{ position: 'relative', lineHeight: 1, width: 36, height: 36, padding: 0 }}
      >
        <Bell size={18} strokeWidth={1.8} />
        {unread > 0 && (
          <span
            style={{
              position: 'absolute', top: 0, right: 0, minWidth: 16, height: 16,
              padding: '0 4px', borderRadius: 99, background: 'var(--agen-secondary)',
              color: '#fff', fontSize: '0.65rem', fontWeight: 700,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          className="card animate-fade-in-up"
          style={{
            position: 'absolute', right: 0, top: 'calc(100% + 8px)', width: 320, maxHeight: 420,
            overflowY: 'auto', zIndex: 50, padding: 0, boxShadow: 'var(--shadow-lg)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', borderBottom: '1px solid var(--border-subtle)' }}>
            <strong style={{ fontSize: '0.95rem', fontWeight: 600 }}>Thông báo</strong>
            {unread > 0 && (
              <button className="btn btn-ghost btn-sm" style={{ fontSize: '0.72rem' }} onClick={handleReadAll}>
                Đánh dấu đã đọc
              </button>
            )}
          </div>

          {loading ? (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>Đang tải…</div>
          ) : items.length === 0 ? (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              Chưa có thông báo nào.
            </div>
          ) : (
            items.map((n) => (
              <button
                key={n.id}
                onClick={() => handleItemClick(n)}
                style={{
                  display: 'flex', gap: 10, width: '100%', textAlign: 'left', padding: '12px 14px',
                  border: 'none', borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer',
                  background: n.is_read ? 'transparent' : 'var(--bg-tint)', color: 'var(--text-primary)', fontFamily: 'inherit',
                }}
              >
                {n.icon ? <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{n.icon}</span> : <Bell size={16} style={{ flexShrink: 0, marginTop: 2 }} color="var(--text-muted)" />}
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ display: 'block', fontWeight: n.is_read ? 400 : 600, fontSize: '0.88rem' }}>{n.title}</span>
                  {n.body && <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 2 }}>{n.body}</span>}
                  <span style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 4 }}>
                    {new Date(n.created_at).toLocaleString('vi-VN')}
                  </span>
                </span>
                {!n.is_read && <span style={{ width: 8, height: 8, borderRadius: 99, background: 'var(--agen-primary)', flexShrink: 0, marginTop: 4 }} />}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
